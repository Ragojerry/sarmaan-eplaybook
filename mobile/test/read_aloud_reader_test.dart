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
import 'package:sarmaan_eplaybook/services/read_aloud_service.dart';

import 'read_aloud_service_test.dart' show FakeEngine, FakeFocus;

/// Read aloud in the real reader: shown for English only, reads the module on
/// Play, and stops when the learner leaves the reader. Offline, in-memory database.
void main() {
  setUp(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(const MethodChannel('flutter_tts'), (call) async => null);
  });

  Future<LocalDatabase> seed(String language) async {
    final db = LocalDatabase.forTesting(NativeDatabase.memory());
    db.setActiveUser('learner-1', learnerRole: 'CDD');
    await db.setSetting('selected_language_code', language);
    final now = DateTime(2026, 11, 14, 9);
    await db.into(db.cachedModules).insert(CachedModulesCompanion.insert(
          id: 'A', moduleCode: 'M1', moduleNumber: 1, title: 'Module one', status: 'PUBLISHED', sortOrder: 1, cachedAt: now));
    for (final code in ['en', 'ha']) {
      await db.into(db.cachedTranslations).insert(CachedTranslationsCompanion.insert(
            id: 't-$code', moduleId: 'A', languageId: '$code-id', languageCode: code, title: 'Module one', status: 'PUBLISHED'));
    }
    for (var i = 0; i < 3; i++) {
      await db.into(db.cachedSections).insert(CachedSectionsCompanion.insert(
            id: 's$i', moduleId: 'A', sectionNumber: i, contentType: 'TEXT', contentJson: '{"text": "Lesson text $i about AZM"}', sortOrder: i));
    }
    await db.into(db.localProgress).insert(LocalProgressCompanion.insert(
          moduleId: 'A', progressPercent: const Value(100), completed: const Value(true), userId: const Value('learner-1'),
          lastOpenedAt: Value(now), completedAt: Value(now), readingCompletedAt: Value(now), synced: const Value(true)));
    return db;
  }

  Future<void> settle(WidgetTester tester) async {
    for (var i = 0; i < 6; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 20)));
      await tester.pump(const Duration(milliseconds: 50));
    }
  }

  Widget app(LocalDatabase db, ReadAloudService service) {
    final router = GoRouter(initialLocation: '/modules', routes: [
      GoRoute(
        path: '/modules',
        builder: (context, state) => Scaffold(
          body: Center(child: TextButton(onPressed: () => context.push('/reader/A'), child: const Text('Open M1'))),
        ),
      ),
      GoRoute(path: '/reader/:moduleId', builder: (context, state) => ReaderScreen(moduleId: state.pathParameters['moduleId']!)),
    ]);
    return ProviderScope(
      overrides: [
        localDatabaseProvider.overrideWithValue(db),
        readAloudServiceProvider.overrideWith((ref) => service),
      ],
      child: MaterialApp.router(routerConfig: router),
    );
  }

  const enVoice = {'name': 'en-gb-x-gba-local', 'locale': 'en-GB', 'network_required': '0'};

  testWidgets('English: the Read aloud bar reads the module, and leaving the reader stops it', (tester) async {
    final db = (await tester.runAsync(() => seed('en')))!;
    final engine = FakeEngine([enVoice])..hold = true;
    final service = ReadAloudService(engine: engine, focus: FakeFocus(), db: db);
    await tester.pumpWidget(app(db, service));
    await settle(tester);
    await tester.tap(find.text('Open M1'));
    await settle(tester);
    expect(find.byKey(const Key('readAloudBar')), findsOneWidget);
    expect(find.text('Read aloud'), findsOneWidget);

    await tester.runAsync(() async {
      await tester.tap(find.byTooltip('Play'));
      await Future<void>.delayed(const Duration(milliseconds: 100));
    });
    await settle(tester);
    expect(engine.spoken.first, 'Module one.');
    expect(service.status, ReadAloudStatus.reading);
    expect(find.byTooltip('Pause'), findsOneWidget);
    expect(find.text('Speed 1x'), findsOneWidget);

    await tester.tap(find.byType(BackButton));
    await settle(tester);
    await tester.pump(const Duration(seconds: 1)); // the page transition
    await settle(tester);
    expect(tester.takeException(), isNull, reason: 'stopping must not change providers while the screen is torn down');
    expect(service.status, ReadAloudStatus.idle, reason: 'leaving the reader stops reading');

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(db.close);
  });

  testWidgets('Hausa selected: no Read aloud at all', (tester) async {
    final db = (await tester.runAsync(() => seed('ha')))!;
    final service = ReadAloudService(engine: FakeEngine([enVoice]), focus: FakeFocus(), db: db);
    await tester.pumpWidget(app(db, service));
    await settle(tester);
    await tester.tap(find.text('Open M1'));
    await settle(tester);
    expect(find.text('Lesson text 0 about AZM'), findsOneWidget, reason: 'the reader is open');
    expect(find.byKey(const Key('readAloudBar')), findsNothing);
    expect(find.text('Read aloud'), findsNothing);

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(db.close);
  });
}
