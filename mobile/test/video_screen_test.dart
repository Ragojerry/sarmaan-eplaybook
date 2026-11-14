import 'dart:async';
import 'dart:io';
import 'dart:typed_data';

import 'package:crypto/crypto.dart';
import 'package:dio/dio.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:sarmaan_eplaybook/db/local_database.dart';
import 'package:sarmaan_eplaybook/offline/content_sync_service.dart' show localDatabaseProvider;
import 'package:sarmaan_eplaybook/screens/video_screen.dart';
import 'package:sarmaan_eplaybook/video/video_downloads.dart';
import 'package:sarmaan_eplaybook/video/video_manifest.dart';

/// The video screen works from the phone's own copy of the video manifest, so it
/// opens offline; it downloads only when the learner taps.

final _bytes = Uint8List.fromList(List<int>.generate(64 * 1024, (i) => i % 251));

class _Net implements VideoNetwork {
  final bool online, mobile;
  _Net({this.online = true, this.mobile = false});
  @override
  Future<bool> isOnline() async => online;
  @override
  Future<bool> isMobileData() async => mobile;
}

class _Disk implements VideoDiskSpace {
  final int? free;
  _Disk([this.free]);
  @override
  Future<int?> freeBytes() async => free;
}

class _Fetcher implements VideoFetcher {
  int calls = 0;
  @override
  Future<FetchResponse> get(String url, {int from = 0, CancelToken? cancel}) async {
    calls++;
    return FetchResponse(statusCode: 200, contentType: 'video/mp4', start: 0, totalSize: _bytes.length, body: Stream.value(_bytes));
  }
}

void main() {
  late Directory dir;
  late LocalDatabase db;
  late _Fetcher fetcher;
  final opened = <String>[];

  setUp(() async {
    dir = await Directory.systemTemp.createTemp('video_screen');
    db = LocalDatabase.forTesting(NativeDatabase.memory());
    fetcher = _Fetcher();
    opened.clear();
  });
  tearDown(() async {
    await db.close();
    await dir.delete(recursive: true);
  });

  Future<void> manifest({int? size}) => storeVideoManifest(db, [
        VideoEntry.fromJson({'video_id': 'v1', 'module_id': null, 'title': 'Hand washing', 'language': 'en',
          'size_bytes': size ?? _bytes.length, 'duration_seconds': 30, 'content_hash': sha256.convert(_bytes).toString(),
          'url': 'https://cdn.example.test/videos/v1/a.mp4', 'version': 1, 'required_for_completion': false,
          'mime_type': 'video/mp4'}),
      ]);

  Future<VideoDownloadManager> pump(WidgetTester tester, {required VideoNetwork net, VideoDiskSpace? disk, bool downloaded = false}) async {
    final manager = VideoDownloadManager(db: db, directory: () async => dir, fetcher: fetcher, network: net, disk: disk ?? _Disk());
    if (downloaded) {
      await tester.runAsync(() async {
        final online = VideoDownloadManager(db: db, directory: () async => dir, fetcher: fetcher, network: _Net(), disk: _Disk());
        await online.start('v1');
        await online.whenIdle();
      });
    }
    final router = GoRouter(initialLocation: '/videos/v1', routes: [
      GoRoute(path: '/videos', builder: (_, __) => const Scaffold(body: Text('LIST'))),
      GoRoute(path: '/videos/:id', builder: (_, s) => VideoScreen(videoId: s.pathParameters['id']!)),
    ]);
    await tester.pumpWidget(ProviderScope(
      overrides: [
        localDatabaseProvider.overrideWithValue(db),
        videoDownloadManagerProvider.overrideWith((ref) => manager),
        videoNetworkProvider.overrideWithValue(net),
        videoOpenerProvider.overrideWithValue((path) async {
          opened.add(path);
          return null;
        }),
      ],
      child: MaterialApp.router(routerConfig: router),
    ));
    for (var i = 0; i < 6; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 20)));
      await tester.pump();
    }
    return manager;
  }

  Future<void> settle(WidgetTester tester) async {
    for (var i = 0; i < 8; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 20)));
      await tester.pump();
    }
  }

  testWidgets('offline with an undownloaded video: the connect message, nothing downloads', (tester) async {
    await tester.runAsync(() => manifest());
    await pump(tester, net: _Net(online: false));
    expect(find.text('Hand washing'), findsOneWidget, reason: 'the screen opens offline');
    expect(find.text('Connect to the internet to watch this video.'), findsOneWidget);
    expect(fetcher.calls, 0);
  });

  testWidgets('offline with a downloaded video: Play and Offline ready; it plays the local file', (tester) async {
    await tester.runAsync(() => manifest());
    await pump(tester, net: _Net(online: false), downloaded: true);
    expect(find.text('Offline ready'), findsOneWidget);
    expect(find.text('Connect to the internet to watch this video.'), findsNothing);
    await tester.tap(find.text('Play'));
    await settle(tester);
    expect(opened.single, startsWith(dir.path));
    expect(opened.single, isNot(endsWith('.part')));
  });

  testWidgets('not downloaded: Download to watch with the size; tapping downloads once and plays', (tester) async {
    await tester.runAsync(() => manifest());
    final manager = await pump(tester, net: _Net());
    expect(find.text('Download to watch'), findsOneWidget);
    expect(find.text(formatBytes(_bytes.length)), findsOneWidget);
    // Real time: file writes started inside the test's fake clock would never finish.
    await tester.runAsync(() async {
      await tester.tap(find.text('Download to watch'));
      for (var i = 0; i < 100 && fetcher.calls == 0; i++) {
        await Future<void>.delayed(const Duration(milliseconds: 10));
      }
      await manager.whenIdle();
    });
    await settle(tester);
    expect(fetcher.calls, 1);
    expect(find.text('Offline ready'), findsOneWidget);
    expect(opened, hasLength(1), reason: 'plays as soon as the download is verified');
  });

  testWidgets('mobile data above the threshold asks first; Cancel downloads nothing', (tester) async {
    await tester.runAsync(() => manifest(size: kMobileDataWarnBytes + 1));
    await pump(tester, net: _Net(mobile: true));
    await tester.tap(find.text('Download to watch'));
    await settle(tester);
    expect(find.textContaining('will use your mobile data'), findsOneWidget);
    expect(find.textContaining('Wi-Fi'), findsOneWidget);
    await tester.tap(find.text('Cancel'));
    await settle(tester);
    expect(fetcher.calls, 0);
  });

  testWidgets('not enough free space: a clear message and no download', (tester) async {
    await tester.runAsync(() => manifest());
    await pump(tester, net: _Net(), disk: _Disk(10));
    await tester.tap(find.text('Download to watch'));
    await settle(tester);
    expect(find.textContaining('Not enough free space'), findsOneWidget);
    expect(fetcher.calls, 0);
  });

  test('sizes read like "12 MB"', () {
    expect(formatBytes(12 * 1024 * 1024), '12 MB');
    expect(formatBytes(1536 * 1024), '1.5 MB');
    expect(formatBytes(800 * 1024), '800 KB');
  });
}
