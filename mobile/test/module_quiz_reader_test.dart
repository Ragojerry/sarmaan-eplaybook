import 'dart:convert';

import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:sarmaan_eplaybook/db/local_database.dart';
import 'package:sarmaan_eplaybook/offline/content_sync_service.dart';
import 'package:sarmaan_eplaybook/screens/reader_screen.dart';

/// The inline True/False quiz in the real reader: a wrong answer shows the right
/// one and "Try again" (all statements again); passing, the time indicator and
/// "Complete module". Offline, against an in-memory database.
void main() {
  setUp(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(const MethodChannel('flutter_tts'), (call) async => null);
  });

  Future<LocalDatabase> seed({required int minSeconds}) async {
    final db = LocalDatabase.forTesting(NativeDatabase.memory());
    db.setActiveUser('learner-1', learnerRole: 'CDD');
    final now = DateTime(2026, 11, 10, 9);
    await db.into(db.cachedModules).insert(CachedModulesCompanion.insert(
          id: 'A', moduleCode: 'CDD-01', moduleNumber: 201, title: 'Module one', status: 'PUBLISHED', sortOrder: 1, cachedAt: now));
    await db.into(db.cachedTranslations).insert(CachedTranslationsCompanion.insert(
          id: 't1', moduleId: 'A', languageId: 'en-id', languageCode: 'en', title: 'Module one', status: 'PUBLISHED'));
    await db.into(db.cachedSections).insert(CachedSectionsCompanion.insert(
          id: 's0', moduleId: 'A', sectionNumber: 1, contentType: 'TEXT', contentJson: '{"text": "AZM is given door to door."}', sortOrder: 1));
    await db.into(db.cachedSections).insert(CachedSectionsCompanion.insert(
          id: 'tf0',
          moduleId: 'A',
          sectionNumber: 2,
          contentType: 'TRUE_FALSE',
          contentJson: jsonEncode({'statement': 'AZM is delivered door to door', 'answer': true, 'audience': 'CDD'}),
          sortOrder: 2));
    await db.setModuleMinSeconds(minSeconds);
    return db;
  }

  Widget app(LocalDatabase db) {
    final router = GoRouter(initialLocation: '/reader/A', routes: [
      GoRoute(path: '/modules', builder: (context, state) => const Scaffold(body: Text('MODULES'))),
      GoRoute(path: '/home', builder: (context, state) => const Scaffold(body: Text('HOME'))),
      GoRoute(path: '/reader/:moduleId', builder: (context, state) => ReaderScreen(moduleId: state.pathParameters['moduleId']!)),
    ]);
    return ProviderScope(overrides: [localDatabaseProvider.overrideWithValue(db)], child: MaterialApp.router(routerConfig: router));
  }

  Future<void> settle(WidgetTester tester) async {
    for (var i = 0; i < 6; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 20)));
      await tester.pump(const Duration(milliseconds: 50));
    }
  }

  testWidgets('wrong answer, try again, pass, then complete the module', (tester) async {
    final db = (await tester.runAsync(() => seed(minSeconds: 0)))!;
    await tester.pumpWidget(app(db));
    await settle(tester);
    expect(find.text('AZM is delivered door to door'), findsOneWidget);
    expect(find.textContaining('Time in this module: 0:00 / 0:00'), findsOneWidget);

    await tester.tap(find.widgetWithText(OutlinedButton, 'False'));
    await settle(tester);
    expect(find.text('Not quite. The answer is True.'), findsOneWidget);
    expect(find.textContaining('You got 0 of 1'), findsOneWidget);

    await tester.ensureVisible(find.widgetWithText(FilledButton, 'Try again'));
    await tester.tap(find.widgetWithText(FilledButton, 'Try again'));
    await settle(tester);
    await tester.tap(find.widgetWithText(OutlinedButton, 'True'));
    await settle(tester);
    expect(find.text('Quiz passed. Well done!'), findsOneWidget);

    await tester.ensureVisible(find.widgetWithText(FilledButton, 'Complete module'));
    await tester.tap(find.widgetWithText(FilledButton, 'Complete module'));
    await settle(tester);
    expect(find.text('HOME'), findsOneWidget, reason: 'completing a module goes straight to Home');
    expect(find.text('Module completed. It will sync to your account when online.'), findsOneWidget);
    final progress = await tester.runAsync(() => db.getProgressForModule('A'));
    expect(progress!.completed, isTrue);
    final attempts = await tester.runAsync(db.getQuizAttempts);
    expect([for (final a in attempts!) '${a.testType} ${a.correctCount}/${a.totalCount}'], ['MODULE_QUIZ 0/1', 'MODULE_QUIZ 1/1']);

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(db.close);
  });

  testWidgets('finishing early explains how much time is left; the time indicator counts', (tester) async {
    final db = (await tester.runAsync(() => seed(minSeconds: 180)))!;
    await tester.pumpWidget(app(db));
    await settle(tester);
    await tester.tap(find.widgetWithText(OutlinedButton, 'True'));
    await settle(tester);
    expect(find.textContaining('Time in this module:'), findsOneWidget);
    expect(find.textContaining('/ 3:00'), findsOneWidget);

    await tester.ensureVisible(find.widgetWithText(FilledButton, 'Complete module'));
    await tester.tap(find.widgetWithText(FilledButton, 'Complete module'));
    await settle(tester);
    expect(find.textContaining('Please spend at least 3:00 in this module.'), findsOneWidget);
    final progress = await tester.runAsync(() => db.getProgressForModule('A'));
    expect(progress!.completed, isFalse, reason: 'reading and the quiz are never blocked; only completing is');

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(db.close);
  });
}
