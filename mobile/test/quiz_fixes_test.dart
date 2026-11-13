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
import 'package:sarmaan_eplaybook/learning/certificate.dart';
import 'package:sarmaan_eplaybook/learning/learning_service.dart';
import 'package:sarmaan_eplaybook/offline/content_sync_service.dart';
import 'package:sarmaan_eplaybook/screens/modules_screen.dart' show GeneralTestCard;
import 'package:sarmaan_eplaybook/screens/reader_screen.dart';

const _lockedPrevious = 'module is locked: complete the previous module first';

/// Module A (one statement, already completed) and module B (a text section and three
/// statements), for a learner of [role]. All offline, against an in-memory database
/// unless [file] is given.
Future<LocalDatabase> _seed({String role = 'CDD', int minSeconds = 0, File? file}) async {
  final db = LocalDatabase.forTesting(file == null ? NativeDatabase.memory() : NativeDatabase(file));
  db.setActiveUser('learner-1', learnerRole: role);
  final now = DateTime(2026, 11, 13, 9);
  for (final (id, order) in [('A', 1), ('B', 2)]) {
    await db.into(db.cachedModules).insert(CachedModulesCompanion.insert(
        id: id, moduleCode: 'M-$id', moduleNumber: order, title: 'Module $id', status: 'PUBLISHED', sortOrder: order, cachedAt: now));
    await db.into(db.cachedTranslations).insert(CachedTranslationsCompanion.insert(
        id: 't$id', moduleId: id, languageId: 'en-id', languageCode: 'en', title: 'Module $id', status: 'PUBLISHED'));
  }
  Future<void> tf(String id, String module, int order, String text, bool answer) =>
      db.into(db.cachedSections).insert(CachedSectionsCompanion.insert(
          id: id,
          moduleId: module,
          sectionNumber: order,
          contentType: 'TRUE_FALSE',
          contentJson: jsonEncode({'statement': text, 'answer': answer, 'explanation': 'Because the training says so.'}),
          sortOrder: order));
  await tf('a1', 'A', 1, 'Statement A1', true);
  await db.into(db.cachedSections).insert(CachedSectionsCompanion.insert(
      id: 'b0', moduleId: 'B', sectionNumber: 1, contentType: 'TEXT', contentJson: '{"text": "Read this first."}', sortOrder: 1));
  await tf('b1', 'B', 2, 'Statement B1', true);
  await tf('b2', 'B', 3, 'Statement B2', false);
  await tf('b3', 'B', 4, 'Statement B3', true);
  await db.setModuleMinSeconds(minSeconds);
  await db.upsertProgress(moduleId: 'A', progressPercent: 100, completed: true);
  return db;
}

Future<String> _latestQuizClientId(LocalDatabase db, String moduleId) async {
  final rows = (await db.getQuizAttempts()).where((a) => a.moduleId == moduleId).toList()
    ..sort((a, b) => a.takenAt.compareTo(b.takenAt));
  return rows.last.clientId;
}

void main() {
  group('Problem 1: completion right after passing', () {
    for (final role in ['CDD', 'HEALTH_WORKER', 'OTHER']) {
      test('[$role] pass the quiz -> Complete works at once, with no retake', () async {
        final db = await _seed(role: role);
        addTearDown(db.close);
        final r = await recordModuleQuiz(db, moduleId: 'B', answers: {'b1': true, 'b2': false, 'b3': true});
        expect(r.passed, isTrue);
        expect(await completeModule(db, 'B'), isNull);
        expect((await loadLearning(db)).of('B')!.completed, isTrue);
      });

      test('[$role] a sync in the middle: an "upload order" refusal does not undo the pass', () async {
        final db = await _seed(role: role);
        addTearDown(db.close);
        await recordModuleQuiz(db, moduleId: 'B', answers: {'b1': true, 'b2': false, 'b3': true});
        // What the server answered when the quiz reached it before module A's completion.
        await db.markQuizAttemptSynced(await _latestQuizClientId(db, 'B'), valid: false, reason: _lockedPrevious);
        expect((await loadLearning(db)).of('B')!.quizPassed, isTrue, reason: 'the server re-checks it later');
        expect(await completeModule(db, 'B'), isNull, reason: 'before the fix: "pass the quiz first"');
      });
    }

    test('pass before the time is met, then the time is met: Complete works without leaving', () async {
      final db = await _seed(minSeconds: 180);
      addTearDown(db.close);
      await recordModuleQuiz(db, moduleId: 'B', answers: {'b1': true, 'b2': false, 'b3': true});
      expect(await completeModule(db, 'B'), contains('3:00'), reason: 'time not met yet');
      await db.addModuleSeconds('B', 180); // the reader saves the running time before completing
      expect(await completeModule(db, 'B'), isNull);
    });

    test('a later server correction is applied, and a final refusal still counts as refused', () async {
      final db = await _seed();
      addTearDown(db.close);
      await recordModuleQuiz(db, moduleId: 'B', answers: {'b1': true, 'b2': false, 'b3': true});
      final id = await _latestQuizClientId(db, 'B');
      await db.restoreAttemptFromServer(clientId: id, moduleId: 'B', testType: 'MODULE_QUIZ', correct: 3, total: 3, scorePercent: 100,
          passed: true, valid: true, takenAt: DateTime.now());
      expect((await loadLearning(db)).of('B')!.quizPassed, isTrue);
      await db.markQuizAttemptSynced(id, valid: false, reason: 'before training restart');
      expect((await loadLearning(db)).of('B')!.quizPassed, isFalse, reason: 'the rules are not relaxed');
    });
  });

  group('Problem 2: no post-test after certification', () {
    Future<LocalDatabase> certified({File? file}) async {
      final db = await _seed(file: file);
      await db.upsertProgress(moduleId: 'B', progressPercent: 100, completed: true);
      await db.setGeneralTestActive(true);
      await db.replaceGeneralQuestions([
        for (var i = 0; i < 25; i++)
          CachedGeneralQuestionsCompanion.insert(id: 'g$i', number: i + 1, prompt: 'Q$i', optionsJson: '["a","b"]', correctIndex: const Value(0)),
      ]);
      await db.insertGeneralAttempt(clientId: 'pre', testType: 'PRE', correct: 10, total: 25, answersJson: '[]', passMark: 60,
          takenAt: DateTime(2026, 11, 1));
      await db.insertGeneralAttempt(clientId: 'post', testType: 'POST', correct: 20, total: 25, answersJson: '[]', passMark: 60,
          takenAt: DateTime(2026, 11, 12));
      return db;
    }

    test('a post-test refused only for upload order still counts: certified, no post-test offered', () async {
      final db = await certified();
      addTearDown(db.close);
      // What the server answered when the post-test arrived before the last completion.
      await db.markGeneralAttemptSynced('post', valid: false, reason: 'complete all your modules first');
      final g = (await loadLearning(db)).general;
      expect(g.post, isNotNull);
      expect(g.canTakePost, isFalse, reason: 'before the fix the post-test came back');
      expect(hasCertificate(g), isTrue);
      // ... and when the server sends it as the counting result, it is marked as such.
      await db.restoreGeneralAttemptFromServer(clientId: 'post', testType: 'POST', correct: 20, total: 25,
          takenAt: DateTime(2026, 11, 12), passMark: 60);
      final row = (await db.getGeneralAttempts()).firstWhere((a) => a.clientId == 'post');
      expect((row.serverValid, row.invalidReason), (true, null));
    });

    testWidgets('no post-test entry on the General test card; modules stay open', (tester) async {
      final db = (await tester.runAsync(() => certified()))!;
      addTearDown(db.close);
      final learning = (await tester.runAsync(() => loadLearning(db)))!;
      await tester.pumpWidget(MaterialApp(home: Scaffold(body: GeneralTestCard(general: learning.general))));
      expect(find.byType(FilledButton), findsNothing, reason: 'no "take the post-test" action');
      expect(find.textContaining('20 of 25'), findsOneWidget, reason: 'the scores show instead');
      expect(learning.of('A')!.canRead && learning.of('B')!.canRead, isTrue);
      expect(learning.of('B')!.completed && !learning.of('B')!.canTakeQuiz, isTrue, reason: 'review only, nothing reset');
    });

    test('the state survives an app restart (the database is reopened) and a training restart clears it', () async {
      final dir = await Directory.systemTemp.createTemp('sarmaan-cert-');
      addTearDown(() => dir.delete(recursive: true));
      final file = File('${dir.path}/app.sqlite');
      final first = await certified(file: file);
      await first.close();
      final again = LocalDatabase.forTesting(NativeDatabase(file));
      again.setActiveUser('learner-1', learnerRole: 'CDD');
      final g = (await loadLearning(again)).general;
      expect(hasCertificate(g) && !g.canTakePost, isTrue);
      await again.restartTraining(at: DateTime.now());
      final after = (await loadLearning(again)).general;
      expect(after.post, isNull);
      expect(after.canTakePre, isTrue, reason: 'the normal flow starts again');
      await again.close();
    });
  });

  group('Problem 3: retry only the statements still wrong', () {
    test('credit is kept, the retry passes, history is complete', () async {
      final db = await _seed();
      addTearDown(db.close);
      final first = await recordModuleQuiz(db, moduleId: 'B', answers: {'b1': true, 'b2': true, 'b3': true});
      expect((first.correct, first.total, first.passed, first.remaining), (2, 3, false, 1));
      expect(await quizCredit(db, 'B'), {'b1', 'b3'});
      final second = await recordModuleQuiz(db, moduleId: 'B', answers: {'b2': false});
      expect((second.correct, second.passed, second.remaining), (3, true, 0), reason: 'effective score after the retry');
      expect(await completeModule(db, 'B'), isNull);

      final rows = (await db.getQuizAttempts()).where((a) => a.moduleId == 'B').toList()..sort((a, b) => a.takenAt.compareTo(b.takenAt));
      expect(rows, hasLength(2), reason: 'every attempt kept');
      expect((rows[0].correctCount, rows[1].correctCount), (2, 3));
      final r1 = (jsonDecode(rows[0].resultsJson) as List).cast<Map<String, dynamic>>();
      final r2 = (jsonDecode(rows[1].resultsJson) as List).cast<Map<String, dynamic>>();
      expect(r1.every((r) => r['shown'] == true), isTrue);
      expect({for (final r in r2) r['question_id']: (r['shown'], r['correct'], r['answer'])},
          {'b1': (false, true, null), 'b2': (true, true, false), 'b3': (false, true, null)});
      expect(await quizCredit(db, 'B'), isEmpty, reason: 'nothing left once passed');
    });

    test('a wrong retry keeps the earlier credit and asks the same statement again', () async {
      final db = await _seed();
      addTearDown(db.close);
      await recordModuleQuiz(db, moduleId: 'B', answers: {'b1': true, 'b2': true, 'b3': true});
      final again = await recordModuleQuiz(db, moduleId: 'B', answers: {'b2': true});
      expect((again.correct, again.remaining), (2, 1));
      expect(await quizCredit(db, 'B'), {'b1', 'b3'});
    });
  });

  group('Problem 3 in the reader', () {
    setUp(() {
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(const MethodChannel('flutter_tts'), (call) async => null);
    });

    Future<void> settle(WidgetTester tester) async {
      for (var i = 0; i < 6; i++) {
        await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 20)));
        await tester.pump(const Duration(milliseconds: 50));
      }
    }

    testWidgets('Try again shows only the wrong statement; passing it completes the module', (tester) async {
      final db = (await tester.runAsync(() => _seed()))!;
      addTearDown(db.close);
      final router = GoRouter(initialLocation: '/reader/B', routes: [
        GoRoute(path: '/modules', builder: (_, __) => const Scaffold(body: Text('MODULES'))),
        GoRoute(path: '/home', builder: (_, __) => const Scaffold(body: Text('HOME'))),
        GoRoute(path: '/reader/:moduleId', builder: (_, s) => ReaderScreen(moduleId: s.pathParameters['moduleId']!)),
      ]);
      await tester.pumpWidget(ProviderScope(overrides: [localDatabaseProvider.overrideWithValue(db)], child: MaterialApp.router(routerConfig: router)));
      await settle(tester);

      Future<void> answer(String statement, String choice) async {
        final card = find.ancestor(of: find.text(statement), matching: find.byType(Container)).first;
        final button = find.descendant(of: card, matching: find.widgetWithText(OutlinedButton, choice));
        await tester.ensureVisible(button);
        await tester.tap(button);
        await settle(tester);
      }

      await answer('Statement B1', 'True');
      await answer('Statement B2', 'True'); // wrong
      await answer('Statement B3', 'True');
      expect(find.textContaining('You got 2 of 3'), findsOneWidget);
      expect(find.text('1 question to retry'), findsOneWidget);

      await tester.ensureVisible(find.widgetWithText(FilledButton, 'Try again'));
      await tester.tap(find.widgetWithText(FilledButton, 'Try again'));
      await settle(tester);
      expect(find.text('Answered correctly: kept from your last try.'), findsNWidgets(2));
      final open = tester.widgetList<OutlinedButton>(find.byType(OutlinedButton)).where((b) => b.onPressed != null);
      expect(open, hasLength(2), reason: 'True and False of the one statement still wrong');

      await answer('Statement B2', 'False');
      expect(find.text('Quiz passed. Well done!'), findsOneWidget);
      // The page grows once the quiz is passed: scroll again after it has settled.
      await tester.ensureVisible(find.widgetWithText(FilledButton, 'Complete module'));
      await settle(tester);
      await tester.ensureVisible(find.widgetWithText(FilledButton, 'Complete module'));
      await tester.pump();
      await tester.tap(find.widgetWithText(FilledButton, 'Complete module'));
      await settle(tester);
      expect(find.text('HOME'), findsOneWidget, reason: 'completed straight away');
    });
  });
}
