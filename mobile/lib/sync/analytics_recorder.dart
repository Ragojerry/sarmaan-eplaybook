import 'dart:convert';

import '../db/local_database.dart';

/// app_settings keys
const kAnalyticsConsentKey = 'analytics_consent';
const _kSelectedLanguageKey = 'selected_language_code';

/// Upper bound on queued, not-yet-uploaded events so a phone that never gets
/// online cannot grow its database without limit.
const _kMaxQueuedEvents = 2000;

/// Queues one usage event (master prompt §50) for upload by the sync engine.
///
/// PRIVACY: records nothing at all unless the person opted in (consent screen /
/// Sync & updates). Events carry only the event type, which module/video it
/// concerns, the language, and a tiny payload (never question text, answers,
/// names or file paths). Analytics must never break the feature that emitted
/// them, so every failure here is swallowed.
Future<void> recordAnalyticsEvent(
  LocalDatabase db,
  String eventType, {
  String? moduleId,
  String? videoId,
  String? language,
  Map<String, dynamic>? payload,
}) async {
  try {
    if ((await db.getSetting(kAnalyticsConsentKey)) != 'true') return;
    if (await db.countPending(entityTypes: ['analytics']) >= _kMaxQueuedEvents) return;
    final lang = language ?? await db.getSetting(_kSelectedLanguageKey);
    await db.enqueueSync(
      'analytics',
      jsonEncode({
        'event_type': eventType,
        'module_id': moduleId,
        'video_id': videoId,
        'language': lang,
        'payload': payload ?? <String, dynamic>{},
        'occurred_at': DateTime.now().toUtc().toIso8601String(),
      }),
    );
  } catch (_) {}
}
