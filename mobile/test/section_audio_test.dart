import 'dart:io';

import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarmaan_eplaybook/db/local_database.dart';
import 'package:sarmaan_eplaybook/sync/release_installer.dart';

import 'support/fake_server.dart';

/// Section audio uploaded in the admin travels in the release package like a
/// picture: the installer saves it straight to a file (never whole in memory),
/// checks its SHA-256 and keeps it for offline playback.
void main() {
  late Directory docs;
  late FakeServer server;
  late LocalDatabase db;
  late ReleaseInstaller installer;

  setUp(() async {
    docs = await tempDocs();
    server = FakeServer();
    db = LocalDatabase.forTesting(NativeDatabase.memory());
    db.setActiveUser('learner-1', learnerRole: 'CDD');
    installer = ReleaseInstaller(fakeApi(server), db);
  });

  tearDown(() async {
    await db.close();
    if (await docs.exists()) await docs.delete(recursive: true);
  });

  Map<String, dynamic> withAudio(String audioId) {
    final m = module('a1', 'HFW-01', 1010);
    (m['sections'] as List).add({
      'id': 's-audio', 'section_number': 2, 'title': 'Listen', 'content_type': 'AUDIO', 'sort_order': 2,
      'content': {'media_asset_id': audioId, 'filename': 'lesson.mp3', 'mime_type': 'audio/mpeg'},
    });
    return m;
  }

  test('section audio is downloaded to a file for offline use', () async {
    final audio = List<int>.generate(200000, (i) => i % 251); // larger than one network chunk
    server.files['/media/aud-1/file'] = audio;
    await installer.install(publish(server, 'R-AUDIO', [withAudio('aud-1')]));

    final row = await db.getMedia('aud-1');
    expect(row, isNotNull);
    expect(row!.assetType, 'AUDIO');
    expect(row.mimeType, 'audio/mpeg');
    expect(await File(row.localPath!).readAsBytes(), audio);
    expect(Directory(p(row.localPath!)).listSync().where((f) => f.path.endsWith('.part')), isEmpty);
  });

  test('a corrupted audio download is rejected and leaves no partial file', () async {
    server.files['/media/aud-2/file'] = List<int>.filled(5000, 7);
    final info = publish(server, 'R-BAD', [withAudio('aud-2')]);
    server.files['/media/aud-2/file'] = List<int>.filled(5000, 8); // bytes change after the package was built

    await expectLater(installer.install(info), throwsA(isA<InstallException>()));
    expect(await db.getMedia('aud-2'), isNull);
    final mediaDir = Directory('${docs.path}${Platform.pathSeparator}media');
    if (await mediaDir.exists()) {
      expect(mediaDir.listSync().where((f) => f.path.endsWith('.part')), isEmpty);
    }
  });
}

String p(String file) => File(file).parent.path;
