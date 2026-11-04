import 'dart:convert';
import 'dart:io';

import 'package:drift/drift.dart' show Value;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarmaan_eplaybook/db/local_database.dart';
import 'package:sarmaan_eplaybook/learning/learning_rules.dart';
import 'package:sarmaan_eplaybook/learning/learning_service.dart';

/// Pre-test -> reading -> post-test on the phone, and role-based visibility of
/// the local cache. The pass rule itself is checked against the vectors the
/// backend generates (test/learning_vectors.json), so both sides agree.
void main() {
  group('pass rule (shared vectors)', () {
    final vectors = jsonDecode(File('test/learning_vectors.json').readAsStringSync()) as Map<String, dynamic>;
    test('pass mark is 90', () => expect(vectors['pass_mark'], 90));
    for (final c in (vectors['cases'] as List).cast<Map<String, dynamic>>()) {
      test(c['why'] as String, () {
        expect(
          postTestCompletes(c['post_correct'] as int, c['post_total'] as int, c['pre_correct'] as int, c['pre_total'] as int,
              exceptionApproved: c['exception_approved'] as bool),
          c['completes'],
        );
      });
    }
  });

  group('state machine', () {
    TestScore t(String type, int correct, int total, int minute) => TestScore(
          clientId: '$type$minute',
          testType: type,
          correct: correct,
          total: total,
          takenAt: DateTime(2026, 11, 4, 9, minute),
        );

    test('question usage: a test with no questions of its own uses all of them', () {
      expect(testQuestionCounts(['BOTH', 'BOTH', 'PRE']), (3, 2));
      expect(testQuestionCounts(['POST', 'POST']), (2, 2));
      expect(testQuestionCounts([]), (0, 0));
    });

    test('pre-test first, reading, then post-test; completing unlocks the next module', () {
      List<ModuleLearning> run(List<TestScore> a, {bool read = false, bool done = false}) => computeLearning([
            ModuleInput(moduleId: 'A', questionUsages: const ['BOTH'], attempts: a, readingDone: read, completed: done),
            const ModuleInput(moduleId: 'B', questionUsages: ['BOTH']),
          ]);
      var s = run([]);
      expect(s[0].stage, ModuleStage.preTest);
      expect(s[0].canRead, isFalse);
      expect(s[0].canTakePostTest, isFalse);
      expect(s[1].stage, ModuleStage.locked);

      s = run([t('PRE', 5, 10, 1)]);
      expect(s[0].stage, ModuleStage.reading);
      expect(s[0].canRead, isTrue);
      expect(s[0].canTakePreTest, isFalse, reason: 'the pre-test is taken once');
      expect(s[0].canTakePostTest, isFalse, reason: 'not before reading');

      s = run([t('PRE', 5, 10, 1)], read: true);
      expect(s[0].stage, ModuleStage.postTest);
      expect(s[0].canTakePostTest, isTrue);
      expect(s[0].completingPost, isNull);

      s = run([t('PRE', 5, 10, 1), t('POST', 9, 10, 3)], read: true);
      expect(s[0].completingPost?.clientId, 'POST3');

      s = run([t('PRE', 5, 10, 1), t('POST', 9, 10, 3)], read: true, done: true);
      expect(s[0].stage, ModuleStage.completed);
      expect(s[1].stage, ModuleStage.preTest, reason: 'the next module unlocks');
    });

    test('a 100% pre-test waits for an approved exception', () {
      ModuleLearning run(bool approved, List<TestScore> a) => computeLearning([
            ModuleInput(moduleId: 'A', questionUsages: const ['BOTH'], attempts: a, readingDone: true, exceptionApproved: approved),
          ]).single;
      final waiting = run(false, [t('PRE', 10, 10, 1), t('POST', 10, 10, 2)]);
      expect(waiting.stage, ModuleStage.exception);
      expect(waiting.canTakePostTest, isFalse);
      expect(waiting.completingPost, isNull);
      final approved = run(true, [t('PRE', 10, 10, 1), t('POST', 9, 10, 2)]);
      expect(approved.stage, ModuleStage.postTest);
      expect(approved.completingPost?.clientId, 'POST2');
    });

    test('modules without questions are read and marked complete as before', () {
      final s = computeLearning([const ModuleInput(moduleId: 'A', questionUsages: [])]).single;
      expect(s.hasTests, isFalse);
      expect(s.canRead, isTrue);
      expect(s.stage, ModuleStage.reading);
    });

    test('visibility: general for everyone, role-specific for its roles, staff see all', () {
      expect(moduleVisibleTo(audience: 'GENERAL', learnerRoles: const [], staff: false, learnerRole: null), isTrue);
      expect(moduleVisibleTo(audience: 'ROLE_SPECIFIC', learnerRoles: const ['LOGISTICIAN'], staff: false, learnerRole: 'CDD'), isFalse);
      expect(moduleVisibleTo(audience: 'ROLE_SPECIFIC', learnerRoles: const ['LOGISTICIAN'], staff: false, learnerRole: 'LOGISTICIAN'), isTrue);
      expect(moduleVisibleTo(audience: 'ROLE_SPECIFIC', learnerRoles: const ['LOGISTICIAN'], staff: false, learnerRole: null), isFalse);
      expect(moduleVisibleTo(audience: 'ROLE_SPECIFIC', learnerRoles: const ['LOGISTICIAN'], staff: true), isTrue);
    });
  });

  test('upgrading a version 6 database keeps attempts (as legacy) and reading progress', () async {
    final dir = await Directory.systemTemp.createTemp('sarmaan-v6');
    final file = File('${dir.path}/db.sqlite');
    // Build today's schema, then take it back to version 6 (drop the v7 columns).
    var db = LocalDatabase.forTesting(NativeDatabase(file));
    await db.customSelect('SELECT 1').get();
    for (final (table, column) in [
      ('cached_modules', 'audience'),
      ('cached_modules', 'learner_roles_json'),
      ('local_progress', 'reading_completed_at'),
      ('cached_quiz_questions', 'usage'),
      ('local_quiz_attempts', 'test_type'),
      ('local_quiz_attempts', 'server_valid'),
      ('local_quiz_attempts', 'invalid_reason'),
    ]) {
      await db.customStatement('ALTER TABLE $table DROP COLUMN $column');
    }
    await db.customStatement(
        "INSERT INTO local_quiz_attempts (user_id, module_id, client_id, correct_count, total_count, score_percent, passed, results_json, taken_at, synced) "
        "VALUES ('u', 'A', 'old-1', 9, 10, 90, 1, '[]', 1700000000, 1)");
    await db.customStatement(
        "INSERT INTO local_progress (module_id, progress_percent, completed, last_opened_at, synced, user_id) VALUES ('A', 99, 0, 1700000500, 1, 'u')");
    await db.customStatement(
        "INSERT INTO local_progress (module_id, progress_percent, completed, last_opened_at, synced, user_id) VALUES ('B', 10, 0, 1700000600, 1, 'u')");
    await db.customStatement('PRAGMA user_version = 6');
    await db.close();

    db = LocalDatabase.forTesting(NativeDatabase(file));
    db.setActiveUser('u', learnerRole: 'CDD');
    final attempt = (await db.getQuizAttempts()).single;
    expect(attempt.testType, 'LEGACY');
    final progress = {for (final p in await db.getAllProgress()) p.moduleId: p};
    expect(progress['A']!.readingCompletedAt, isNotNull, reason: 'reading already done is kept');
    expect(progress['B']!.readingCompletedAt, isNull);
    expect(progress['A']!.progressPercent, 99);
    await db.close();
    await dir.delete(recursive: true);
  });

  group('local database', () {
    late LocalDatabase db;
    final now = DateTime(2026, 11, 4);

    Future<void> module(String id, int order, {String audience = 'GENERAL', List<String> roles = const [], int questions = 2}) async {
      await db.into(db.cachedModules).insert(CachedModulesCompanion.insert(
            id: id,
            moduleCode: id,
            moduleNumber: order,
            title: 'Module $id',
            status: 'PUBLISHED',
            sortOrder: order,
            cachedAt: now,
            audience: Value(audience),
            learnerRolesJson: Value(jsonEncode(roles)),
          ));
      await db.into(db.contentChunks).insert(ContentChunksCompanion.insert(
            id: 'chunk-$id', moduleId: id, moduleCode: id, language: 'en', sourceTitle: 'Module $id', chunkText: 'text $id'));
      for (var i = 0; i < questions; i++) {
        await db.into(db.cachedQuizQuestions).insert(CachedQuizQuestionsCompanion.insert(
              id: '$id-q$i', moduleId: id, questionType: 'TRUE_FALSE', prompt: 'Q$i', contentJson: '{"correct": true}', sortOrder: i));
      }
    }

    Future<TestOutcome> take(String moduleId, String type, int correct, int total) => recordTestAttempt(
          db,
          moduleId: moduleId,
          testType: type,
          correct: correct,
          total: total,
          resultsJson: '[]',
          clientId: '$type-$moduleId-${DateTime.now().microsecondsSinceEpoch}',
        );

    setUp(() async {
      db = LocalDatabase.forTesting(NativeDatabase.memory());
      db.setActiveUser('user-1', learnerRole: 'CDD');
      await module('A', 1);
      await module('B', 2);
      await module('R', 3, audience: 'ROLE_SPECIFIC', roles: ['HEALTH_WORKER']);
    });
    tearDown(() => db.close());

    test('a learner never sees another role\'s module, its search passages or its id', () async {
      expect([for (final m in await db.getAllModules()) m.id], ['A', 'B']);
      expect(await db.getModule('R'), isNull);
      expect({for (final c in await db.getChunks('en')) c.moduleId}, {'A', 'B'});
      expect((await loadLearning(db)).of('R'), isNull);

      db.setActiveUser('user-2', learnerRole: 'HEALTH_WORKER');
      expect([for (final m in await db.getAllModules()) m.id], ['A', 'B', 'R']);
      db.setActiveUser('staff-1', staff: true);
      expect((await db.getAllModules()).length, 3);
    });

    test('pre-test, reading, post-test at exactly 90% completes and queues the upload', () async {
      expect((await loadLearning(db)).of('A')!.stage, ModuleStage.preTest);
      await expectLater(take('A', 'POST', 9, 10), throwsStateError, reason: 'no post-test before the pre-test');
      final pre = await take('A', 'PRE', 5, 10);
      expect(pre.after.stage, ModuleStage.reading);
      await expectLater(take('A', 'PRE', 1, 10), throwsStateError, reason: 'the pre-test is taken once');
      await expectLater(take('A', 'POST', 9, 10), throwsStateError, reason: 'no post-test before reading');

      await db.markReadingComplete('A');
      final post = await take('A', 'POST', 9, 10);
      expect(post.reachedPassMark && post.beatPreTest && post.completedNow, isTrue);
      expect((await db.getProgressForModule('A'))!.completed, isTrue);
      final queued = await db.getPendingByType('progress');
      expect(queued.single.payloadJson, contains('"completed":true'));
      expect((await loadLearning(db)).of('B')!.stage, ModuleStage.preTest);
    });

    test('below 90% or not higher than the pre-test does not complete; retries are kept', () async {
      await take('A', 'PRE', 9, 10);
      await db.markReadingComplete('A');
      expect((await take('A', 'POST', 8, 10)).completedNow, isFalse); // below 90%
      final equal = await take('A', 'POST', 9, 10); // 90% but equal to the pre-test
      expect(equal.reachedPassMark, isTrue);
      expect(equal.beatPreTest, isFalse);
      expect(equal.completedNow, isFalse);
      expect((await loadLearning(db)).of('B')!.stage, ModuleStage.locked);
      final ok = await take('A', 'POST', 10, 10);
      expect(ok.completedNow, isTrue);
      expect((await db.getQuizAttempts(moduleId: 'A')).length, 4);
    });

    test('an attempt the server did not count is ignored, and restored attempts keep the baseline', () async {
      await db.restoreAttemptFromServer(
        clientId: 'srv-pre', moduleId: 'A', testType: 'PRE', correct: 6, total: 10, scorePercent: 60, passed: false,
        valid: true, takenAt: now);
      await db.restoreAttemptFromServer(
        clientId: 'srv-bad', moduleId: 'A', testType: 'PRE', correct: 1, total: 10, scorePercent: 10, passed: false,
        valid: false, invalidReason: 'pre-test already taken', takenAt: now.add(const Duration(minutes: 5)));
      final s = (await loadLearning(db)).of('A')!;
      expect(s.pre?.clientId, 'srv-pre');
      expect((await db.getUnsyncedQuizAttempts()), isEmpty, reason: 'restored attempts are not uploaded again');
    });

    test('legacy single-quiz attempts never count', () async {
      await db.into(db.localQuizAttempts).insert(LocalQuizAttemptsCompanion.insert(
            userId: const Value('user-1'), moduleId: 'A', clientId: 'old', correctCount: 10, totalCount: 10,
            scorePercent: 100, passed: true, resultsJson: '[]', takenAt: now, testType: const Value('LEGACY')));
      expect((await loadLearning(db)).of('A')!.stage, ModuleStage.preTest);
    });

    test('an approved exception lets a 100% pre-test learner complete with 90%', () async {
      await take('A', 'PRE', 10, 10);
      await db.markReadingComplete('A');
      expect((await loadLearning(db)).of('A')!.stage, ModuleStage.exception);
      await expectLater(take('A', 'POST', 10, 10), throwsStateError);
      await db.setTestExceptions(['A']);
      expect((await take('A', 'POST', 9, 10)).completedNow, isTrue);
    });

    test('pre-test and post-test questions follow their usage tags', () async {
      await (db.update(db.cachedQuizQuestions)..where((q) => q.id.equals('A-q0'))).write(const CachedQuizQuestionsCompanion(usage: Value('PRE')));
      expect([for (final q in await db.getQuizQuestions('A', testType: 'PRE')) q.id], ['A-q0', 'A-q1']);
      expect([for (final q in await db.getQuizQuestions('A', testType: 'POST')) q.id], ['A-q1']);
    });

    test('a hidden module\'s downloaded video is removed after a role change', () async {
      await db.into(db.cachedVideos).insert(CachedVideosCompanion.insert(
            id: 'v1', title: 'V', moduleId: const Value('R'), language: 'en', offlineAvailable: true, status: 'PUBLISHED',
            hasFile: true, localPath: const Value('/tmp/v1.mp4')));
      db.setActiveUser('user-2', learnerRole: 'HEALTH_WORKER');
      expect(await db.removeVideosOfHiddenModules(), isEmpty);
      db.setActiveUser('user-2', learnerRole: 'LOGISTICIAN');
      expect(await db.removeVideosOfHiddenModules(), ['/tmp/v1.mp4']);
      expect(await db.getVideo('v1'), isNull);
    });
  });
}
