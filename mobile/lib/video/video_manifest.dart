import 'dart:io';

import 'package:dio/dio.dart';
import 'package:drift/drift.dart';

import '../db/local_database.dart';
import '../services/api_client.dart';
import 'video_downloads.dart' show adoptLegacyVideoDownloads;

/// One video in the manifest (GET /sync/videos): what it is and where to fetch it.
/// The phone keeps a copy in cached_videos so the Videos tab and the video screen
/// work offline. The manifest never makes the phone download anything.
class VideoEntry {
  final String videoId;
  final String? moduleId;
  final String title;
  final String language;
  final int sizeBytes;
  final int? durationSeconds;
  final String contentHash; // SHA-256 hex
  final String url; // CloudFront (or /videos/{id}/file on a development server)
  final int version;
  final bool requiredForCompletion; // nothing reads it: training never waits for a video
  final String mimeType;

  const VideoEntry({
    required this.videoId,
    required this.moduleId,
    required this.title,
    required this.language,
    required this.sizeBytes,
    required this.durationSeconds,
    required this.contentHash,
    required this.url,
    required this.version,
    required this.requiredForCompletion,
    required this.mimeType,
  });

  factory VideoEntry.fromJson(Map<String, dynamic> j) => VideoEntry(
        videoId: j['video_id'] as String,
        moduleId: j['module_id'] as String?,
        title: j['title'] as String,
        language: (j['language'] as String?) ?? 'en',
        sizeBytes: (j['size_bytes'] as num).toInt(),
        durationSeconds: (j['duration_seconds'] as num?)?.toInt(),
        contentHash: j['content_hash'] as String,
        url: j['url'] as String,
        version: (j['version'] as num?)?.toInt() ?? 1,
        requiredForCompletion: j['required_for_completion'] as bool? ?? false,
        mimeType: (j['mime_type'] as String?) ?? 'video/mp4',
      );

  static VideoEntry? fromRow(CachedVideoRow r) {
    if (!r.manifestSeen || r.url == null || r.sizeBytes == null || r.contentHash == null) return null;
    return VideoEntry(
      videoId: r.id,
      moduleId: r.moduleId,
      title: r.title,
      language: r.language,
      sizeBytes: r.sizeBytes!,
      durationSeconds: r.durationSeconds,
      contentHash: r.contentHash!,
      url: r.url!,
      version: r.version,
      requiredForCompletion: r.requiredForCompletion,
      mimeType: r.mimeType ?? 'video/mp4',
    );
  }
}

/// Replaces the stored manifest with [entries]. Videos no longer listed (unpublished,
/// or in a module this account cannot see) are forgotten; their downloaded files are
/// returned for the caller to delete.
Future<List<String>> storeVideoManifest(LocalDatabase db, List<VideoEntry> entries) async {
  final ids = {for (final e in entries) e.videoId};
  final stale = <String>[];
  await db.transaction(() async {
    for (final e in entries) {
      await db.into(db.cachedVideos).insert(
            CachedVideosCompanion.insert(
              id: e.videoId,
              title: e.title,
              moduleId: Value(e.moduleId),
              durationSeconds: Value(e.durationSeconds),
              language: e.language,
              offlineAvailable: true,
              status: 'PUBLISHED',
              hasFile: true,
              sizeBytes: Value(e.sizeBytes),
              contentHash: Value(e.contentHash),
              url: Value(e.url),
              version: Value(e.version),
              requiredForCompletion: Value(e.requiredForCompletion),
              mimeType: Value(e.mimeType),
              manifestSeen: const Value(true),
            ),
            onConflict: DoUpdate((old) => CachedVideosCompanion(
                  title: Value(e.title),
                  moduleId: Value(e.moduleId),
                  durationSeconds: Value(e.durationSeconds),
                  language: Value(e.language),
                  sizeBytes: Value(e.sizeBytes),
                  contentHash: Value(e.contentHash),
                  url: Value(e.url),
                  version: Value(e.version),
                  requiredForCompletion: Value(e.requiredForCompletion),
                  mimeType: Value(e.mimeType),
                  manifestSeen: const Value(true),
                )),
          );
    }
    for (final row in await (db.select(db.cachedVideos)..where((v) => v.manifestSeen.equals(true))).get()) {
      if (ids.contains(row.id)) continue;
      final d = await (db.select(db.videoDownloads)..where((x) => x.videoId.equals(row.id))).getSingleOrNull();
      if (d?.localPath != null) stale.add(d!.localPath!);
      await (db.delete(db.videoDownloads)..where((x) => x.videoId.equals(row.id))).go();
      await (db.delete(db.cachedVideos)..where((x) => x.id.equals(row.id))).go();
    }
  });
  return stale;
}

Future<List<VideoEntry>> allVideoEntries(LocalDatabase db) async {
  final rows = await (db.select(db.cachedVideos)..orderBy([(v) => OrderingTerm.asc(v.title)])).get();
  return rows.map(VideoEntry.fromRow).whereType<VideoEntry>().toList();
}

Future<List<VideoEntry>> videosOfModule(LocalDatabase db, String moduleId) async =>
    [for (final e in await allVideoEntries(db)) if (e.moduleId == moduleId) e];

Future<VideoEntry?> videoEntry(LocalDatabase db, String videoId) async {
  final row = await (db.select(db.cachedVideos)..where((v) => v.id.equals(videoId))).getSingleOrNull();
  return row == null ? null : VideoEntry.fromRow(row);
}

/// The content-sync step for videos: fetches the manifest only (never a video),
/// keeps it, forgets videos no longer listed and recognises videos the old app
/// downloaded. A server without the manifest (older backend) leaves things as they are.
Future<void> refreshVideoManifest(ApiClient api, LocalDatabase db) async {
  final Response<dynamic> resp;
  try {
    resp = await api.dio.get('/sync/videos');
  } on DioException catch (e) {
    if (e.response?.statusCode == 404) return;
    rethrow;
  }
  final entries = [for (final j in (resp.data['videos'] as List)) VideoEntry.fromJson(j as Map<String, dynamic>)];
  for (final path in await storeVideoManifest(db, entries)) {
    await _deleteQuietly(path);
  }
  await adoptLegacyVideoDownloads(db);
}

Future<void> _deleteQuietly(String path) async {
  try {
    final f = File(path);
    if (await f.exists()) await f.delete();
  } catch (_) {}
}
