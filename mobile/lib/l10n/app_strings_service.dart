import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../db/local_database.dart';
import '../offline/content_sync_service.dart' show localDatabaseProvider;
import '../services/api_client.dart';
import '../services/auth_service.dart' show apiClientProvider;
import 'l10n.dart';

final appStringsServiceProvider =
    Provider<AppStringsService>((ref) => AppStringsService(ref.read(apiClientProvider), ref.read(localDatabaseProvider)));

/// Keeps the interface text in the learner's language: shows what is cached on
/// the phone straight away (works offline), and downloads published changes in
/// the background. The same language setting drives content and interface.
class AppStringsService {
  final ApiClient _api;
  final LocalDatabase _db;

  AppStringsService(this._api, this._db);

  static String _sinceKey(String code) => 'app_strings_since_$code';

  /// Shows [code] using only what is stored on the phone (English for 'en' or
  /// anything not downloaded yet).
  Future<void> show(String code) async {
    L10n.instance.apply(code, code == 'en' ? const {} : await _db.getAppStrings(code));
  }

  /// Downloads the published strings for [code] that changed since the last
  /// download (all of them the first time), stores them and shows them if
  /// [code] is still the chosen language. Never throws; safe to repeat.
  Future<void> sync(String code) async {
    if (code == 'en') return;
    try {
      final since = await _db.getSetting(_sinceKey(code));
      final resp = await _api.dio.get('/sync/app-strings', queryParameters: {
        'language': code,
        if (since != null && since.isNotEmpty) 'since': since,
      });
      final data = resp.data as Map<String, dynamic>;
      final strings = <String, String>{};
      for (final s in (data['strings'] as List).cast<Map<String, dynamic>>()) {
        final key = s['key'] as String;
        strings[key] = s['text'] as String;
        final one = s['text_one'] as String?;
        if (one != null && one.isNotEmpty) strings['$key#one'] = one;
      }
      await _db.applyAppStrings(code, strings, (data['removed'] as List? ?? const []).cast<String>(),
          replaceAll: data['full'] == true);
      await _db.setSetting(_sinceKey(code), data['server_time'] as String);
      if (L10n.instance.code == code) await show(code);
    } catch (_) {
      // Offline or the server is unreachable: keep what is cached (or English).
    }
  }
}
