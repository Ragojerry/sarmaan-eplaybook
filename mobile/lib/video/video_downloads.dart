import 'dart:async';
import 'dart:io';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:crypto/crypto.dart';
import 'package:dio/dio.dart';
import 'package:drift/drift.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:video_player/video_player.dart';

import '../db/local_database.dart';
import '../offline/content_sync_service.dart' show localDatabaseProvider;
import '../services/api_client.dart';
import '../services/auth_service.dart' show apiClientProvider;
import '../sync/analytics_recorder.dart';
import 'video_manifest.dart';

/// Videos download only when the learner asks (tap to watch, or a "download"
/// button), never during sync. Downloads write to <id>.v<version>.part, resume
/// with HTTP Range from the saved offset (after a dropped connection, a closed
/// app or a restart), and become playable only once their size and SHA-256
/// match the manifest. Nothing in training depends on any of this.

/// Above this size, a download over mobile data asks first.
const kMobileDataWarnBytes = 10 * 1024 * 1024;

/// Downloads run one at a time (low-end phones, shared connections).
const kMaxParallelDownloads = 1;

/// Room left free on the phone after a download.
const kFreeSpaceMarginBytes = 50 * 1024 * 1024;

enum VideoDownloadState { notDownloaded, downloading, paused, failed, downloaded }

enum VideoDownloadError { network, corrupt, notFound, storage }

enum StartResult { started, alreadyQueued, alreadyDownloaded, offline, needsMobileDataConfirm, notEnoughSpace, unknownVideo }

const _stateNames = {
  VideoDownloadState.notDownloaded: 'not_downloaded',
  VideoDownloadState.downloading: 'downloading',
  VideoDownloadState.paused: 'paused',
  VideoDownloadState.failed: 'failed',
  VideoDownloadState.downloaded: 'downloaded',
};

VideoDownloadState _stateOf(String? name) =>
    _stateNames.entries.firstWhere((e) => e.value == name, orElse: () => _stateNames.entries.first).key;

String formatBytes(int bytes) {
  const mb = 1024 * 1024;
  if (bytes >= mb) {
    final v = bytes / mb;
    return '${v >= 10 || v == v.roundToDouble() ? v.round() : v.toStringAsFixed(1)} MB';
  }
  return '${(bytes / 1024).ceil()} KB';
}

/// SHA-256 of a file, read in chunks (never the whole video in memory).
Future<String> fileSha256(File f) async => (await sha256.bind(f.openRead()).first).toString();

// ---- what the manager talks to (real ones at the bottom; fakes in tests) ----

class FetchResponse {
  final int statusCode;
  final String? contentType;
  final int start; // first byte in the body
  final int? totalSize; // whole file, when the server says
  final Stream<List<int>> body;
  const FetchResponse({required this.statusCode, required this.contentType, required this.start, required this.totalSize, required this.body});
}

class VideoFetchException implements Exception {
  final VideoDownloadError kind;
  final String detail;
  VideoFetchException(this.kind, this.detail);
  @override
  String toString() => 'VideoFetchException($kind, $detail)';
}

abstract class VideoFetcher {
  Future<FetchResponse> get(String url, {int from = 0, CancelToken? cancel});
}

abstract class VideoNetwork {
  Future<bool> isOnline();
  Future<bool> isMobileData();
}

abstract class VideoDiskSpace {
  /// Free bytes, or null when the phone cannot say (then the download is allowed).
  Future<int?> freeBytes();
}

class VideoDownloadStatus {
  final String videoId;
  final VideoDownloadState state;
  final int bytesDownloaded;
  final int totalBytes;
  final String? localPath; // verified file; plays even while an update downloads
  final int version;
  final String? contentHash;
  final VideoDownloadError? error;
  final bool updateAvailable;
  final bool active; // bytes are arriving now
  final bool queued;

  const VideoDownloadStatus({
    required this.videoId,
    required this.state,
    this.bytesDownloaded = 0,
    this.totalBytes = 0,
    this.localPath,
    this.version = 0,
    this.contentHash,
    this.error,
    this.updateAvailable = false,
    this.active = false,
    this.queued = false,
  });

  double get progress => totalBytes <= 0 ? 0 : (bytesDownloaded / totalBytes).clamp(0.0, 1.0);
  bool get playable => localPath != null;
  bool get busy => active || queued;
}

/// Checks videos the old app downloaded against the manifest; a match becomes
/// "downloaded" with no second download, a mismatch is removed. Returns how many matched.
Future<int> adoptLegacyVideoDownloads(LocalDatabase db) async {
  var adopted = 0;
  final rows = await (db.select(db.videoDownloads)
        ..where((d) => d.state.equals('not_downloaded') & d.localPath.isNotNull() & d.contentHash.isNull()))
      .get();
  for (final row in rows) {
    final entry = await videoEntry(db, row.videoId);
    if (entry == null) continue; // not in the manifest (yet): keep the file, check next time
    final file = File(row.localPath!);
    final ok = await file.exists() && await file.length() == entry.sizeBytes && await fileSha256(file) == entry.contentHash;
    if (ok) {
      adopted++;
      await (db.update(db.videoDownloads)..where((d) => d.videoId.equals(row.videoId))).write(VideoDownloadsCompanion(
            state: const Value('downloaded'),
            bytesDownloaded: Value(entry.sizeBytes),
            totalBytes: Value(entry.sizeBytes),
            contentHash: Value(entry.contentHash),
            version: Value(entry.version),
            updatedAt: Value(DateTime.now()),
          ));
    } else {
      try {
        if (await file.exists()) await file.delete();
      } catch (_) {}
      await (db.update(db.videoDownloads)..where((d) => d.videoId.equals(row.videoId)))
          .write(VideoDownloadsCompanion(localPath: const Value(null), updatedAt: Value(DateTime.now())));
    }
  }
  return adopted;
}

typedef DownloadLog = Future<void> Function(String eventType, String videoId, Map<String, dynamic> payload);

class VideoDownloadManager extends ChangeNotifier {
  final LocalDatabase db;
  final Future<Directory> Function() directory;
  final VideoFetcher fetcher;
  final VideoNetwork network;
  final VideoDiskSpace disk;
  final DownloadLog? log;

  VideoDownloadManager({required this.db, required this.directory, required this.fetcher, required this.network, required this.disk, this.log});

  final _queue = <String>[];
  final _active = <String>{};
  final _cancelTokens = <String, CancelToken>{};
  final _stopReason = <String, VideoDownloadState>{}; // paused or notDownloaded (cancel)
  final _live = <String, int>{}; // bytes on disk while downloading
  final _idle = <Completer<void>>[];
  bool _disposed = false;

  @override
  void dispose() {
    _disposed = true;
    for (final t in _cancelTokens.values) {
      t.cancel('closing');
    }
    super.dispose();
  }

  void _changed() {
    if (!_disposed) notifyListeners();
  }

  /// Resumes downloads that were running when the app closed or the connection dropped.
  Future<void> init() => resumeInterrupted();

  Future<void> resumeInterrupted() async {
    if (!await network.isOnline()) return;
    final rows = await (db.select(db.videoDownloads)..where((d) => d.state.equals('downloading'))).get();
    for (final r in rows) {
      if (!_queue.contains(r.videoId) && !_active.contains(r.videoId)) _queue.add(r.videoId);
    }
    _pump();
  }

  static Future<VideoDownloadStatus> readStatus(LocalDatabase db, String videoId) async {
    final row = await (db.select(db.videoDownloads)..where((d) => d.videoId.equals(videoId))).getSingleOrNull();
    final entry = await videoEntry(db, videoId);
    return _status(videoId, row, entry);
  }

  static VideoDownloadStatus _status(String id, VideoDownloadRow? row, VideoEntry? entry, {bool active = false, bool queued = false, int? live}) {
    if (row == null) {
      return VideoDownloadStatus(videoId: id, state: VideoDownloadState.notDownloaded, totalBytes: entry?.sizeBytes ?? 0, active: active, queued: queued);
    }
    final playable = row.localPath != null && row.contentHash != null;
    final update = playable && entry != null && (row.version != entry.version || row.contentHash != entry.contentHash);
    return VideoDownloadStatus(
      videoId: id,
      state: _stateOf(row.state),
      bytesDownloaded: live ?? row.bytesDownloaded,
      totalBytes: row.totalBytes > 0 ? row.totalBytes : (entry?.sizeBytes ?? 0),
      localPath: playable ? row.localPath : null,
      version: row.version,
      contentHash: row.contentHash,
      error: row.error == null ? null : VideoDownloadError.values.where((e) => e.name == row.error).firstOrNull,
      updateAvailable: update,
      active: active,
      queued: queued,
    );
  }

  Future<VideoDownloadStatus> statusOf(String videoId) async {
    final row = await (db.select(db.videoDownloads)..where((d) => d.videoId.equals(videoId))).getSingleOrNull();
    final entry = await videoEntry(db, videoId);
    return _status(videoId, row, entry, active: _active.contains(videoId), queued: _queue.contains(videoId), live: _live[videoId]);
  }

  bool needsMobileDataWarning(VideoEntry e, {required bool onMobileData}) => onMobileData && e.sizeBytes > kMobileDataWarnBytes;

  /// The learner asked for this video (tap to watch, Download, Resume, Retry, Update).
  Future<StartResult> start(String videoId, {bool confirmedMobileData = false}) async {
    final entry = await videoEntry(db, videoId);
    if (entry == null) return StartResult.unknownVideo;
    if (_active.contains(videoId) || _queue.contains(videoId)) return StartResult.alreadyQueued;
    final status = await statusOf(videoId);
    if (status.state == VideoDownloadState.downloaded && !status.updateAvailable) return StartResult.alreadyDownloaded;
    if (!await network.isOnline()) return StartResult.offline;
    if (!confirmedMobileData && needsMobileDataWarning(entry, onMobileData: await network.isMobileData())) {
      return StartResult.needsMobileDataConfirm;
    }
    final part = await _partFile(entry);
    final have = await part.exists() ? await part.length() : 0;
    final free = await disk.freeBytes();
    if (free != null && free < (entry.sizeBytes - have) + kFreeSpaceMarginBytes) return StartResult.notEnoughSpace;
    if (_active.contains(videoId) || _queue.contains(videoId)) return StartResult.alreadyQueued; // tapped twice meanwhile
    await _write(videoId, state: VideoDownloadState.downloading, total: entry.sizeBytes, bytes: have, error: null);
    _queue.add(videoId);
    unawaited(log?.call('DOWNLOAD_STARTED', videoId, {'bytes': entry.sizeBytes, 'resume_from': have, 'version': entry.version}));
    _changed();
    _pump();
    return StartResult.started;
  }

  /// "Download videos for this module" / "Download all videos": queued, one at a time.
  Future<Map<String, StartResult>> startAll(Iterable<String> videoIds, {bool confirmedMobileData = false}) async =>
      {for (final id in videoIds) id: await start(id, confirmedMobileData: confirmedMobileData)};

  Future<void> pause(String videoId) async {
    if (_queue.remove(videoId)) {
      await _write(videoId, state: VideoDownloadState.paused);
    } else if (_active.contains(videoId)) {
      _stopReason[videoId] = VideoDownloadState.paused;
      _cancelTokens[videoId]?.cancel('paused');
    }
    _changed();
  }

  Future<void> cancel(String videoId) async {
    _queue.remove(videoId);
    if (_active.contains(videoId)) {
      _stopReason[videoId] = VideoDownloadState.notDownloaded;
      _cancelTokens[videoId]?.cancel('cancelled');
      await whenIdleFor(videoId);
    }
    await _deleteParts(videoId);
    final status = await statusOf(videoId);
    await _write(videoId,
        state: status.playable ? VideoDownloadState.downloaded : VideoDownloadState.notDownloaded, bytes: 0, error: null);
    _changed();
  }

  /// Frees the space: the downloaded file and any partial file.
  Future<void> delete(String videoId) async {
    await cancel(videoId);
    final row = await (db.select(db.videoDownloads)..where((d) => d.videoId.equals(videoId))).getSingleOrNull();
    if (row?.localPath != null) await _deleteQuietly(File(row!.localPath!));
    await (db.delete(db.videoDownloads)..where((d) => d.videoId.equals(videoId))).go();
    _changed();
  }

  Future<void> deleteAll() async {
    for (final r in await db.select(db.videoDownloads).get()) {
      await delete(r.videoId);
    }
    final dir = await directory();
    if (await dir.exists()) {
      await for (final f in dir.list()) {
        if (f is File && (f.path.endsWith('.part') || f.path.endsWith('.mp4') || f.path.endsWith('.webm'))) await _deleteQuietly(f);
      }
    }
    _changed();
  }

  /// Space used by videos on this phone (finished and partial files).
  Future<int> totalBytesUsed() async {
    final dir = await directory();
    if (!await dir.exists()) return 0;
    var total = 0;
    final counted = <String>{};
    for (final r in await db.select(db.videoDownloads).get()) {
      if (r.localPath != null) {
        final f = File(r.localPath!);
        if (await f.exists()) {
          total += await f.length();
          counted.add(p.normalize(f.path));
        }
      }
    }
    await for (final f in dir.list()) {
      if (f is File && f.path.endsWith('.part') && !counted.contains(p.normalize(f.path))) total += await f.length();
    }
    return total;
  }

  Future<int> adoptLegacyDownloads() async {
    final n = await adoptLegacyVideoDownloads(db);
    if (n > 0) _changed();
    return n;
  }

  /// Completes when no download is queued or running (tests, and "Delete all").
  Future<void> whenIdle() {
    if (_queue.isEmpty && _active.isEmpty) return Future.value();
    final c = Completer<void>();
    _idle.add(c);
    return c.future;
  }

  Future<void> whenIdleFor(String videoId) async {
    while (_active.contains(videoId)) {
      await Future<void>.delayed(const Duration(milliseconds: 10));
    }
  }

  // ---- internals ----

  void _pump() {
    while (_active.length < kMaxParallelDownloads && _queue.isNotEmpty) {
      final id = _queue.removeAt(0);
      _active.add(id);
      unawaited(_run(id).whenComplete(() {
        _active.remove(id);
        _live.remove(id);
        _cancelTokens.remove(id);
        _changed();
        _pump();
        if (_queue.isEmpty && _active.isEmpty) {
          for (final c in List.of(_idle)) {
            if (!c.isCompleted) c.complete();
          }
          _idle.clear();
        }
      }));
    }
  }

  Future<File> _partFile(VideoEntry e) async => File(p.join((await directory()).path, '${e.videoId}.v${e.version}.part'));

  Future<File> _finalFile(VideoEntry e) async =>
      File(p.join((await directory()).path, '${e.videoId}.v${e.version}${e.mimeType == 'video/webm' ? '.webm' : '.mp4'}'));

  Future<void> _deleteParts(String videoId) async {
    final dir = await directory();
    if (!await dir.exists()) return;
    await for (final f in dir.list()) {
      if (f is File && p.basename(f.path).startsWith('$videoId.v') && f.path.endsWith('.part')) await _deleteQuietly(f);
    }
  }

  Future<void> _run(String videoId) async {
    for (var attempt = 1; attempt <= 2; attempt++) {
      final entry = await videoEntry(db, videoId);
      if (entry == null) {
        await _write(videoId, state: VideoDownloadState.notDownloaded);
        return;
      }
      try {
        await _fetchToPart(entry);
        final stop = _stopReason.remove(videoId);
        if (stop != null) {
          await _write(videoId, state: stop == VideoDownloadState.paused ? VideoDownloadState.paused : VideoDownloadState.notDownloaded);
          return;
        }
        if (await _verifyAndKeep(entry)) {
          unawaited(log?.call('DOWNLOAD_COMPLETED', videoId, {'bytes': entry.sizeBytes, 'version': entry.version}));
          return;
        }
        throw VideoFetchException(VideoDownloadError.corrupt, 'size or SHA-256 does not match the manifest');
      } on VideoFetchException catch (e) {
        if (e.kind == VideoDownloadError.network) {
          await _keepForResume(videoId, e.kind);
          return;
        }
        await _deleteQuietly(await _partFile(entry)); // never keep bytes that failed the check
        if (attempt < 2) continue; // one more try, from zero
        await _fail(videoId, e.kind);
        return;
      } on DioException catch (e) {
        final stop = _stopReason.remove(videoId);
        if (stop != null || CancelToken.isCancel(e)) {
          await _write(videoId, state: stop == VideoDownloadState.notDownloaded ? VideoDownloadState.notDownloaded : VideoDownloadState.paused);
          return;
        }
        await _keepForResume(videoId, VideoDownloadError.network);
        return;
      } on FileSystemException {
        await _fail(videoId, VideoDownloadError.storage);
        unawaited(log?.call('STORAGE_ERROR', videoId, {'stage': 'video_download'}));
        return;
      } on SocketException {
        await _keepForResume(videoId, VideoDownloadError.network);
        return;
      } on HttpException {
        await _keepForResume(videoId, VideoDownloadError.network);
        return;
      } on TimeoutException {
        await _keepForResume(videoId, VideoDownloadError.network);
        return;
      }
    }
  }

  /// Interrupted: the bytes stay, the row stays "downloading", and it resumes
  /// from the saved offset when the app opens again or the connection returns.
  Future<void> _keepForResume(String videoId, VideoDownloadError why) async {
    await _write(videoId, state: VideoDownloadState.downloading, bytes: _live[videoId], error: why);
  }

  Future<void> _fail(String videoId, VideoDownloadError why) async {
    await _write(videoId, state: VideoDownloadState.failed, bytes: 0, error: why);
    unawaited(log?.call('DOWNLOAD_FAILED', videoId, {'reason': why.name}));
  }

  Future<void> _fetchToPart(VideoEntry entry) async {
    final dir = await directory();
    if (!await dir.exists()) await dir.create(recursive: true);
    final part = await _partFile(entry);
    // Parts of an older version of this video are useless now.
    await for (final f in dir.list()) {
      if (f is File && p.basename(f.path).startsWith('${entry.videoId}.v') && f.path.endsWith('.part') && f.path != part.path) {
        await _deleteQuietly(f);
      }
    }
    var offset = await part.exists() ? await part.length() : 0;
    if (offset > entry.sizeBytes) {
      await part.delete();
      offset = 0;
    }
    _live[entry.videoId] = offset;
    if (offset == entry.sizeBytes) return; // all bytes are here; just verify

    final token = CancelToken();
    _cancelTokens[entry.videoId] = token;
    final resp = await fetcher.get(entry.url, from: offset, cancel: token);
    final type = (resp.contentType ?? '').toLowerCase();
    if (type.startsWith('text/') || type.contains('html') || type.contains('json')) {
      // e.g. CloudFront's 404 fallback page: never written as a video.
      await resp.body.drain<void>().catchError((_) {});
      throw VideoFetchException(VideoDownloadError.notFound, 'got $type instead of a video');
    }
    if (resp.statusCode == 404 || resp.statusCode == 403 || resp.statusCode == 410) {
      throw VideoFetchException(VideoDownloadError.notFound, 'HTTP ${resp.statusCode}');
    }
    if (resp.totalSize != null && resp.totalSize != entry.sizeBytes) {
      await resp.body.drain<void>().catchError((_) {});
      throw VideoFetchException(VideoDownloadError.corrupt, 'server has ${resp.totalSize} bytes, manifest says ${entry.sizeBytes}');
    }
    var mode = FileMode.append;
    if (offset > 0 && (resp.statusCode == 200 || resp.start != offset)) {
      offset = 0; // the server sent the whole file: start over
      mode = FileMode.write;
    } else if (offset == 0) {
      mode = FileMode.write;
    }
    final out = await part.open(mode: mode);
    var written = offset;
    var sinceSave = 0;
    var lastNotify = DateTime.now();
    try {
      await for (final chunk in resp.body) {
        if (_stopReason.containsKey(entry.videoId)) break;
        await out.writeFrom(chunk);
        written += chunk.length;
        sinceSave += chunk.length;
        _live[entry.videoId] = written;
        if (sinceSave >= 512 * 1024) {
          sinceSave = 0;
          await out.flush();
          await _write(entry.videoId, state: VideoDownloadState.downloading, bytes: written);
        }
        if (DateTime.now().difference(lastNotify) > const Duration(milliseconds: 250)) {
          lastNotify = DateTime.now();
          _changed();
        }
      }
    } catch (e) {
      await out.flush();
      await out.close();
      _live[entry.videoId] = await part.length();
      if (e is SocketException || e is HttpException || e is TimeoutException) {
        throw VideoFetchException(VideoDownloadError.network, e.toString());
      }
      rethrow;
    }
    await out.flush();
    await out.close();
    _live[entry.videoId] = await part.length();
    await _write(entry.videoId, state: VideoDownloadState.downloading, bytes: _live[entry.videoId]);
  }

  Future<bool> _verifyAndKeep(VideoEntry entry) async {
    final part = await _partFile(entry);
    if (!await part.exists() || await part.length() != entry.sizeBytes) return false;
    if (await fileSha256(part) != entry.contentHash) return false;
    final target = await _finalFile(entry);
    if (await target.exists()) await target.delete();
    await part.rename(target.path);
    final before = await (db.select(db.videoDownloads)..where((d) => d.videoId.equals(entry.videoId))).getSingleOrNull();
    await db.into(db.videoDownloads).insertOnConflictUpdate(VideoDownloadsCompanion.insert(
          videoId: entry.videoId,
          state: 'downloaded',
          bytesDownloaded: Value(entry.sizeBytes),
          totalBytes: Value(entry.sizeBytes),
          localPath: Value(target.path),
          contentHash: Value(entry.contentHash),
          version: Value(entry.version),
          error: const Value(null),
          updatedAt: DateTime.now(),
        ));
    // The previous version kept playing until now; it is no longer needed.
    if (before?.localPath != null && p.normalize(before!.localPath!) != p.normalize(target.path)) {
      await _deleteQuietly(File(before.localPath!));
    }
    return true;
  }

  /// Updates the row, keeping the verified file details (it may still be playing).
  Future<void> _write(String videoId, {required VideoDownloadState state, int? total, int? bytes, Object? error = _keep}) async {
    final existing = await (db.select(db.videoDownloads)..where((d) => d.videoId.equals(videoId))).getSingleOrNull();
    var name = _stateNames[state]!;
    // A verified older version still plays: "not downloaded" would hide it.
    if (existing?.localPath != null && existing?.contentHash != null && state == VideoDownloadState.notDownloaded) {
      name = 'downloaded';
    }
    await db.into(db.videoDownloads).insertOnConflictUpdate(VideoDownloadsCompanion.insert(
          videoId: videoId,
          state: name,
          bytesDownloaded: Value(bytes ?? existing?.bytesDownloaded ?? 0),
          totalBytes: Value(total ?? existing?.totalBytes ?? 0),
          localPath: Value(existing?.localPath),
          contentHash: Value(existing?.contentHash),
          version: Value(existing?.version ?? 0),
          error: Value(identical(error, _keep) ? existing?.error : (error as VideoDownloadError?)?.name),
          updatedAt: DateTime.now(),
        ));
    _changed();
  }

  static Future<void> _deleteQuietly(File f) async {
    try {
      if (await f.exists()) await f.delete();
    } catch (_) {}
  }
}

const Object _keep = Object();

// ---- the real fetcher, network check and disk check ----

/// GET with Range. CloudFront URLs go through a plain client (no API token);
/// a development server's /videos/{id}/file goes through the API client.
class DioVideoFetcher implements VideoFetcher {
  final ApiClient api;
  final Dio _plain = Dio(BaseOptions(connectTimeout: const Duration(seconds: 20), receiveTimeout: const Duration(seconds: 60)));

  DioVideoFetcher(this.api);

  @override
  Future<FetchResponse> get(String url, {int from = 0, CancelToken? cancel}) async {
    final dio = url.startsWith('http') ? _plain : api.dio;
    final r = await dio.get<ResponseBody>(
      url,
      cancelToken: cancel,
      options: Options(
        responseType: ResponseType.stream,
        headers: from > 0 ? {'Range': 'bytes=$from-'} : null,
        validateStatus: (s) => s != null && s < 500,
        receiveTimeout: const Duration(seconds: 60),
      ),
    );
    final status = r.statusCode ?? 0;
    var start = 0;
    int? total;
    final range = r.headers.value('content-range'); // bytes 100-199/200
    final m = range == null ? null : RegExp(r'bytes (\d+)-\d+/(\d+)').firstMatch(range);
    if (status == 206 && m != null) {
      start = int.parse(m.group(1)!);
      total = int.parse(m.group(2)!);
    } else if (status == 200) {
      total = int.tryParse(r.headers.value('content-length') ?? '');
    } else if (status == 416) {
      throw VideoFetchException(VideoDownloadError.corrupt, 'range not satisfiable');
    }
    return FetchResponse(
      statusCode: status,
      contentType: r.headers.value('content-type'),
      start: start,
      totalSize: total,
      body: r.data!.stream.map((b) => b),
    );
  }
}

class ConnectivityVideoNetwork implements VideoNetwork {
  final Connectivity _c = Connectivity();

  // When the phone cannot say, assume online (the download then simply tries) and not mobile data.
  @override
  Future<bool> isOnline() async {
    try {
      return (await _c.checkConnectivity()).any((r) => r != ConnectivityResult.none);
    } catch (_) {
      return true;
    }
  }

  @override
  Future<bool> isMobileData() async {
    try {
      final r = await _c.checkConnectivity();
      return r.contains(ConnectivityResult.mobile) && !r.contains(ConnectivityResult.wifi) && !r.contains(ConnectivityResult.ethernet);
    } catch (_) {
      return false;
    }
  }

  Stream<bool> get onlineChanges =>
      _c.onConnectivityChanged.map((r) => r.any((x) => x != ConnectivityResult.none)).handleError((_) {});
}

/// Free space from Android (MainActivity "freeBytes"); null when unknown.
class ChannelDiskSpace implements VideoDiskSpace {
  static const _channel = MethodChannel('org.malariaconsortium.sarmaan/device');
  @override
  Future<int?> freeBytes() async {
    try {
      return await _channel.invokeMethod<int>('freeBytes');
    } catch (_) {
      return null;
    }
  }
}

Future<Directory> defaultVideoDirectory() async {
  final docs = await getApplicationDocumentsDirectory();
  return Directory(p.join(docs.path, 'videos')); // the folder app 0.1.19 and older used
}

typedef VideoOpener = Future<VideoPlayerController?> Function(String path);

final videoNetworkProvider = Provider<VideoNetwork>((ref) => ConnectivityVideoNetwork());
final videoDiskSpaceProvider = Provider<VideoDiskSpace>((ref) => ChannelDiskSpace());
final videoFetcherProvider = Provider<VideoFetcher>((ref) => DioVideoFetcher(ref.read(apiClientProvider)));

final videoOpenerProvider = Provider<VideoOpener>((ref) => (path) async {
      final c = VideoPlayerController.file(File(path));
      await c.initialize();
      return c;
    });

final videoDownloadManagerProvider = ChangeNotifierProvider<VideoDownloadManager>((ref) {
  final db = ref.read(localDatabaseProvider);
  final network = ref.read(videoNetworkProvider);
  final manager = VideoDownloadManager(
    db: db,
    directory: defaultVideoDirectory,
    fetcher: ref.read(videoFetcherProvider),
    network: network,
    disk: ref.read(videoDiskSpaceProvider),
    log: (type, videoId, payload) => recordAnalyticsEvent(db, type, videoId: videoId, payload: payload),
  );
  unawaited(manager.init().catchError((_) {}));
  return manager;
});

/// Resumes interrupted downloads when the connection returns. Started once from
/// main() (not from screens, so widget tests need no connectivity plugin).
void resumeVideoDownloadsOnReconnect(ProviderContainer container) {
  final network = container.read(videoNetworkProvider);
  if (network is! ConnectivityVideoNetwork) return;
  network.onlineChanges.where((online) => online).listen(
        (_) => container.read(videoDownloadManagerProvider).resumeInterrupted().catchError((_) {}),
        onError: (_) {},
      );
}

/// One video's status, refreshed whenever the manager reports a change.
final videoStatusProvider = FutureProvider.autoDispose.family<VideoDownloadStatus, String>((ref, videoId) {
  final manager = ref.watch(videoDownloadManagerProvider);
  return manager.statusOf(videoId);
});

/// The phone's copy of one manifest entry (null: not in the manifest).
final videoEntryProvider = FutureProvider.autoDispose.family<VideoEntry?, String>((ref, videoId) {
  ref.watch(videoDownloadManagerProvider);
  return videoEntry(ref.read(localDatabaseProvider), videoId);
});

final videoEntriesProvider = FutureProvider.autoDispose<List<VideoEntry>>((ref) {
  ref.watch(videoDownloadManagerProvider);
  return allVideoEntries(ref.read(localDatabaseProvider));
});
