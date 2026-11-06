import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';

import '../db/local_database.dart';

/// Which curriculum the installed content is ("legacy" = the old M1-M6,
/// "hfw-2026" = the HFW flipbook modules). Set by the release installer.
const kInstalledCurriculumKey = 'installed_curriculum';

/// Set when an installed release changed the curriculum; the Home screen shows
/// the one-time "training updated" notice and clears it.
const kPendingTrainingNoticeKey = 'pending_training_notice';

/// Lowest app version the server allows (GET /sync/learning: min_app_version).
const kMinAppVersionKey = 'min_app_version';

/// Message shown once after the changeover. The Hausa text is a DRAFT that a
/// native speaker must review before release (content/hfw_flipbook/open_questions.md).
const trainingNotice = {
  'en': 'The training has been updated. Start the new modules.',
  'ha': 'An sabunta horon. Fara sababbin darussa.',
};

const updateRequiredText = {
  'en': 'Training updated, please update the app.',
  'ha': 'An sabunta horo, da fatan za a sabunta manhajar.',
};

String inLanguage(Map<String, String> texts, String? code) => texts[code] ?? texts['en']!;

/// Called by the release installer BEFORE it replaces the content, with the
/// curriculum of the incoming package. A phone that had content but no record
/// (an app updated from 0.1.9 or older) is treated as having the old curriculum.
Future<String?> previousCurriculum(LocalDatabase db) async {
  final saved = await db.getSetting(kInstalledCurriculumKey);
  if (saved != null && saved.isNotEmpty) return saved;
  return await db.countModules() > 0 ? 'legacy' : null; // null: first install, nothing to announce
}

/// Called AFTER a successful install.
Future<void> recordCurriculum(LocalDatabase db, String? previous, String? incoming) async {
  final now = (incoming == null || incoming.isEmpty) ? 'legacy' : incoming;
  await db.setSetting(kInstalledCurriculumKey, now);
  if (previous != null && previous != now && now != 'legacy') {
    await db.setSetting(kPendingTrainingNoticeKey, now);
  }
}

Future<bool> hasPendingTrainingNotice(LocalDatabase db) async =>
    ((await db.getSetting(kPendingTrainingNoticeKey)) ?? '').isNotEmpty;

Future<void> clearTrainingNotice(LocalDatabase db) => db.setSetting(kPendingTrainingNoticeKey, '');

bool _noticeOpen = false;

/// Shows the one-time "training updated" notice if one is waiting, in the
/// learner's language, and clears it once dismissed. Returns whether it showed.
Future<bool> showTrainingNoticeIfPending(BuildContext context, LocalDatabase db) async {
  if (_noticeOpen || !await hasPendingTrainingNotice(db)) return false;
  final lang = await db.getSetting('selected_language_code');
  if (!context.mounted) return false;
  _noticeOpen = true;
  try {
    await showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: const Icon(Icons.campaign_outlined, size: 36),
        content: Text(inLanguage(trainingNotice, lang), textAlign: TextAlign.center),
        actions: [
          // "To" is the Hausa "OK" (draft, for native review).
          FilledButton(onPressed: () => Navigator.of(ctx).pop(), child: Text(lang == 'ha' ? 'To' : 'OK')),
        ],
      ),
    );
    await clearTrainingNotice(db);
    return true;
  } finally {
    _noticeOpen = false;
  }
}

/// True when [current] (e.g. "0.1.9" or "0.1.9+10") is lower than [minimum].
bool isOlderVersion(String current, String minimum) {
  List<int> parts(String v) => v.split('+').first.split('.').map((p) => int.tryParse(p.trim()) ?? 0).toList();
  final a = parts(current), b = parts(minimum);
  for (var i = 0; i < 3; i++) {
    final x = i < a.length ? a[i] : 0, y = i < b.length ? b[i] : 0;
    if (x != y) return x < y;
  }
  return false;
}

/// True when the server asks for a newer app than this one.
Future<bool> updateRequired(LocalDatabase db, {Future<String> Function()? appVersion}) async {
  final minimum = await db.getSetting(kMinAppVersionKey);
  if (minimum == null || minimum.isEmpty) return false;
  final version = await (appVersion ?? () async => (await PackageInfo.fromPlatform()).version)();
  return isOlderVersion(version, minimum);
}
