import 'dart:convert';
import 'dart:io';

import 'package:drift/drift.dart' show Value;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:sarmaan_eplaybook/db/local_database.dart';
import 'package:sarmaan_eplaybook/learning/learning_service.dart';
import 'package:sarmaan_eplaybook/offline/content_sync_service.dart';
import 'package:sarmaan_eplaybook/screens/reader_screen.dart';

/// Bug 1: the quiz result is saved when the last statement is answered; the module
/// is completed only with "Complete module" (quiz passed + minimum time), in one
/// local transaction, its quiz attempts are uploaded in the same sync as the
/// completion, and the learner goes to Home where the next module is open.
/// Bug 2: a retry asks only the statements still wrong, saved per user per module.
/// For every role. All offline, against the local database.

/// A module: id, number of True/False statements (0 = no quiz). Every statement's
/// right answer is True; each has a content section just above it.
typedef Mod = (String id, int statements);

const roles = {
  'CDD': [('C1', 3), ('C2', 3), ('C3', 3)],
  'HEALTH_WORKER': [('H1', 3), ('H2', 0), ('H3', 3)],
  'OTHER': [('O1', 3), ('O2', 3)],
};

Future<LocalDatabase> seed(List<Mod> mods, {String role = 'CDD', int minSeconds = 0, File? file, bool generalTest = false}) async {
  final db = LocalDatabase.forTesting(file == null ? NativeDatabase.memory() : NativeDatabase(file));
  db.setActiveUser('learner-1', learnerRole: role);
  final now = DateTime(2026, 11, 13, 9);
  var order = 0;
  for (final (id, statements) in mods) {
    order++;
    await db.into(db.cachedModules).insert(CachedModulesCompanion.insert(
        id: id, moduleCode: 'M-$id', moduleNumber: order, title: 'Module $id', status: 'PUBLISHED', sortOrder: order, cachedAt: now));
    await db.into(db.cachedTranslations).insert(CachedTranslationsCompanion.insert(
        id: 't$id', moduleId: id, languageId: 'en-id', languageCode: 'en', title: 'Module $id', status: 'PUBLISHED'));
    var n = 0;
    for (var k = 1; k <= statements; k++) {
      await db.into(db.cachedSections).insert(CachedSectionsCompanion.insert(
          id: '$id-s$k', moduleId: id, sectionNumber: ++n, contentType: 'TEXT', contentJson: '{"text": "Teaching $id $k."}', sortOrder: n));
      await db.into(db.cachedSections).insert(CachedSectionsCompanion.insert(
          id: '$id-q$k',
          moduleId: id,
          sectionNumber: ++n,
          contentType: 'TRUE_FALSE',
          contentJson: jsonEncode({'statement': 'Statement $id $k', 'answer': true}),
          sortOrder: n));
    }
    if (statements == 0) {
      await db.into(db.cachedSections).insert(CachedSectionsCompanion.insert(
          id: '$id-s1', moduleId: id, sectionNumber: 1, contentType: 'TEXT', contentJson: '{"text": "Reading only."}', sortOrder: 1));
    }
  }
  await db.setModuleMinSeconds(minSeconds);
  if (generalTest) {
    await db.setGeneralTestActive(true);
    await db.replaceGeneralQuestions([
      for (var i = 0; i < 25; i++)
        CachedGeneralQuestionsCompanion.insert(id: 'g$i', number: i + 1, prompt: 'Q$i', optionsJson: '["a","b"]', correctIndex: const Value(0)),
    ]);
    await db.insertGeneralAttempt(clientId: 'pre', testType: 'PRE', correct: 12, total: 25, answersJson: '[]', passMark: 60);
  }
  return db;
}

Map<String, bool> allRight(String id, int n) => {for (var k = 1; k <= n; k++) '$id-q$k': true};

void main() {
  group('Bug 1: completion and unlock', () {
    test('passing saves the result only; "Complete module" completes and opens the next module', () async {
      final db = await seed(roles['CDD']!);
      addTearDown(db.close);
      final r = await recordModuleQuiz(db, moduleId: 'C1', answers: allRight('C1', 3));
      expect(r.passed, isTrue);
      var l = await loadLearning(db);
      expect(l.of('C1')!.quizPassed && !l.of('C1')!.completed, isTrue, reason: 'nothing completes by itself');
      expect(l.of('C2')!.unlocked, isFalse);
      expect(await completeModule(db, 'C1'), isNull);
      l = await loadLearning(db);
      expect(l.of('C1')!.completed && l.of('C2')!.unlocked, isTrue, reason: 'the next module opens with the completion');
    });

    test('the quiz attempts are held until the module is completed, then go in the same sync', () async {
      final db = await seed(roles['CDD']!);
      addTearDown(db.close);
      await recordModuleQuiz(db, moduleId: 'C1', answers: {...allRight('C1', 3), 'C1-q2': false});
      await recordModuleQuiz(db, moduleId: 'C1', answers: {'C1-q2': true});
      expect(await quizAttemptsReadyToUpload(db), isEmpty, reason: 'not sent while the module is not completed');
      expect(await completeModule(db, 'C1'), isNull);
      expect((await quizAttemptsReadyToUpload(db)).map((a) => a.correctCount), [2, 3], reason: 'both attempts, honestly');
      expect((await db.getUnsyncedItems()).where((i) => i.entityType == 'progress'), isNotEmpty,
          reason: 'the completion is queued for the same sync');
    });

    test('the 3-minute rule still applies to "Complete module"', () async {
      final db = await seed(roles['CDD']!, minSeconds: 180);
      addTearDown(db.close);
      await recordModuleQuiz(db, moduleId: 'C1', answers: allRight('C1', 3));
      expect(await completeModule(db, 'C1'), contains('3:00'));
      expect((await loadLearning(db)).of('C1')!.completed, isFalse);
      await db.addModuleSeconds('C1', 180);
      expect(await completeModule(db, 'C1'), isNull);
      expect((await loadLearning(db)).of('C2')!.unlocked, isTrue);
    });

    test('the unlock survives an app restart (everything rebuilt from the database)', () async {
      final dir = await Directory.systemTemp.createTemp('sarmaan-flow-');
      addTearDown(() => dir.delete(recursive: true));
      final file = File('${dir.path}/app.sqlite');
      final first = await seed(roles['CDD']!, file: file);
      await recordModuleQuiz(first, moduleId: 'C1', answers: allRight('C1', 3));
      await completeModule(first, 'C1');
      await first.close();
      final again = LocalDatabase.forTesting(NativeDatabase(file));
      again.setActiveUser('learner-1', learnerRole: 'CDD');
      final l = await loadLearning(again);
      expect(l.of('C1')!.completed && l.of('C2')!.unlocked, isTrue);
      await again.close();
    });

    test('offline completion, then a sync with an older server copy, does not re-lock', () async {
      final db = await seed(roles['CDD']!);
      addTearDown(db.close);
      await recordModuleQuiz(db, moduleId: 'C1', answers: allRight('C1', 3));
      await completeModule(db, 'C1');
      final local = await db.getProgressForModule('C1');
      await db.markProgressSynced('C1', local!.lastOpenedAt);
      // The server has not got the completion yet, and its copy says "opened later".
      await db.restoreProgressFromServer(moduleId: 'C1', progressPercent: 50, completed: false,
          lastOpenedAt: DateTime.now().add(const Duration(hours: 1)));
      final l = await loadLearning(db);
      expect(l.of('C1')!.completed && l.of('C2')!.unlocked, isTrue);
    });

    for (final role in roles.keys) {
      test('[$role] every module in order, the last one opens the General post-test', () async {
        final mods = roles[role]!;
        final db = await seed(mods, role: role, generalTest: true);
        addTearDown(db.close);
        for (final (id, n) in mods) {
          expect((await loadLearning(db)).of(id)!.unlocked, isTrue, reason: '$id open');
          if (n > 0) await recordModuleQuiz(db, moduleId: id, answers: allRight(id, n));
          expect(await completeModule(db, id), isNull, reason: '$id: "Complete module"');
          expect((await loadLearning(db)).of(id)!.completed, isTrue, reason: '$id completed');
        }
        expect((await loadLearning(db)).general.canTakePost, isTrue, reason: 'the last module opens the post-test');
      });
    }
  });

  group('Bug 2: retry only the statements still wrong', () {
    test('fail 2 of 6: retry asks exactly those 2; 1 right leaves 1; then passed and the next module open', () async {
      final db = await seed([('S6', 6), ('NEXT', 3)]);
      addTearDown(db.close);
      final first = await recordModuleQuiz(db, moduleId: 'S6',
          answers: {...allRight('S6', 6), 'S6-q2': false, 'S6-q5': false});
      expect((first.correct, first.total, first.passed), (4, 6, false));
      final credit = await quizCredit(db, 'S6');
      final toRetry = {for (var k = 1; k <= 6; k++) 'S6-q$k'}.difference(credit);
      expect(toRetry, {'S6-q2', 'S6-q5'});
      final second = await recordModuleQuiz(db, moduleId: 'S6', answers: {'S6-q2': true, 'S6-q5': false});
      expect((second.correct, second.remaining, second.passed), (5, 1, false));
      expect({for (var k = 1; k <= 6; k++) 'S6-q$k'}.difference(await quizCredit(db, 'S6')), {'S6-q5'});
      final third = await recordModuleQuiz(db, moduleId: 'S6', answers: {'S6-q5': true});
      expect(third.passed, isTrue);
      expect(await completeModule(db, 'S6'), isNull);
      final l = await loadLearning(db);
      expect(l.of('S6')!.completed && l.of('NEXT')!.unlocked, isTrue);
      final rows = (await db.getQuizAttempts()).where((a) => a.moduleId == 'S6').toList();
      expect(rows, hasLength(3), reason: 'three honest attempts, each kept');
    });

    test('resume after leaving mid-retry (app restart): only the remaining statement is asked', () async {
      final dir = await Directory.systemTemp.createTemp('sarmaan-retry-');
      addTearDown(() => dir.delete(recursive: true));
      final file = File('${dir.path}/app.sqlite');
      final first = await seed([('S6', 6), ('NEXT', 3)], file: file);
      await recordModuleQuiz(first, moduleId: 'S6', answers: {...allRight('S6', 6), 'S6-q2': false, 'S6-q5': false});
      await recordModuleQuiz(first, moduleId: 'S6', answers: {'S6-q2': true, 'S6-q5': false});
      await first.close();
      final again = LocalDatabase.forTesting(NativeDatabase(file));
      again.setActiveUser('learner-1', learnerRole: 'CDD');
      expect({for (var k = 1; k <= 6; k++) 'S6-q$k'}.difference(await quizCredit(again, 'S6')), {'S6-q5'});
      expect((await recordModuleQuiz(again, moduleId: 'S6', answers: {'S6-q5': true})).passed, isTrue);
      await again.close();
    });

    test('a training restart clears the per-statement state', () async {
      final db = await seed([('S6', 6), ('NEXT', 3)]);
      addTearDown(db.close);
      await recordModuleQuiz(db, moduleId: 'S6', answers: {...allRight('S6', 6), 'S6-q2': false});
      expect(await quizCredit(db, 'S6'), hasLength(5));
      await db.restartTraining(at: DateTime.now());
      expect(await quizCredit(db, 'S6'), isEmpty);
      expect(await db.getQuizAttempts(), isEmpty);
    });

    test('statements removed by a content update are dropped from the saved state', () async {
      final db = await seed([('S6', 6), ('NEXT', 3)]);
      addTearDown(db.close);
      await recordModuleQuiz(db, moduleId: 'S6', answers: {...allRight('S6', 6), 'S6-q6': false});
      await (db.delete(db.cachedSections)..where((s) => s.id.isIn(['S6-q6', 'S6-q5']))).go();
      final r = await recordModuleQuiz(db, moduleId: 'S6', answers: const {});
      expect((r.correct, r.total, r.passed), (4, 4, true), reason: 'no crash; the remaining 4 kept their credit');
    });
  });

  group('in the reader (no navigation)', () {
    setUp(() {
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(const MethodChannel('flutter_tts'), (call) async => null);
    });

    Future<void> settle(WidgetTester tester) async {
      for (var i = 0; i < 8; i++) {
        await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 20)));
        await tester.pump(const Duration(milliseconds: 50));
      }
    }

    testWidgets('pass the quiz: nothing completes by itself; "Complete module" completes and goes Home', (tester) async {
      final db = (await tester.runAsync(() => seed(roles['CDD']!)))!;
      addTearDown(db.close);
      final router = GoRouter(initialLocation: '/reader/C1', routes: [
        GoRoute(path: '/modules', builder: (_, __) => const Scaffold(body: Text('MODULES'))),
        GoRoute(path: '/home', builder: (_, __) => const Scaffold(body: Text('HOME'))),
        GoRoute(path: '/reader/:moduleId', builder: (_, s) => ReaderScreen(moduleId: s.pathParameters['moduleId']!)),
      ]);
      await tester.pumpWidget(ProviderScope(overrides: [localDatabaseProvider.overrideWithValue(db)], child: MaterialApp.router(routerConfig: router)));
      await settle(tester);
      for (var k = 1; k <= 3; k++) {
        final card = find.ancestor(of: find.text('Statement C1 $k'), matching: find.byType(Container)).first;
        final button = find.descendant(of: card, matching: find.widgetWithText(OutlinedButton, 'True'));
        await tester.ensureVisible(button);
        await tester.tap(button);
        await settle(tester);
      }
      expect(find.text('Quiz passed. Well done!'), findsOneWidget);
      var l = (await tester.runAsync(() => loadLearning(db)))!;
      expect(l.of('C1')!.completed, isFalse, reason: 'passing alone does not complete the module');
      expect(l.of('C2')!.unlocked, isFalse, reason: 'and does not open the next one');
      expect(find.text('HOME'), findsNothing, reason: 'no automatic navigation');
      // The time indicator sits at the top of the module: scroll up to it.
      await tester.scrollUntilVisible(find.textContaining('Time in this module'), -300, scrollable: find.byType(Scrollable).first);
      expect(find.textContaining('Time in this module'), findsOneWidget, reason: 'the timer keeps running');

      await tester.scrollUntilVisible(find.widgetWithText(FilledButton, 'Complete module'), 300, scrollable: find.byType(Scrollable).first);
      await settle(tester);
      await tester.ensureVisible(find.widgetWithText(FilledButton, 'Complete module'));
      await tester.pump();
      await tester.tap(find.widgetWithText(FilledButton, 'Complete module'));
      await settle(tester);
      expect(find.text('HOME'), findsOneWidget, reason: '"Complete module" goes to Home');
      l = (await tester.runAsync(() => loadLearning(db)))!;
      expect(l.of('C1')!.completed && l.of('C2')!.unlocked, isTrue, reason: 'completed and the next module open');
      final ready = (await tester.runAsync(() => quizAttemptsReadyToUpload(db)))!;
      expect(ready, hasLength(1), reason: 'the quiz goes up with the completion');
    });
  });
}
