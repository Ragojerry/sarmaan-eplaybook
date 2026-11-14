import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:crypto/crypto.dart';
import 'package:dio/dio.dart';
import 'package:drift/drift.dart' show Value;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarmaan_eplaybook/db/local_database.dart';
import 'package:sarmaan_eplaybook/video/video_downloads.dart';
import 'package:sarmaan_eplaybook/video/video_manifest.dart';

import 'support/fake_server.dart';

/// Videos download only when the learner asks: resumable (.part + Range),
/// verified (SHA-256) before they count, never duplicated, never blocking training.

final _bytes = Uint8List.fromList(List<int>.generate(200 * 1024, (i) => (i * 31 + 7) % 256)); // 200 KB "video"
String _sha(List<int> b) => sha256.convert(b).toString();

Map<String, dynamic> _entry({String id = 'v1', int version = 1, List<int>? data, int? size, String? moduleId = 'm1'}) => {
      'video_id': id,
      'module_id': moduleId,
      'title': 'Video $id',
      'language': 'en',
      'size_bytes': size ?? (data ?? _bytes).length,
      'duration_seconds': 60,
      'content_hash': _sha(data ?? _bytes),
      'url': 'https://cdn.example.test/videos/$id/v$version.mp4',
      'version': version,
      'required_for_completion': false,
      'mime_type': 'video/mp4',
    };

/// Serves [data] for any URL, honouring Range; can fail part-way or send other bytes.
class FakeFetcher implements VideoFetcher {
  List<int> data;
  String contentType;
  double? dropAt; // fraction after which the connection "drops"
  final calls = <({String url, int from})>[];
  Completer<void>? gate; // holds the response open until completed

  FakeFetcher(this.data, {this.contentType = 'video/mp4'});

  @override
  Future<FetchResponse> get(String url, {int from = 0, CancelToken? cancel}) async {
    calls.add((url: url, from: from));
    if (gate != null) await gate!.future;
    final end = dropAt == null ? data.length : (data.length * dropAt!).round();
    Stream<List<int>> body() async* {
      const chunk = 16 * 1024;
      for (var i = from; i < end; i += chunk) {
        yield data.sublist(i, i + chunk > end ? end : i + chunk);
      }
      if (end < data.length) throw const SocketException('connection dropped');
    }

    return FetchResponse(
      statusCode: from > 0 ? 206 : 200,
      contentType: contentType,
      start: from,
      totalSize: data.length,
      body: body(),
    );
  }
}

class FakeNetwork implements VideoNetwork {
  bool online;
  bool mobile;
  FakeNetwork({this.online = true, this.mobile = false});
  @override
  Future<bool> isOnline() async => online;
  @override
  Future<bool> isMobileData() async => mobile;
}

class FakeDisk implements VideoDiskSpace {
  int? free;
  FakeDisk([this.free]);
  @override
  Future<int?> freeBytes() async => free;
}

late Directory _dir;

VideoDownloadManager _manager(LocalDatabase db, FakeFetcher fetcher, {FakeNetwork? network, FakeDisk? disk, List<String>? log}) =>
    VideoDownloadManager(
      db: db,
      directory: () async => _dir,
      fetcher: fetcher,
      network: network ?? FakeNetwork(),
      disk: disk ?? FakeDisk(),
      log: (type, videoId, payload) async => log?.add(type),
    );

Future<void> _manifest(LocalDatabase db, List<Map<String, dynamic>> entries) =>
    storeVideoManifest(db, [for (final e in entries) VideoEntry.fromJson(e)]);

void main() {
  setUp(() async => _dir = await Directory.systemTemp.createTemp('videos_test'));
  tearDown(() async {
    if (await _dir.exists()) await _dir.delete(recursive: true);
  });

  test('tapping Download starts exactly one download; a second tap does not duplicate it', () async {
    final db = LocalDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    await _manifest(db, [_entry()]);
    final fetcher = FakeFetcher(_bytes)..gate = Completer<void>();
    final m = _manager(db, fetcher);
    expect(await m.start('v1'), StartResult.started);
    expect(await m.start('v1'), StartResult.alreadyQueued);
    fetcher.gate!.complete();
    await m.whenIdle();
    expect(await m.start('v1'), StartResult.alreadyDownloaded);
    expect(fetcher.calls, hasLength(1));
    final s = await m.statusOf('v1');
    expect(s.state, VideoDownloadState.downloaded);
    expect(await File(s.localPath!).readAsBytes(), _bytes);
    expect(s.localPath, isNot(endsWith('.part')));
  });

  test('interrupted at 40% and the app killed: reopening resumes from the saved offset, not zero', () async {
    final file = File('${_dir.path}/db.sqlite');
    var db = LocalDatabase.forTesting(NativeDatabase(file));
    await _manifest(db, [_entry()]);
    final first = FakeFetcher(_bytes)..dropAt = 0.4;
    final log = <String>[];
    final m1 = _manager(db, first, log: log);
    await m1.start('v1');
    await m1.whenIdle();
    var s = await VideoDownloadManager.readStatus(db, 'v1');
    expect(s.state, isNot(VideoDownloadState.downloaded));
    expect(s.bytesDownloaded, closeTo(_bytes.length * 0.4, 1));
    expect(s.bytesDownloaded, greaterThan(0));
    final saved = s.bytesDownloaded;
    await db.close(); // the app is killed

    db = LocalDatabase.forTesting(NativeDatabase(file)); // and opened again
    addTearDown(db.close);
    final second = FakeFetcher(_bytes);
    final m = _manager(db, second);
    await m.init(); // resumes interrupted downloads
    await m.whenIdle();
    expect(second.calls.single.from, saved);
    s = await m.statusOf('v1');
    expect(s.state, VideoDownloadState.downloaded);
    expect(_sha(await File(s.localPath!).readAsBytes()), _sha(_bytes));
    expect(log, contains('DOWNLOAD_STARTED'));
  });

  test('a corrupt file deletes the part file, retries once, then shows Retry; never marked downloaded', () async {
    final db = LocalDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    await _manifest(db, [_entry()]);
    final wrong = Uint8List.fromList(List<int>.filled(_bytes.length, 1)); // right size, wrong bytes
    final fetcher = FakeFetcher(wrong);
    final log = <String>[];
    final m = _manager(db, fetcher, log: log);
    await m.start('v1');
    await m.whenIdle();
    expect(fetcher.calls, hasLength(2), reason: 'one retry');
    expect(fetcher.calls.last.from, 0, reason: 'the retry starts again from zero');
    final s = await m.statusOf('v1');
    expect(s.state, VideoDownloadState.failed);
    expect(s.error, VideoDownloadError.corrupt);
    expect(s.localPath, isNull);
    expect(_dir.listSync().whereType<File>().where((f) => f.path.contains('v1')), isEmpty, reason: 'no .part or final file left');
    expect(log, contains('DOWNLOAD_FAILED'));
    expect(log, isNot(contains('DOWNLOAD_COMPLETED')));
  });

  test('a web page instead of a video (CloudFront 404 fallback) is never saved', () async {
    final db = LocalDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    await _manifest(db, [_entry()]);
    final fetcher = FakeFetcher(List<int>.filled(_bytes.length, 60), contentType: 'text/html');
    final m = _manager(db, fetcher);
    await m.start('v1');
    await m.whenIdle();
    expect((await m.statusOf('v1')).state, VideoDownloadState.failed);
    expect(_dir.listSync().whereType<File>().where((f) => f.path.contains('v1')), isEmpty);
  });

  test('offline: an undownloaded video does not start', () async {
    final db = LocalDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    await _manifest(db, [_entry()]);
    final fetcher = FakeFetcher(_bytes);
    final m = _manager(db, fetcher, network: FakeNetwork(online: false));
    expect(await m.start('v1'), StartResult.offline);
    expect(fetcher.calls, isEmpty);
  });

  test('the mobile-data warning appears above the threshold and not below it', () async {
    final db = LocalDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    const big = kMobileDataWarnBytes + 1;
    await _manifest(db, [_entry(id: 'big', size: big), _entry(id: 'small', size: kMobileDataWarnBytes - 1)]);
    final fetcher = FakeFetcher(_bytes)..gate = Completer<void>();
    final m = _manager(db, fetcher, network: FakeNetwork(mobile: true));
    expect(await m.start('big'), StartResult.needsMobileDataConfirm);
    expect(fetcher.calls, isEmpty);
    expect(await m.start('small'), StartResult.started);
    expect(await m.start('big', confirmedMobileData: true), StartResult.started);
    fetcher.gate!.complete();
    await m.whenIdle();
    await _manifest(db, [_entry(id: 'wifi', size: kMobileDataWarnBytes + 1)]);
    final wifi = _manager(db, FakeFetcher(_bytes), network: FakeNetwork());
    expect(await wifi.start('wifi'), isNot(StartResult.needsMobileDataConfirm));
    await wifi.whenIdle();
    expect(kMobileDataWarnBytes, 10 * 1024 * 1024);
  });

  test('not enough free space blocks the download with a clear result', () async {
    final db = LocalDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    await _manifest(db, [_entry()]);
    final fetcher = FakeFetcher(_bytes);
    final m = _manager(db, fetcher, disk: FakeDisk(_bytes.length ~/ 2));
    expect(await m.start('v1'), StartResult.notEnoughSpace);
    expect(fetcher.calls, isEmpty);
  });

  test('a newer manifest version shows Update available and keeps the old file until the new one is fetched', () async {
    final db = LocalDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    await _manifest(db, [_entry()]);
    final m = _manager(db, FakeFetcher(_bytes));
    await m.start('v1');
    await m.whenIdle();
    final old = (await m.statusOf('v1')).localPath!;

    final newer = Uint8List.fromList([..._bytes, 1, 2, 3]);
    await _manifest(db, [_entry(version: 2, data: newer)]);
    final s = await m.statusOf('v1');
    expect(s.state, VideoDownloadState.downloaded);
    expect(s.updateAvailable, isTrue);
    expect(s.localPath, old);
    expect(await File(old).exists(), isTrue, reason: 'still plays the old file');

    final m2 = _manager(db, FakeFetcher(newer));
    expect(await m2.start('v1'), StartResult.started); // only when the learner taps
    await m2.whenIdle();
    final after = await m2.statusOf('v1');
    expect(after.updateAvailable, isFalse);
    expect(after.version, 2);
    expect(await File(after.localPath!).readAsBytes(), newer);
  });

  test('videos downloaded by the old app are recognised after the upgrade, without downloading again', () async {
    final db = LocalDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final legacy = File('${_dir.path}/v1.mp4')..writeAsBytesSync(_bytes);
    await db.into(db.cachedVideos).insert(CachedVideosCompanion.insert(
          id: 'v1', title: 'Old', language: 'en', offlineAvailable: true, status: 'PUBLISHED', hasFile: true,
          localPath: Value(legacy.path)));
    await db.recordLegacyVideoDownloads(); // what the v13 migration does
    await _manifest(db, [_entry()]);
    final fetcher = FakeFetcher(_bytes);
    final m = _manager(db, fetcher);
    expect(await m.adoptLegacyDownloads(), 1);
    final s = await m.statusOf('v1');
    expect(s.state, VideoDownloadState.downloaded);
    expect(s.localPath, legacy.path);
    expect(fetcher.calls, isEmpty);
  });

  test('a training restart does not delete downloaded videos', () async {
    final db = LocalDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    db.setActiveUser('u1', learnerRole: 'CDD');
    await _manifest(db, [_entry()]);
    final m = _manager(db, FakeFetcher(_bytes));
    await m.start('v1');
    await m.whenIdle();
    final path = (await m.statusOf('v1')).localPath!;
    await db.restartTraining(enqueue: false);
    expect(await File(path).exists(), isTrue);
    expect((await m.statusOf('v1')).state, VideoDownloadState.downloaded);
  });

  test('delete frees the space: the file and its record go', () async {
    final db = LocalDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    await _manifest(db, [_entry()]);
    final m = _manager(db, FakeFetcher(_bytes));
    await m.start('v1');
    await m.whenIdle();
    expect(await m.totalBytesUsed(), _bytes.length);
    await m.delete('v1');
    expect((await m.statusOf('v1')).state, VideoDownloadState.notDownloaded);
    expect(await m.totalBytesUsed(), 0);
    expect(_dir.listSync().whereType<File>().where((f) => f.path.contains('v1')), isEmpty);
  });

  test('downloading all videos of a module queues them one at a time', () async {
    final db = LocalDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    await _manifest(db, [_entry(id: 'a'), _entry(id: 'b'), _entry(id: 'c', moduleId: 'other')]);
    var active = 0, maxActive = 0;
    final fetcher = _CountingFetcher(_bytes, onStart: () => maxActive = (++active > maxActive) ? active : maxActive, onEnd: () => active--);
    final m = VideoDownloadManager(db: db, directory: () async => _dir, fetcher: fetcher, network: FakeNetwork(), disk: FakeDisk());
    final ids = await videosOfModule(db, 'm1');
    expect(ids.map((e) => e.videoId), unorderedEquals(['a', 'b']));
    await m.startAll(ids.map((e) => e.videoId));
    await m.whenIdle();
    expect(maxActive, lessThanOrEqualTo(kMaxParallelDownloads));
    expect((await m.statusOf('a')).state, VideoDownloadState.downloaded);
    expect((await m.statusOf('b')).state, VideoDownloadState.downloaded);
    expect((await m.statusOf('c')).state, VideoDownloadState.notDownloaded);
  });

  test('the content sync step fetches the manifest only and downloads no video', () async {
    final db = LocalDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final server = _RecordingServer({'videos': [_entry(), _entry(id: 'v2')]});
    final api = fakeApi(FakeServer())..dio.httpClientAdapter = server;
    await refreshVideoManifest(api, db);
    expect(server.paths, ['/sync/videos']);
    expect((await allVideoEntries(db)).map((e) => e.videoId), unorderedEquals(['v1', 'v2']));
    expect(_dir.listSync().whereType<File>(), isEmpty);
    // And the sync engine never starts a download.
    final engine = File('lib/sync/sync_engine.dart').readAsStringSync();
    expect(engine.contains('VideoDownloadManager'), isFalse);
    expect(engine.contains('downloadVideo'), isFalse);
  });
}

class _CountingFetcher extends FakeFetcher {
  final void Function() onStart, onEnd;
  _CountingFetcher(super.data, {required this.onStart, required this.onEnd});
  @override
  Future<FetchResponse> get(String url, {int from = 0, CancelToken? cancel}) async {
    onStart();
    await Future<void>.delayed(const Duration(milliseconds: 5));
    final r = await super.get(url, from: from, cancel: cancel);
    return FetchResponse(
      statusCode: r.statusCode, contentType: r.contentType, start: r.start, totalSize: r.totalSize,
      body: r.body.transform(StreamTransformer.fromHandlers(handleDone: (sink) {
        onEnd();
        sink.close();
      })),
    );
  }
}

class _RecordingServer implements HttpClientAdapter {
  final Map<String, dynamic> manifest;
  final paths = <String>[];
  _RecordingServer(this.manifest);
  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    paths.add(options.path);
    if (options.path == '/sync/videos') {
      return ResponseBody.fromString(jsonEncode(manifest), 200, headers: {
        Headers.contentTypeHeader: ['application/json'],
      });
    }
    return ResponseBody.fromString('unexpected', 500);
  }

  @override
  void close({bool force = false}) {}
}
