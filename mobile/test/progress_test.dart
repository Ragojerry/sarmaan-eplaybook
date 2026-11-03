import 'package:drift/drift.dart' show Value;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarmaan_eplaybook/db/local_database.dart';

void main() {
  late LocalDatabase db;

  setUp(() {
    db = LocalDatabase.forTesting(NativeDatabase.memory());
    db.setActiveUser('user-1');
  });
  tearDown(() => db.close());

  test('each module keeps its own progress', () async {
    await db.upsertProgress(moduleId: 'm1', progressPercent: 62, lastSection: 'Dosing');
    await db.upsertProgress(moduleId: 'm2', progressPercent: 30, lastSection: 'Eligibility');
    await db.upsertProgress(moduleId: 'm1', progressPercent: 100, completed: true);
    await db.upsertProgress(moduleId: 'm3', progressPercent: 10);

    final all = {for (final p in await db.getAllProgress()) p.moduleId: p};
    expect(all.length, 3);
    expect(all['m1']!.completed, isTrue);
    expect(all['m2']!.progressPercent, 30);
    expect(all['m2']!.lastSection, 'Eligibility');
    expect(all['m3']!.progressPercent, 10);
  });

  test('saves racing for a new module leave a single row', () async {
    await Future.wait([
      db.upsertProgress(moduleId: 'm1'),
      db.upsertProgress(moduleId: 'm1', progressPercent: 20),
      db.upsertProgress(moduleId: 'm1', progressPercent: 40),
    ]);
    final rows = await db.getAllProgress();
    expect(rows.length, 1);
    expect(rows.single.progressPercent, 40);
  });

  test('a duplicate row left by an older build still reads and updates', () async {
    for (final pct in [15, 45]) {
      await db.into(db.localProgress).insert(LocalProgressCompanion.insert(
            moduleId: 'm1',
            progressPercent: Value(pct),
            userId: const Value('user-1'),
          ));
    }
    expect((await db.getProgressForModule('m1'))!.progressPercent, 45);
    await db.upsertProgress(moduleId: 'm1', progressPercent: 70);
    expect((await db.getProgressForModule('m1'))!.progressPercent, 70);
  });

  test('another account on the same phone starts fresh', () async {
    await db.upsertProgress(moduleId: 'm1', progressPercent: 50);
    db.setActiveUser('user-2');
    expect(await db.getAllProgress(), isEmpty);
  });
}
