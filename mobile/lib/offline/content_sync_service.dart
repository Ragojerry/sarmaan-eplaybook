import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:crypto/crypto.dart';
import 'package:dio/dio.dart';
import 'package:drift/drift.dart' show Value;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import '../db/local_database.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart' show apiClientProvider;

final localDatabaseProvider = Provider<LocalDatabase>((ref) {
  final db = LocalDatabase();
  ref.onDispose(db.close);
  return db;
});

final contentSyncServiceProvider = Provider<ContentSyncService>(
  (ref) => ContentSyncService(ref.read(apiClientProvider), ref.read(localDatabaseProvider)),
);

class SyncResult {
  final int moduleCount;
  final int sectionCount;
  final int mediaDownloaded;
  final int mediaFailed;

  SyncResult({
    required this.moduleCount,
    required this.sectionCount,
    required this.mediaDownloaded,
    required this.mediaFailed,
  });
}

/// Implements master prompt §18's offline-first principle: after this runs
/// once successfully, module reading, image viewing, and job aid access
/// must all work with zero network connectivity. This is what makes that
/// true — it's the one place that actually writes into LocalDatabase from
/// live API data. Local search, "mark as complete", and every reader/home/
/// modules screen read from the local cache this populates, never directly
/// from the network.
class ContentSyncService {
  final ApiClient _api;
  final LocalDatabase _db;

  ContentSyncService(this._api, this._db);

  Future<Directory> _mediaDir() async {
    final docs = await getApplicationDocumentsDirectory();
    final dir = Directory(p.join(docs.path, 'media'));
    if (!await dir.exists()) await dir.create(recursive: true);
    return dir;
  }

  /// Full sync: fetches every published module, its English translation and
  /// sections, downloads every referenced image (verifying its checksum
  /// against what the server recorded), and records the result as an
  /// installed release. Call this after login, and let the caller decide
  /// whether to show a progress UI — this service doesn't own that.
  Future<SyncResult> syncAll() async {
    final modulesResp = await _api.dio.get('/modules');
    final modules = (modulesResp.data as List).where((m) => m['status'] == 'PUBLISHED').toList();

    await _db.replaceModules([
      for (final m in modules)
        CachedModulesCompanion.insert(
          id: m['id'] as String,
          moduleCode: m['module_code'] as String,
          moduleNumber: m['module_number'] as int,
          title: m['title'] as String,
          description: Value(m['description'] as String?),
          status: m['status'] as String,
          sortOrder: m['sort_order'] as int,
          cachedAt: DateTime.now(),
        ),
    ]);

    int sectionCount = 0;
    int mediaDownloaded = 0;
    int mediaFailed = 0;

    for (final m in modules) {
      final moduleId = m['id'] as String;

      final translationsResp = await _api.dio.get('/modules/$moduleId/translations');
      final translations = translationsResp.data as List;
      await _db.replaceTranslationsForModule(moduleId, [
        for (final t in translations)
          CachedTranslationsCompanion.insert(
            id: t['id'] as String,
            moduleId: moduleId,
            languageId: t['language_id'] as String,
            // The backend translation response doesn't include the language
            // code directly (only language_id) — English is assumed here
            // since that's the only language with real migrated content
            // (docs/content-migration.md §8). Multi-language sync should
            // resolve this from GET /languages instead of assuming 'en'
            // once real translations exist for other languages.
            languageCode: 'en',
            title: t['title'] as String,
            description: Value(t['description'] as String?),
            body: Value(t['body'] as String?),
            audioText: Value(t['audio_text'] as String?),
            status: t['status'] as String,
          ),
      ]);

      final sectionsResp = await _api.dio.get('/modules/$moduleId/sections');
      final sections = sectionsResp.data as List;
      sectionCount += sections.length;

      await _db.replaceSectionsForModule(moduleId, [
        for (final s in sections)
          CachedSectionsCompanion.insert(
            id: s['id'] as String,
            moduleId: moduleId,
            sectionNumber: s['section_number'] as int,
            title: Value(s['title'] as String?),
            contentType: s['content_type'] as String,
            contentJson: jsonEncode(s['content']),
            sortOrder: s['sort_order'] as int,
          ),
      ]);

      for (final s in sections) {
        if (s['content_type'] == 'IMAGE') {
          final assetId = s['content']?['media_asset_id'] as String?;
          if (assetId == null) continue;
          final ok = await _downloadMediaIfNeeded(assetId);
          if (ok) {
            mediaDownloaded++;
          } else {
            mediaFailed++;
          }
        }
      }
    }

    await _db.recordInstalledRelease(
      releaseCode: 'local-sync-${DateTime.now().toIso8601String()}',
      version: '1.0.0',
      moduleCount: modules.length,
      sectionCount: sectionCount,
    );

    return SyncResult(
      moduleCount: modules.length,
      sectionCount: sectionCount,
      mediaDownloaded: mediaDownloaded,
      mediaFailed: mediaFailed,
    );
  }

  /// Downloads one media asset if it isn't already cached with a verified
  /// checksum. Returns false (not an exception) on failure — a single bad
  /// image must never abort the whole sync, per the offline-first principle
  /// that partial content is far better than none.
  Future<bool> _downloadMediaIfNeeded(String assetId) async {
    final existing = await _db.getMedia(assetId);
    if (existing != null && existing.localPath != null && await File(existing.localPath!).exists()) {
      return true; // already cached
    }

    try {
      final metaResp = await _api.dio.get('/media/$assetId');
      final meta = metaResp.data as Map<String, dynamic>;

      final fileResp = await _api.dio.get<List<int>>(
        '/media/$assetId/file',
        options: Options(responseType: ResponseType.bytes),
      );
      final bytes = Uint8List.fromList(fileResp.data!);

      final actualChecksum = sha256.convert(bytes).toString();
      final expectedChecksum = meta['checksum'] as String;
      if (actualChecksum != expectedChecksum) {
        // Never trust a corrupted/tampered download — treat as failed
        // rather than caching a file whose integrity can't be confirmed.
        return false;
      }

      final mediaDir = await _mediaDir();
      final filename = meta['filename'] as String;
      final file = File(p.join(mediaDir.path, filename));
      await file.writeAsBytes(bytes);

      await _db.upsertMedia(
        CachedMediaCompanion.insert(
          id: assetId,
          assetType: meta['asset_type'] as String,
          filename: filename,
          localPath: Value(file.path),
          checksum: expectedChecksum,
          sizeBytes: meta['size_bytes'] as int,
          mimeType: meta['mime_type'] as String,
          downloadedAt: Value(DateTime.now()),
        ),
      );
      return true;
    } catch (_) {
      return false;
    }
  }
}
