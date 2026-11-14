import 'dart:io';

import 'package:drift/drift.dart' show Value;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarmaan_eplaybook/db/local_database.dart';

/// Database v12 -> v13 on an existing install: training progress is untouched,
/// and a video the old app downloaded is remembered (its file kept) until the
/// next manifest verifies it.
void main() {
  test('upgrading from v12 keeps progress and records videos already on the phone', () async {
    final dir = await Directory.systemTemp.createTemp('v12');
    addTearDown(() => dir.delete(recursive: true));
    final file = File('${dir.path}/app.sqlite');
    final legacy = File('${dir.path}/v1.mp4')..writeAsBytesSync(List<int>.filled(1000, 7));

    // Make a v12 database: today's schema minus what v13 adds, with data in it.
    var db = LocalDatabase.forTesting(NativeDatabase(file));
    db.setActiveUser('u1', learnerRole: 'CDD');
    await db.into(db.localProgress).insert(LocalProgressCompanion.insert(
          moduleId: 'A', progressPercent: const Value(100), completed: const Value(true), userId: const Value('u1'),
          secondsSpent: const Value(240), synced: const Value(true)));
    await db.customStatement('DROP TABLE video_downloads');
    for (final col in ['size_bytes', 'content_hash', 'url', 'version', 'required_for_completion', 'mime_type', 'manifest_seen']) {
      await db.customStatement('ALTER TABLE cached_videos DROP COLUMN $col');
    }
    await db.customStatement(
        "INSERT INTO cached_videos (id, title, language, offline_available, status, has_file, local_path) "
        "VALUES ('v1', 'Old', 'en', 1, 'PUBLISHED', 1, ?)", [legacy.path]);
    await db.customStatement('PRAGMA user_version = 12');
    await db.close();

    db = LocalDatabase.forTesting(NativeDatabase(file)); // the new app opens it
    addTearDown(db.close);
    db.setActiveUser('u1', learnerRole: 'CDD');
    final progress = (await db.getProgressForModule('A'))!;
    expect((progress.completed, progress.secondsSpent, progress.progressPercent), (true, 240, 100));
    final rows = await db.select(db.videoDownloads).get();
    expect(rows.single.videoId, 'v1');
    expect(rows.single.localPath, legacy.path);
    expect(rows.single.state, isNot('downloaded'), reason: 'verified against the manifest first');
    expect(await legacy.exists(), isTrue);
    expect((await db.customSelect('PRAGMA user_version').getSingle()).read<int>('user_version'), 13);
  });
}
