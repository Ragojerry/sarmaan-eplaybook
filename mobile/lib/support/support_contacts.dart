import 'package:drift/drift.dart' show Value;
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../db/local_database.dart';
import '../offline/content_sync_service.dart' show localDatabaseProvider;
import '../services/api_client.dart';
import '../services/auth_service.dart' show apiClientProvider, authProvider;
import '../sync/sync_engine.dart';

/// How a Support deck row reaches a person.
enum SupportContactType { phone, sms, email, whatsapp, link }

SupportContactType? supportContactTypeFrom(String raw) => switch (raw) {
      'PHONE' => SupportContactType.phone,
      'SMS' => SupportContactType.sms,
      'EMAIL' => SupportContactType.email,
      'WHATSAPP' => SupportContactType.whatsapp,
      'LINK' => SupportContactType.link,
      _ => null,
    };

/// Email, WhatsApp and web links need a connection; a call or an SMS does not.
bool needsInternet(SupportContactType type) =>
    type == SupportContactType.email || type == SupportContactType.whatsapp || type == SupportContactType.link;

/// One contact as the admin entered it (label and availability shown as is).
class SupportContact {
  final String id;
  final SupportContactType type;
  final String label;
  final String value;
  final String? whatsappMessage;
  final String? emailSubject;
  final bool includeAppVersion;
  final String? availability;
  final String? languages;

  const SupportContact({
    required this.id,
    required this.type,
    required this.label,
    required this.value,
    this.whatsappMessage,
    this.emailSubject,
    this.includeAppVersion = false,
    this.availability,
    this.languages,
  });

  /// Null for a type this app version does not know (added to the server later).
  static SupportContact? fromRow(CachedSupportContactRow r) {
    final type = supportContactTypeFrom(r.type);
    if (type == null) return null;
    return SupportContact(
      id: r.id,
      type: type,
      label: r.label,
      value: r.value,
      whatsappMessage: r.whatsappMessage,
      emailSubject: r.emailSubject,
      includeAppVersion: r.includeAppVersion,
      availability: r.availability,
      languages: r.languages,
    );
  }
}

/// What the deck shows: the contacts, and the admin's optional note (null = hidden).
class SupportDeckData {
  final List<SupportContact> contacts;
  final String? note;

  const SupportDeckData(this.contacts, this.note);

  static const empty = SupportDeckData([], null);
}

/// The address to open for [c]. Pre-filled text carries only what the admin
/// wrote, plus the app version when the admin enabled it; never anything about
/// the learner (no name, learner ID or location). Null if the value is unusable.
Uri? supportUri(SupportContact c, {String? appVersionLine}) {
  String withVersion(String? text) => [
        if (text != null && text.trim().isNotEmpty) text.trim(),
        if (c.includeAppVersion && appVersionLine != null) appVersionLine,
      ].join('\n');

  switch (c.type) {
    case SupportContactType.phone:
      return Uri(scheme: 'tel', path: c.value);
    case SupportContactType.sms:
      return Uri(scheme: 'sms', path: c.value);
    case SupportContactType.email:
      // mailto wants %20 for spaces (not the + of query parameters), so encode by hand.
      final query = [
        if (c.emailSubject != null && c.emailSubject!.trim().isNotEmpty) 'subject=${Uri.encodeComponent(c.emailSubject!.trim())}',
        if (withVersion(null).isNotEmpty) 'body=${Uri.encodeComponent(withVersion(null))}',
      ].join('&');
      return Uri.parse('mailto:${c.value}${query.isEmpty ? '' : '?$query'}');
    case SupportContactType.whatsapp:
      final digits = c.value.replaceAll(RegExp(r'\D'), '');
      if (digits.isEmpty) return null;
      final text = withVersion(c.whatsappMessage);
      return Uri.parse('https://wa.me/$digits${text.isEmpty ? '' : '?text=${Uri.encodeComponent(text)}'}');
    case SupportContactType.link:
      final uri = Uri.tryParse(c.value);
      return uri != null && uri.scheme == 'https' && uri.host.isNotEmpty ? uri : null;
  }
}

/// Setting keys (app_settings table).
const kSupportSinceKey = 'support_contacts_since';
const kSupportAudienceKey = 'support_contacts_audience';
const kSupportNoteKey = 'support_deck_note';

final supportContactsServiceProvider = Provider<SupportContactsService>(
    (ref) => SupportContactsService(ref.read(apiClientProvider), ref.read(localDatabaseProvider)));

/// The deck's contents from the local database (works offline); re-read after
/// every sync.
final supportDeckProvider = FutureProvider<SupportDeckData>((ref) async {
  ref.watch(syncEngineProvider.select((s) => s.contentRevision));
  return ref.read(supportContactsServiceProvider).load();
});

/// Keeps the Support deck contacts on the phone: shows what is cached straight
/// away, and downloads only the changes since the last download (everything the
/// first time, or when the account's audience changed).
class SupportContactsService {
  final ApiClient _api;
  final LocalDatabase _db;

  SupportContactsService(this._api, this._db);

  Future<SupportDeckData> load() async {
    final contacts = [for (final r in await _db.getSupportContacts()) SupportContact.fromRow(r)].whereType<SupportContact>().toList();
    final note = (await _db.getSetting(kSupportNoteKey))?.trim();
    return SupportDeckData(contacts, note == null || note.isEmpty ? null : note);
  }

  /// [audience] names whose contacts these are (the learner role, or staff).
  /// Never throws; safe to repeat. A server without the endpoint (older
  /// backend) simply leaves the deck as it is (hidden when nothing is cached).
  Future<void> sync(String audience) async {
    try {
      final sameAudience = (await _db.getSetting(kSupportAudienceKey)) == audience;
      final since = sameAudience ? await _db.getSetting(kSupportSinceKey) : null;
      final resp = await _api.dio.get('/sync/support-contacts', queryParameters: {
        if (since != null && since.isNotEmpty) 'since': since,
      });
      final data = resp.data as Map<String, dynamic>;
      await _db.applySupportContacts(
        [
          for (final c in (data['contacts'] as List).cast<Map<String, dynamic>>())
            CachedSupportContactsCompanion.insert(
              id: c['id'] as String,
              type: c['type'] as String,
              label: c['label'] as String,
              value: c['value'] as String,
              whatsappMessage: Value(c['whatsapp_message'] as String?),
              emailSubject: Value(c['email_subject'] as String?),
              includeAppVersion: Value(c['include_app_version'] == true),
              availability: Value(c['availability'] as String?),
              languages: Value(c['languages'] as String?),
              displayOrder: Value((c['display_order'] as num?)?.toInt() ?? 0),
            ),
        ],
        (data['removed'] as List? ?? const []).cast<String>(),
        replaceAll: data['full'] == true,
      );
      await _db.setSetting(kSupportNoteKey, (data['note'] as String?) ?? '');
      await _db.setSetting(kSupportAudienceKey, audience);
      await _db.setSetting(kSupportSinceKey, data['server_time'] as String);
    } catch (_) {
      // Offline, or a server without the endpoint: keep what is cached.
    }
  }
}

/// Whose contacts the phone should hold: learners by learner role, staff all.
String supportAudienceOf(Ref ref) {
  final user = ref.read(authProvider).user;
  if (user == null) return '';
  return user.isLearner ? 'learner:${user.learnerRole ?? 'none'}' : 'staff';
}
