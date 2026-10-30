import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:crypto/crypto.dart';
import 'package:dio/dio.dart';
import 'package:drift/drift.dart' show Value;
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import '../db/local_database.dart';
import '../services/api_client.dart';
import 'analytics_recorder.dart';

/// A release the server is offering (GET /sync/release/current).
class ReleaseInfo {
  final String releaseCode;
  final String version;
  final bool mandatory;
  final String? description;
  final int? packageSize;
  final String? checksum;

  const ReleaseInfo({
    required this.releaseCode,
    required this.version,
    required this.mandatory,
    this.description,
    this.packageSize,
    this.checksum,
  });

  factory ReleaseInfo.fromJson(Map<String, dynamic> j) => ReleaseInfo(
        releaseCode: j['release_code'] as String,
        version: j['version'] as String,
        mandatory: j['mandatory'] as bool? ?? false,
        description: j['description'] as String?,
        packageSize: j['package_size'] as int?,
        checksum: j['checksum'] as String?,
      );
}

enum InstallStage { download, validate, media, apply, verify, done }

class InstallException implements Exception {
  final InstallStage stage;
  final String message;
  InstallException(this.stage, this.message);

  @override
  String toString() => 'Update failed while ${stage.name}: $message';
}

typedef InstallProgress = void Function(InstallStage stage, double fraction);

/// Installs a content release (master prompt §56):
///
///   download -> validate -> stage media -> apply -> verify -> activate
///
/// SAFETY RULE: nothing in the live local database changes until every
/// download has been fetched and checked. The swap itself is ONE database
/// transaction that also verifies row counts before it commits, so any failure
/// at any step leaves the previously installed release exactly as it was.
/// (Media files are staged under new names, so the old release's images stay
/// readable until the swap succeeds.)
class ReleaseInstaller {
  final ApiClient _api;
  final LocalDatabase _db;

  ReleaseInstaller(this._api, this._db);

  Future<Directory> _mediaDir() async {
    final docs = await getApplicationDocumentsDirectory();
    final dir = Directory(p.join(docs.path, 'media'));
    if (!await dir.exists()) await dir.create(recursive: true);
    return dir;
  }

  Future<void> install(ReleaseInfo release, {InstallProgress? onProgress}) async {
    void report(InstallStage s, double f) => onProgress?.call(s, f);

    // 1. DOWNLOAD the package and check it is byte-for-byte what was published.
    report(InstallStage.download, 0);
    final Uint8List bytes;
    try {
      final resp = await _api.dio.get<List<int>>(
        '/sync/release/${release.releaseCode}/package',
        options: Options(responseType: ResponseType.bytes, receiveTimeout: const Duration(minutes: 5)),
        onReceiveProgress: (received, total) {
          final expected = total > 0 ? total : (release.packageSize ?? 0);
          if (expected > 0) report(InstallStage.download, (received / expected).clamp(0.0, 1.0));
        },
      );
      bytes = Uint8List.fromList(resp.data!);
    } on DioException catch (e) {
      throw InstallException(InstallStage.download, e.message ?? 'network error');
    }

    // 2. VALIDATE integrity + structure before looking at any content.
    report(InstallStage.validate, 0);
    if (release.packageSize != null && bytes.length != release.packageSize) {
      throw InstallException(InstallStage.validate, 'size mismatch (got ${bytes.length}, expected ${release.packageSize})');
    }
    if (release.checksum != null && sha256.convert(bytes).toString() != release.checksum) {
      throw InstallException(InstallStage.validate, 'checksum mismatch — the download is corrupted');
    }
    final Map<String, dynamic> pkg;
    try {
      pkg = jsonDecode(utf8.decode(bytes)) as Map<String, dynamic>;
    } catch (_) {
      throw InstallException(InstallStage.validate, 'package is not valid JSON');
    }
    if (pkg['schema_version'] != 1) {
      throw InstallException(InstallStage.validate, 'unsupported package version ${pkg['schema_version']} — update the app');
    }
    final modules = (pkg['modules'] as List).cast<Map<String, dynamic>>();
    final media = (pkg['media'] as List).cast<Map<String, dynamic>>();
    final chunks = (pkg['chunks'] as List).cast<Map<String, dynamic>>();
    final counts = pkg['counts'] as Map<String, dynamic>;
    final sectionTotal = modules.fold<int>(0, (n, m) => n + (m['sections'] as List).length);
    if (modules.isEmpty ||
        counts['modules'] != modules.length ||
        counts['sections'] != sectionTotal ||
        counts['media'] != media.length ||
        counts['chunks'] != chunks.length) {
      throw InstallException(InstallStage.validate, 'package contents do not match its own manifest');
    }
    report(InstallStage.validate, 1);

    // 3. STAGE media: only files whose checksum is new or missing are downloaded.
    final staged = <String, String>{}; // media id -> local path
    final mediaDir = await _mediaDir();
    final existing = {for (final m in await _db.getAllMedia()) m.id: m};
    var done = 0;
    for (final m in media) {
      final id = m['id'] as String;
      final checksum = m['checksum'] as String;
      final have = existing[id];
      if (have != null && have.checksum == checksum && have.localPath != null && await File(have.localPath!).exists()) {
        staged[id] = have.localPath!;
      } else {
        staged[id] = await _downloadMedia(m, mediaDir);
      }
      done++;
      report(InstallStage.media, media.isEmpty ? 1 : done / media.length);
    }

    // 4+5. APPLY and VERIFY in one transaction; throwing rolls everything back.
    report(InstallStage.apply, 0);
    final moduleIds = <String>{for (final m in modules) m['id'] as String};
    final languages = <String>{for (final c in chunks) c['language'] as String};
    final now = DateTime.now();
    try {
      await _db.transaction(() async {
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
              cachedAt: now,
            ),
        ]);
        for (final m in modules) {
          final moduleId = m['id'] as String;
          await _db.replaceTranslationsForModule(moduleId, [
            for (final t in (m['translations'] as List).cast<Map<String, dynamic>>())
              CachedTranslationsCompanion.insert(
                id: t['id'] as String,
                moduleId: moduleId,
                languageId: t['language_id'] as String,
                languageCode: t['language_code'] as String,
                title: t['title'] as String,
                description: Value(t['description'] as String?),
                body: Value(t['body'] as String?),
                audioText: Value(t['audio_text'] as String?),
                status: t['status'] as String,
              ),
          ]);
          // An empty list is ignored here: quizzes are refreshed on every sync
          // from /sync/quiz-questions, and an older package must not wipe them.
          if (((m['quiz_questions'] as List?) ?? const []).isNotEmpty)
          await _db.replaceQuizForModule(moduleId, [
            for (final q in ((m['quiz_questions'] as List?) ?? const []).cast<Map<String, dynamic>>())
              CachedQuizQuestionsCompanion.insert(
                id: q['id'] as String,
                moduleId: moduleId,
                questionType: q['question_type'] as String,
                prompt: q['prompt'] as String,
                contentJson: jsonEncode(q['content']),
                explanation: Value(q['explanation'] as String?),
                sortOrder: q['sort_order'] as int,
              ),
          ]);
          await _db.replaceSectionsForModule(moduleId, [
            for (final s in (m['sections'] as List).cast<Map<String, dynamic>>())
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
        }
        await _db.deleteContentOutside(moduleIds, languages);

        for (final lang in languages) {
          await _db.replaceChunks(lang, [
            for (final c in chunks.where((c) => c['language'] == lang))
              ContentChunksCompanion.insert(
                id: c['id'] as String,
                moduleId: c['module_id'] as String,
                moduleCode: c['module_code'] as String,
                sectionId: Value(c['section_id'] as String?),
                sectionTitle: Value(c['section_title'] as String?),
                language: c['language'] as String,
                sourceTitle: c['source_title'] as String,
                chunkText: c['chunk_text'] as String,
              ),
          ]);
        }

        for (final m in media) {
          final id = m['id'] as String;
          await _db.upsertMedia(
            CachedMediaCompanion.insert(
              id: id,
              assetType: m['asset_type'] as String,
              filename: m['filename'] as String,
              localPath: Value(staged[id]),
              checksum: m['checksum'] as String,
              sizeBytes: m['size_bytes'] as int,
              mimeType: m['mime_type'] as String,
              downloadedAt: Value(now),
            ),
          );
        }

        // VERIFY what is actually in the database before committing.
        if (await _db.countModules() != modules.length ||
            await _db.countSections() != sectionTotal ||
            await _db.countChunks() != chunks.length) {
          throw InstallException(InstallStage.verify, 'stored content does not match the package');
        }

        // ACTIVATE: this row is what makes the release "current".
        await _db.recordInstalledRelease(
          releaseCode: release.releaseCode,
          version: release.version,
          moduleCount: modules.length,
          sectionCount: sectionTotal,
        );
      });
    } on InstallException {
      rethrow;
    } catch (e) {
      throw InstallException(InstallStage.apply, '$e');
    }
    report(InstallStage.apply, 1);

    // Best-effort tidy-up AFTER success: images that left the release, and
    // superseded files for images whose checksum changed.
    try {
      final keepPaths = staged.values.toSet();
      for (final old in existing.values) {
        if (!staged.containsKey(old.id)) await _db.deleteMedia(old.id);
        final path = old.localPath;
        if (path != null && !keepPaths.contains(path)) {
          final f = File(path);
          if (await f.exists()) await f.delete();
        }
      }
    } catch (_) {}
    report(InstallStage.done, 1);
  }

  /// Downloads one image to a temp file, verifies its SHA-256, then renames it
  /// into place. The name embeds the checksum so a changed image never
  /// overwrites the file the current release is still showing.
  Future<String> _downloadMedia(Map<String, dynamic> m, Directory dir) async {
    final id = m['id'] as String;
    final checksum = m['checksum'] as String;
    try {
      final resp = await _api.dio.get<List<int>>(
        '/media/$id/file',
        options: Options(responseType: ResponseType.bytes),
      );
      final bytes = Uint8List.fromList(resp.data!);
      if (sha256.convert(bytes).toString() != checksum) {
        throw InstallException(InstallStage.media, '${m['filename']}: checksum mismatch');
      }
      final target = File(p.join(dir.path, '${id}_${checksum.substring(0, 12)}_${m['filename']}'));
      final tmp = File('${target.path}.part');
      await tmp.writeAsBytes(bytes, flush: true);
      await tmp.rename(target.path);
      return target.path;
    } on DioException catch (e) {
      throw InstallException(InstallStage.media, '${m['filename']}: ${e.message ?? 'network error'}');
    } on FileSystemException catch (e) {
      await recordAnalyticsEvent(_db, 'STORAGE_ERROR', payload: {'stage': 'install_media'});
      throw InstallException(InstallStage.media, 'storage problem: ${e.message}');
    }
  }
}
