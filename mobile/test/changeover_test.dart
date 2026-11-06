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
import 'package:sarmaan_eplaybook/screens/quiz_screen.dart';
import 'package:sarmaan_eplaybook/screens/reader_screen.dart';
import 'package:sarmaan_eplaybook/sync/release_installer.dart';

import 'support/fake_server.dart';

/// The curriculum changeover on a phone: M1-M6 are archived on the server and a
/// new release holds only the HFW modules. Uses only APIs that exist in app
/// 0.1.9 too, so this file also runs against the 0.1.9 code.
void main() {
  late Directory docs;
  late FakeServer server;
  late LocalDatabase db;
  late ReleaseInstaller installer;

  setUp(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(const MethodChannel('flutter_tts'), (call) async => null);
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

  final legacyModules = [
    module('m1', 'M1', 1, imageId: 'img-old-1'),
    module('m2', 'M2', 2, imageId: 'img-old-2'),
  ];
  final hfwModules = [
    module('h01', 'HFW-01', 1010, imageId: 'img-new-1'),
    module('h02', 'HFW-02', 1020),
    module('h03', 'HFW-03', 1080, audience: 'ROLE_SPECIFIC', roles: ['CDD'], imageId: 'img-new-3'),
    module('h16', 'HFW-16', 1170, audience: 'ROLE_SPECIFIC', roles: ['LOGISTICIAN']),
  ];

  Future<void> learnerWorkedOnOldModules() async {
    final now = DateTime(2026, 10, 1, 9);
    await db.into(db.localProgress).insert(LocalProgressCompanion.insert(
          moduleId: 'm1', progressPercent: const Value(100), completed: const Value(true), userId: const Value('learner-1'),
          completedAt: Value(now), readingCompletedAt: Value(now), lastOpenedAt: Value(now), synced: const Value(true)));
    await db.into(db.localProgress).insert(LocalProgressCompanion.insert(
          moduleId: 'm2', progressPercent: const Value(40), userId: const Value('learner-1'), lastOpenedAt: Value(now),
          synced: const Value(true)));
  }

  Future<List<String>> codes() async => [for (final m in await db.getAllModules()) m.moduleCode];

  test('online phone: archived modules and their cached pictures are removed at the next sync', () async {
    await installer.install(publish(server, 'R-LEGACY', legacyModules));
    await learnerWorkedOnOldModules();
    final oldFiles = [for (final m in await db.getAllMedia()) m.localPath!];
    expect(await codes(), ['M1', 'M2']);
    expect(oldFiles.every((p) => File(p).existsSync()), isTrue);

    await installer.install(publish(server, 'R-HFW', hfwModules, curriculum: 'hfw-2026'));

    expect(await codes(), ['HFW-01', 'HFW-02', 'HFW-03'], reason: 'general first, then the CDD module; no M1-M6');
    expect(await db.getSectionsForModule('m1'), isEmpty);
    expect((await db.getAllMedia()).map((m) => m.id).toSet(), {'img-new-1', 'img-new-3'});
    expect(oldFiles.any((p) => File(p).existsSync()), isFalse, reason: 'cached files of archived modules are released');
    // the learner's old records stay on the phone, but nothing old counts toward the new curriculum
    expect((await db.getProgressForModule('m1'))!.completed, isTrue);
    final learning = await loadLearning(db);
    expect(learning.completedCount, 0);
    expect(learning.blockerOf('h02')?.moduleCode, 'HFW-01', reason: 'the unlock chain starts at the first general module');
  });

  test('phone offline through the changeover keeps the old content until it syncs', () async {
    await installer.install(publish(server, 'R-LEGACY', legacyModules));
    await learnerWorkedOnOldModules();
    publish(server, 'R-HFW', hfwModules, curriculum: 'hfw-2026'); // the server moved on; this phone has not synced
    expect(await codes(), ['M1', 'M2'], reason: 'offline: still the old modules, fully usable');
    expect((await db.getAllMedia()).every((m) => File(m.localPath!).existsSync()), isTrue);
    // on reconnecting, the same install happens and the old content goes
    await installer.install(publish(server, 'R-HFW', hfwModules, curriculum: 'hfw-2026'));
    expect(await codes(), ['HFW-01', 'HFW-02', 'HFW-03']);
  });

  group('tapping a completed or archived module never freezes', () {
    Widget app(LocalDatabase db, String target) {
      final router = GoRouter(initialLocation: '/modules', routes: [
        GoRoute(
          path: '/modules',
          builder: (context, state) => Scaffold(
            body: Center(child: TextButton(onPressed: () => context.push(target), child: const Text('Open'))),
          ),
        ),
        GoRoute(path: '/reader/:moduleId', builder: (context, state) => ReaderScreen(moduleId: state.pathParameters['moduleId']!)),
        GoRoute(
          path: '/quiz/:moduleId',
          builder: (context, state) => QuizScreen(moduleId: state.pathParameters['moduleId']!, testType: 'POST'),
        ),
      ]);
      return ProviderScope(overrides: [localDatabaseProvider.overrideWithValue(db)], child: MaterialApp.router(routerConfig: router));
    }

    Future<void> settle(WidgetTester tester) async {
      for (var i = 0; i < 6; i++) {
        await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 20)));
        await tester.pump(const Duration(milliseconds: 50));
      }
    }

    for (final target in ['/reader/m1', '/quiz/m1']) {
      testWidgets('archived module M1 ($target): a message, no freeze, back works', (tester) async {
        await tester.runAsync(() async {
          await installer.install(publish(server, 'R-LEGACY', legacyModules));
          await learnerWorkedOnOldModules();
          await installer.install(publish(server, 'R-HFW', hfwModules, curriculum: 'hfw-2026'));
        });
        await tester.pumpWidget(app(db, target));
        await settle(tester);
        for (var i = 0; i < 5; i++) {
          await tester.tap(find.text('Open'), warnIfMissed: false);
          await tester.pump();
        }
        await settle(tester);
        expect(tester.takeException(), isNull);
        expect(find.textContaining('Lesson of M1'), findsNothing, reason: 'archived content is gone');
        expect(find.textContaining(RegExp(r'not (part of|available)')), findsWidgets);
        // every tap opened a screen (the reader's back goes straight to the list; the quiz pops one at a time)
        for (var i = 0; i < 6 && find.text('Open').evaluate().isEmpty; i++) {
          await tester.tap(find.byType(BackButton).first);
          await settle(tester);
        }
        expect(tester.takeException(), isNull);
        expect(find.text('Open'), findsOneWidget, reason: 'back navigation works');
        await tester.pumpWidget(const SizedBox());
      });
    }
  });
}
