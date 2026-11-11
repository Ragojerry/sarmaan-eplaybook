import 'dart:convert';
import 'dart:io';

import 'package:drift/drift.dart' show Value;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarmaan_eplaybook/db/local_database.dart';
import 'package:sarmaan_eplaybook/learning/learning_rules.dart';
import 'package:sarmaan_eplaybook/learning/learning_service.dart';

/// Module completion (inline True/False quiz + minimum active time), the General
/// pre/post test, and role-based visibility of the local cache. The rules are
/// checked against the vectors the backend generates (test/learning_vectors.json),
/// so both sides agree.
void main() {
  group('rules (shared vectors)', () {
    final vectors = jsonDecode(File('test/learning_vectors.json').readAsStringSync()) as Map<String, dynamic>;
    test('pass mark 90, default minimum time 180 seconds', () {
      expect(vectors['pass_mark'], 90);
      expect(vectors['module_min_seconds'], kDefaultModuleMinSeconds);
    });
    for (final c in (vectors['completion'] as List).cast<Map<String, dynamic>>()) {
      test('completion: ${c['why']}', () {
        final n = c['quiz_statements'] as int;
        final correct = c['quiz_correct'] as int?;
        final passed = n > 0 && correct != null && moduleQuizPasses(correct, n);
        expect(
          canCompleteModule(
              unlocked: c['unlocked'] as bool, hasQuiz: n > 0, quizPassed: passed, seconds: c['seconds'] as int, minSeconds: c['min_seconds'] as int),
          c['can_complete'],
        );
      });
    }
    for (final c in (vectors['cases'] as List).cast<Map<String, dynamic>>()) {
      test('retired pre/post rule: ${c['why']}', () {
        expect(
          postTestCompletes(c['post_correct'] as int, c['post_total'] as int, c['pre_correct'] as int, c['pre_total'] as int,
              autoApprovePercent: vectors['auto_approve_percent'] as int),
          c['completes'],
        );
      });
    }
  });

  group('state', () {
    TestScore quiz(int correct, int minute, {int total = 3}) => TestScore(
          clientId: 'q$minute', testType: 'MODULE_QUIZ', correct: correct, total: total, takenAt: DateTime(2026, 11, 10, 9, minute));

    test('the quiz and the minimum time both decide completion; the next module waits', () {
      List<ModuleLearning> run({List<TestScore> a = const [], int secs = 0, bool done = false}) => computeLearning(minSeconds: 180, [
            ModuleInput(moduleId: 'A', quizStatements: 3, quizAttempts: a, secondsSpent: secs, completed: done),
            const ModuleInput(moduleId: 'B', quizStatements: 3),
          ]);
      var s = run();
      expect(s[0].stage, ModuleStage.reading);
      expect(s[0].canRead && s[0].canTakeQuiz, isTrue);
      expect(s[0].canComplete, isFalse);
      expect(s[1].stage, ModuleStage.locked);
      s = run(a: [quiz(2, 1)], secs: 600);
      expect(s[0].quizPassed, isFalse, reason: '2 of 3 is below 90%');
      s = run(a: [quiz(2, 1), quiz(3, 2)], secs: 179);
      expect(s[0].quizPassed, isTrue, reason: 'retakes until passed');
      expect(s[0].canComplete, isFalse, reason: 'one second short');
      expect(s[0].secondsLeft, 1);
      s = run(a: [quiz(3, 2)], secs: 180);
      expect(s[0].canComplete, isTrue);
      s = run(a: [quiz(3, 2)], secs: 180, done: true);
      expect(s[0].stage, ModuleStage.completed);
      expect(s[0].canTakeQuiz || s[0].canComplete, isFalse, reason: 'a completed module is review-only');
      expect(s[1].stage, ModuleStage.reading, reason: 'the next module unlocks');
    });

    test('a module without a quiz needs only the time', () {
      final s = computeLearning(minSeconds: 180, [const ModuleInput(moduleId: 'A', secondsSpent: 180)]);
      expect(s[0].hasQuiz, isFalse);
      expect(s[0].quizPassed && s[0].canComplete, isTrue);
    });

    test('the General pre-test gate locks every module until it is taken; completed ones stay open', () {
      final s = computeLearning(gateOpen: false, [
        const ModuleInput(moduleId: 'A', completed: true),
        const ModuleInput(moduleId: 'B'),
      ]);
      expect(s[0].stage, ModuleStage.completed);
      expect(s[1].stage, ModuleStage.locked);
      expect(s[1].lockedByGeneralTest, isTrue);
    });

    test('General test: pre once, post once after all modules', () {
      final pre = TestScore(clientId: 'p', testType: 'PRE', correct: 10, total: 25, takenAt: DateTime(2026, 11, 10));
      expect(const GeneralLearning(active: true, questions: 25, pre: null, post: null, modulesTotal: 2, modulesCompleted: 0).canTakePre, isTrue);
      final half = GeneralLearning(active: true, questions: 25, pre: pre, post: null, modulesTotal: 2, modulesCompleted: 1);
      expect(half.canTakePre || half.canTakePost, isFalse);
      expect(half.gateOpen, isTrue);
      final all = GeneralLearning(active: true, questions: 25, pre: pre, post: null, modulesTotal: 2, modulesCompleted: 2);
      expect(all.canTakePost, isTrue);
      expect(const GeneralLearning(active: false, questions: 0, pre: null, post: null, modulesTotal: 2, modulesCompleted: 0).gateOpen, isTrue);
      expect(formatDuration(80), '1:20');
      expect(formatDuration(180), '3:00');
    });

    test('visibility: general for everyone, role-specific for its roles, staff see all', () {
      expect(moduleVisibleTo(audience: 'GENERAL', learnerRoles: const [], staff: false, learnerRole: null), isTrue);
      expect(moduleVisibleTo(audience: 'ROLE_SPECIFIC', learnerRoles: const ['LOGISTICIAN'], staff: false, learnerRole: 'CDD'), isFalse);
      expect(moduleVisibleTo(audience: 'ROLE_SPECIFIC', learnerRoles: const ['LOGISTICIAN'], staff: false, learnerRole: 'LOGISTICIAN'), isTrue);
      expect(moduleVisibleTo(audience: 'ROLE_SPECIFIC', learnerRoles: const ['LOGISTICIAN'], staff: false, learnerRole: null), isFalse);
      expect(moduleVisibleTo(audience: 'ROLE_SPECIFIC', learnerRoles: const ['LOGISTICIAN'], staff: true), isTrue);
    });
  });

  test('upgrading a version 7 database keeps progress and attempts, with time starting at 0', () async {
    final dir = await Directory.systemTemp.createTemp('sarmaan-v7');
    final file = File('${dir.path}/db.sqlite');
    // Build today's schema, then take it back to version 7 (drop what v8 added).
    var db = LocalDatabase.forTesting(NativeDatabase(file));
    await db.customSelect('SELECT 1').get();
    await db.customStatement('ALTER TABLE local_progress DROP COLUMN seconds_spent');
    await db.customStatement('DROP TABLE cached_general_questions');
    await db.customStatement('DROP TABLE local_general_attempts');
    await db.customStatement(
        "INSERT INTO local_quiz_attempts (user_id, module_id, client_id, correct_count, total_count, score_percent, passed, results_json, taken_at, synced, test_type) "
        "VALUES ('u', 'A', 'old-pre', 9, 10, 90, 1, '[]', 1700000000, 1, 'PRE')");
    await db.customStatement(
        "INSERT INTO local_progress (module_id, progress_percent, completed, last_opened_at, synced, user_id) VALUES ('A', 100, 1, 1700000500, 1, 'u')");
    await db.customStatement('PRAGMA user_version = 7');
    await db.close();

    db = LocalDatabase.forTesting(NativeDatabase(file));
    db.setActiveUser('u', learnerRole: 'CDD');
    expect((await db.getQuizAttempts()).single.testType, 'PRE', reason: 'old attempts are kept as history');
    final p = (await db.getAllProgress()).single;
    expect(p.completed && p.progressPercent == 100, isTrue, reason: 'a completed module stays completed');
    expect(p.secondsSpent, 0);
    expect(await db.getGeneralAttempts(), isEmpty);
    expect(await db.getGeneralQuestions(), isEmpty);
    await db.close();
    await dir.delete(recursive: true);
  });

  group('local database', () {
    late LocalDatabase db;
    final now = DateTime(2026, 11, 10);

    Future<void> module(String id, int order, {String audience = 'GENERAL', List<String> roles = const [], List<bool> quiz = const [true, false, true]}) async {
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
      await db.into(db.cachedSections).insert(CachedSectionsCompanion.insert(
          id: '$id-s0', moduleId: id, sectionNumber: 1, contentType: 'TEXT', contentJson: '{"text": "Reading $id"}', sortOrder: 1));
      for (var i = 0; i < quiz.length; i++) {
        await db.into(db.cachedSections).insert(CachedSectionsCompanion.insert(
            id: '$id-tf$i',
            moduleId: id,
            sectionNumber: i + 2,
            contentType: 'TRUE_FALSE',
            contentJson: jsonEncode({'statement': 'Statement $i', 'answer': quiz[i], 'audience': 'HFW'}),
            sortOrder: i + 2));
      }
    }

    Map<String, bool> right(String id) => {'$id-tf0': true, '$id-tf1': false, '$id-tf2': true};

    Future<void> generalTest() async {
      await db.setGeneralTestActive(true);
      await db.replaceGeneralQuestions([
        for (var i = 0; i < 3; i++)
          CachedGeneralQuestionsCompanion.insert(
              id: 'g$i', number: i + 1, prompt: 'Question $i?', optionsJson: '["a","b","c","d"]', correctIndex: Value(i)),
      ]);
    }

    setUp(() async {
      db = LocalDatabase.forTesting(NativeDatabase.memory());
      db.setActiveUser('user-1', learnerRole: 'CDD');
      await module('A', 1);
      await module('B', 2, quiz: const []);
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

    test('the module quiz, retries and the minimum time complete a module offline and queue the upload', () async {
      expect((await db.quizStatementCountsByModule())['A'], 3);
      var wrong = await recordModuleQuiz(db, moduleId: 'A', answers: {...right('A'), 'A-tf1': true});
      expect((wrong.correct, wrong.total, wrong.passed), (2, 3, false));
      expect(await completeModule(db, 'A'), 'Answer the module quiz correctly to finish this module.');
      final ok = await recordModuleQuiz(db, moduleId: 'A', answers: right('A'));
      expect(ok.passed && ok.completedModuleQuiz, isTrue);
      expect(await completeModule(db, 'A'), contains('Please spend at least 3:00 in this module.'));
      await db.addModuleSeconds('A', 120);
      await db.addModuleSeconds('A', 60);
      expect((await db.getProgressForModule('A'))!.secondsSpent, 180);
      expect(await completeModule(db, 'A'), isNull);
      expect((await db.getProgressForModule('A'))!.completed, isTrue);
      expect((await db.getPendingByType('progress')).single.payloadJson, contains('"completed":true'));
      expect([for (final a in await db.getUnsyncedQuizAttempts()) a.testType], ['MODULE_QUIZ', 'MODULE_QUIZ']);
      final b = (await loadLearning(db)).of('B')!;
      expect(b.stage, ModuleStage.reading, reason: 'the next module unlocks');
      expect(b.hasQuiz, isFalse);
      await expectLater(recordModuleQuiz(db, moduleId: 'A', answers: right('A')), throwsStateError,
          reason: 'a completed module is review-only');
    });

    test('old per-module test attempts and attempts the server refused never count', () async {
      for (final type in ['PRE', 'POST', 'LEGACY']) {
        await db.into(db.localQuizAttempts).insert(LocalQuizAttemptsCompanion.insert(
              userId: const Value('user-1'), moduleId: 'A', clientId: 'old-$type', correctCount: 3, totalCount: 3,
              scorePercent: 100, passed: true, resultsJson: '[]', takenAt: now, testType: Value(type)));
      }
      await db.restoreAttemptFromServer(
          clientId: 'srv-bad', moduleId: 'A', testType: 'MODULE_QUIZ', correct: 3, total: 3, scorePercent: 100, passed: true,
          valid: false, invalidReason: 'module is locked', takenAt: now);
      expect((await loadLearning(db)).of('A')!.quizPassed, isFalse);
      await db.restoreAttemptFromServer(
          clientId: 'srv-ok', moduleId: 'A', testType: 'MODULE_QUIZ', correct: 3, total: 3, scorePercent: 100, passed: true,
          valid: true, takenAt: now);
      expect((await loadLearning(db)).of('A')!.quizPassed, isTrue, reason: 'restored from the server (new phone)');
    });

    test('the General pre-test opens the modules; the post-test opens after all of them; each is taken once', () async {
      await generalTest();
      var l = await loadLearning(db);
      expect(l.of('A')!.lockedByGeneralTest, isTrue);
      expect(await completeModule(db, 'A'), 'Take the General pre-test first.');
      await expectLater(recordGeneralTest(db, testType: 'POST', answers: const {}), throwsStateError);
      final pre = await recordGeneralTest(db, testType: 'PRE', answers: {'g0': 0, 'g1': 0}); // g1 wrong, g2 unanswered
      expect((pre.correct, pre.total, pre.percent), (1, 3, 33));
      await expectLater(recordGeneralTest(db, testType: 'PRE', answers: const {}), throwsStateError, reason: 'once only');
      l = await loadLearning(db);
      expect(l.of('A')!.unlocked && l.general.gateOpen, isTrue);
      expect(l.general.canTakePost, isFalse);
      for (final id in ['A', 'B']) {
        if (id == 'A') await recordModuleQuiz(db, moduleId: id, answers: right(id));
        await db.addModuleSeconds(id, 200);
        expect(await completeModule(db, id), isNull);
      }
      expect((await loadLearning(db)).general.canTakePost, isTrue);
      final post = await recordGeneralTest(db, testType: 'POST', answers: {'g0': 0, 'g1': 1, 'g2': 2});
      expect((post.correct, post.pre!.correct), (3, 1));
      await expectLater(recordGeneralTest(db, testType: 'POST', answers: const {}), throwsStateError, reason: 'once only');
      final queued = await db.getUnsyncedGeneralAttempts();
      expect([for (final a in queued) a.testType], ['PRE', 'POST']);
      expect(jsonDecode(queued.first.answersJson), [
        {'question_id': 'g0', 'choice': 0},
        {'question_id': 'g1', 'choice': 0},
        {'question_id': 'g2', 'choice': null},
      ]);
    });

    test('restarting the training clears the General results and the time spent', () async {
      await generalTest();
      await recordGeneralTest(db, testType: 'PRE', answers: const {'g0': 0});
      await db.addModuleSeconds('A', 90);
      await db.restartTraining();
      expect(await db.getGeneralAttempts(), isEmpty);
      expect(await db.getAllProgress(), isEmpty);
      expect((await loadLearning(db)).of('A')!.lockedByGeneralTest, isTrue, reason: 'the pre-test is needed again');
    });

    test('time from another phone counts here too, and never goes down', () async {
      await db.addModuleSeconds('A', 50);
      await db.markProgressSynced('A', (await db.getProgressForModule('A'))!.lastOpenedAt);
      await db.restoreProgressFromServer(moduleId: 'A', progressPercent: 10, completed: false, secondsSpent: 140);
      expect((await db.getProgressForModule('A'))!.secondsSpent, 140);
      await db.restoreProgressFromServer(moduleId: 'A', progressPercent: 10, completed: false, secondsSpent: 20);
      expect((await db.getProgressForModule('A'))!.secondsSpent, 140);
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
