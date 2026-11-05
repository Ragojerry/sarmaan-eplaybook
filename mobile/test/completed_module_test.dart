import 'package:drift/drift.dart' show Value;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:sarmaan_eplaybook/db/local_database.dart';
import 'package:sarmaan_eplaybook/offline/content_sync_service.dart';
import 'package:sarmaan_eplaybook/screens/reader_screen.dart';

/// Regression: opening a module that is already Complete froze the app.
/// Runs with no network at all (the app is offline-first), against an
/// in-memory database and the real reader screen and router.
void main() {
  setUp(() {
    // flutter_tts has no platform side in widget tests.
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(const MethodChannel('flutter_tts'), (call) async => null);
  });

  Future<LocalDatabase> seed({required bool withPreTest}) async {
    final db = LocalDatabase.forTesting(NativeDatabase.memory());
    db.setActiveUser('learner-1', learnerRole: 'CDD');
    final now = DateTime(2026, 11, 4, 9);
    await db.into(db.cachedModules).insert(CachedModulesCompanion.insert(
          id: 'A', moduleCode: 'M1', moduleNumber: 1, title: 'Module one', status: 'PUBLISHED', sortOrder: 1, cachedAt: now));
    await db.into(db.cachedTranslations).insert(CachedTranslationsCompanion.insert(
          id: 't1', moduleId: 'A', languageId: 'en-id', languageCode: 'en', title: 'Module one', status: 'PUBLISHED'));
    for (var i = 0; i < 3; i++) {
      await db.into(db.cachedSections).insert(CachedSectionsCompanion.insert(
            id: 's$i', moduleId: 'A', sectionNumber: i, contentType: 'TEXT', contentJson: '{"text": "Lesson text $i"}', sortOrder: i));
    }
    await db.into(db.cachedQuizQuestions).insert(CachedQuizQuestionsCompanion.insert(
          id: 'q1', moduleId: 'A', questionType: 'TRUE_FALSE', prompt: 'Q?', contentJson: '{"correct": true}', sortOrder: 1));
    if (withPreTest) {
      for (final (type, correct, minute) in [('PRE', 5, 1), ('POST', 10, 3)]) {
        await db.into(db.localQuizAttempts).insert(LocalQuizAttemptsCompanion.insert(
              userId: const Value('learner-1'), moduleId: 'A', clientId: '$type-1', correctCount: correct, totalCount: 10,
              scorePercent: correct * 10, passed: correct >= 9, resultsJson: '[]', takenAt: now.add(Duration(minutes: minute)),
              testType: Value(type), synced: const Value(true)));
      }
    }
    // Completed - for the legacy case, before pre/post tests existed (no pre-test).
    await db.into(db.localProgress).insert(LocalProgressCompanion.insert(
          moduleId: 'A', progressPercent: const Value(100), completed: const Value(true), userId: const Value('learner-1'),
          lastOpenedAt: Value(now), completedAt: Value(now), readingCompletedAt: Value(now), synced: const Value(true)));
    return db;
  }

  Widget app(LocalDatabase db) {
    final router = GoRouter(initialLocation: '/modules', routes: [
      GoRoute(
        path: '/modules',
        builder: (context, state) => Scaffold(
          body: Center(child: TextButton(onPressed: () => context.push('/reader/A'), child: const Text('Open M1'))),
        ),
      ),
      GoRoute(path: '/reader/:moduleId', builder: (context, state) => ReaderScreen(moduleId: state.pathParameters['moduleId']!)),
      GoRoute(path: '/quiz/:moduleId', builder: (context, state) => const Scaffold(body: Text('QUIZ'))),
    ]);
    return ProviderScope(
      overrides: [localDatabaseProvider.overrideWithValue(db)],
      child: MaterialApp.router(routerConfig: router),
    );
  }

  /// Lets the database futures finish (they run outside the fake clock).
  Future<void> settle(WidgetTester tester) async {
    for (var i = 0; i < 6; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 20)));
      await tester.pump(const Duration(milliseconds: 50));
    }
  }

  for (final withPreTest in [false, true]) {
    testWidgets('a completed module (${withPreTest ? 'via pre/post tests' : 'legacy, no pre-test'}) opens in review mode, '
        'survives repeated taps and goes back', (tester) async {
      final db = await tester.runAsync(() => seed(withPreTest: withPreTest));
      await tester.pumpWidget(app(db!));
      await settle(tester);

      for (var i = 0; i < 5; i++) {
        await tester.tap(find.text('Open M1'), warnIfMissed: false);
        await tester.pump();
      }
      await settle(tester);
      expect(tester.takeException(), isNull);
      expect(find.text('Lesson text 0'), findsOneWidget, reason: 'the lessons are readable');
      expect(find.text('Module completed'), findsOneWidget);
      expect(find.textContaining('post-test again'), findsNothing, reason: 'no re-submitting a completed module');

      for (var i = 0; i < 5; i++) {
        await tester.tap(find.text('Lesson text 1'));
        await tester.pump();
      }
      await tester.drag(find.byType(ListView), const Offset(0, -400));
      await settle(tester);
      expect(tester.takeException(), isNull);

      await tester.tap(find.byType(BackButton));
      await settle(tester);
      expect(find.text('Open M1'), findsOneWidget, reason: 'back navigation works');
      final progress = await tester.runAsync(() => db.getProgressForModule('A'));
      expect(progress!.completed, isTrue);
      expect(progress.progressPercent, 100, reason: 'status and score unchanged');

      await tester.pumpWidget(const SizedBox());
      await tester.runAsync(db.close);
    });
  }
}
