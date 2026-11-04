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
          audience: Value(m['audience'] as String? ?? 'GENERAL'),
          learnerRolesJson: Value(jsonEncode(m['learner_roles'] ?? const [])),
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

    await syncQuizzes();

    // Q&A passages (revised Phases 10/11). Kept separate from the content
    // sync's success: if this fails the modules are still usable, and the Ask
    // screen degrades gracefully (server fallback, or a clear "nothing
    // downloaded yet" message) rather than the whole sync reporting failure.
    try {
      final chunksResp = await _api.dio.get('/ai/chunks', queryParameters: {'language': 'en'});
      final chunks = chunksResp.data as List;
      await _db.replaceChunks('en', [
        for (final c in chunks)
          ContentChunksCompanion.insert(
            id: c['id'] as String,
            moduleId: c['module_id'] as String,
            moduleCode: c['module_code'] as String,
            sectionId: Value(c['section_id'] as String?),
            sectionTitle: Value(c['section_title'] as String?),
            language: c['language'] as String,
            sourceTitle: c['source_title'] as String,
            chunkText: c['chunk_text'] as String,
            faqQuestions: Value(encodeFaqQuestions(c['faq_questions'])),
          ),
      ]);
    } catch (_) {}

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

  /// Downloads the published translations for the language the person chose
  /// (nothing to do for English). Text that has no published translation simply
  /// stays in English on the phone. Never throws.
  Future<void> syncTranslations(String languageCode) async {
    if (languageCode == 'en') return;
    try {
      final resp = await _api.dio.get('/sync/translations', queryParameters: {'language': languageCode});
      final mods = ((resp.data as Map)['modules'] as List).cast<Map<String, dynamic>>();
      final known = {for (final m in await _db.getAllModules()) m.id};
      final moduleRows = <CachedTranslationsCompanion>[];
      final sectionRows = <CachedSectionTranslationsCompanion>[];
      for (final m in mods) {
        final moduleId = m['module_id'] as String;
        if (!known.contains(moduleId)) continue;
        moduleRows.add(CachedTranslationsCompanion.insert(
          id: '$moduleId:$languageCode',
          moduleId: moduleId,
          languageId: 'lang-$languageCode',
          languageCode: languageCode,
          title: m['title'] as String,
          description: Value(m['description'] as String?),
          body: Value(m['body'] as String?),
          audioText: Value(m['audio_text'] as String?),
          status: 'PUBLISHED',
        ));
        for (final s in (m['sections'] as List).cast<Map<String, dynamic>>()) {
          sectionRows.add(CachedSectionTranslationsCompanion.insert(
            sectionId: s['section_id'] as String,
            moduleId: moduleId,
            languageCode: languageCode,
            title: Value(s['title'] as String?),
            contentJson: jsonEncode(s['content']),
          ));
        }
      }
      // Modules with no published translation any more are cleared too.
      await _db.replaceLanguageTranslations(languageCode, known, moduleRows, sectionRows);
    } catch (_) {}
  }

  /// Downloads every module quiz (questions + answers; the phone grades) and
  /// any quiz pictures. Independent of release installs so quizzes reach the
  /// phone on every sync. Never throws: a failure just leaves the old quizzes.
  Future<void> syncQuizzes() async {
    try {
      final quizResp = await _api.dio.get('/sync/quiz-questions');
      final byModule = <String, List<Map<String, dynamic>>>{};
      for (final q in (quizResp.data as List).cast<Map<String, dynamic>>()) {
        byModule.putIfAbsent(q['module_id'] as String, () => []).add(q);
      }
      for (final m in await _db.getAllModules()) {
        final qs = byModule[m.id] ?? const <Map<String, dynamic>>[];
        await _db.replaceQuizForModule(m.id, [
          for (final q in qs)
            CachedQuizQuestionsCompanion.insert(
              id: q['id'] as String,
              moduleId: m.id,
              questionType: q['question_type'] as String,
              prompt: q['prompt'] as String,
              contentJson: jsonEncode(q['content']),
              explanation: Value(q['explanation'] as String?),
              sortOrder: q['sort_order'] as int,
              usage: Value(q['usage'] as String? ?? 'BOTH'),
            ),
        ]);
        for (final q in qs) {
          final assetId = (q['content'] as Map?)?['media_asset_id'] as String?;
          if (assetId != null) await _downloadMediaIfNeeded(assetId);
        }
      }
    } catch (_) {}
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
