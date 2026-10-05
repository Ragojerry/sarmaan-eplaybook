import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../db/local_database.dart';
import '../models/api_models.dart';
import '../offline/content_sync_service.dart' show localDatabaseProvider;

final settingsServiceProvider = Provider<SettingsService>((ref) => SettingsService(ref.read(localDatabaseProvider)));

/// Backed by the Drift `app_settings` table (master prompt §19) — replaces
/// the Phase 7 SharedPreferences-based version now that Phase 8 has a real
/// local database. One local storage technology, not two.
class SettingsService {
  final LocalDatabase _db;

  SettingsService(this._db);

  static const _firstLaunchDoneKey = 'first_launch_done';
  static const _selectedLanguageCodeKey = 'selected_language_code';
  static const _cachedLanguagesKey = 'cached_languages_json';

  Future<bool> isFirstLaunch() async {
    final value = await _db.getSetting(_firstLaunchDoneKey);
    return value != 'true';
  }

  Future<void> markFirstLaunchDone() async {
    await _db.setSetting(_firstLaunchDoneKey, 'true');
  }

  Future<String?> getSelectedLanguageCode() async {
    return _db.getSetting(_selectedLanguageCodeKey);
  }

  Future<void> setSelectedLanguageCode(String code) async {
    await _db.setSetting(_selectedLanguageCodeKey, code);
  }

  /// No dedicated `cached_languages` table exists in master prompt §19's
  /// schema list — the language set is small and changes rarely, so it's
  /// stored as one JSON blob under `app_settings` rather than adding a new
  /// table just for this. Returns null if nothing has been cached yet
  /// (fresh install, never successfully synced).
  Future<List<AppLanguage>?> getCachedLanguages() async {
    final raw = await _db.getSetting(_cachedLanguagesKey);
    if (raw == null) return null;
    try {
      final list = jsonDecode(raw) as List;
      return list.map((j) => AppLanguage.fromJson(j as Map<String, dynamic>)).toList();
    } catch (_) {
      // Corrupted/unreadable cache — treat exactly like "nothing cached"
      // rather than crashing the language picker over stored garbage.
      return null;
    }
  }

  Future<void> setCachedLanguages(List<AppLanguage> languages) async {
    final encoded = jsonEncode([
      for (final l in languages)
        {
          'id': l.id,
          'code': l.code,
          'name': l.name,
          'native_name': l.nativeName,
          'status': l.status,
          'is_default': l.isDefault,
        },
    ]);
    await _db.setSetting(_cachedLanguagesKey, encoded);
  }
}
