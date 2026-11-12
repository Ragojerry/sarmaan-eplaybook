import 'dart:io';

import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarmaan_eplaybook/db/local_database.dart';
import 'package:sarmaan_eplaybook/l10n/l10n.dart';
import 'package:sarmaan_eplaybook/learning/curriculum_notice.dart';
import 'package:sarmaan_eplaybook/offline/content_sync_service.dart';
import 'package:sarmaan_eplaybook/screens/update_required_screen.dart';
import 'package:sarmaan_eplaybook/sync/release_installer.dart';

import 'support/fake_server.dart';

/// App 0.1.10: the one-time "training updated" notice and version gating.
void main() {
  late Directory docs;
  late FakeServer server;
  late LocalDatabase db;
  late ReleaseInstaller installer;

  setUp(() async {
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

  final legacy = [module('m1', 'M1', 1)];
  final hfw = [module('h01', 'HFW-01', 1010), module('h03', 'HFW-03', 1080, audience: 'ROLE_SPECIFIC', roles: ['CDD'])];

  group('one-time notice', () {
    test('queued when the installed curriculum changes from the old modules to the new', () async {
      await installer.install(publish(server, 'R1', legacy));
      expect(await hasPendingTrainingNotice(db), isFalse);
      await installer.install(publish(server, 'R2', hfw, curriculum: 'hfw-2026'));
      expect(await hasPendingTrainingNotice(db), isTrue);
    });

    test('an app updated from 0.1.9 (content cached, nothing recorded) still gets it', () async {
      await installer.install(publish(server, 'R1', legacy));
      await db.setSetting(kInstalledCurriculumKey, ''); // what a 0.1.9 phone has: no record
      await installer.install(publish(server, 'R2', hfw, curriculum: 'hfw-2026'));
      expect(await hasPendingTrainingNotice(db), isTrue);
    });

    test('not shown on a first install, a re-install of the same curriculum, or a rollback', () async {
      await installer.install(publish(server, 'R2', hfw, curriculum: 'hfw-2026'));
      expect(await hasPendingTrainingNotice(db), isFalse, reason: 'new phone: nothing changed for this learner');
      await installer.install(publish(server, 'R3', hfw, curriculum: 'hfw-2026'));
      expect(await hasPendingTrainingNotice(db), isFalse);
      await installer.install(publish(server, 'R4', legacy, curriculum: 'legacy'));
      expect(await hasPendingTrainingNotice(db), isFalse, reason: 'rollback to the old modules: no "start the new modules"');
    });

    // The text comes from the interface-text registry: English built in, other
    // languages only once a translation is published (fake "[zz]" text here: this
    // checks the plumbing, real text comes from translators).
    for (final (lang, published, text, button) in [
      ('en', const <String, String>{}, 'The training has been updated. Start the new modules.', 'OK'),
      ('zz', const {'notice.trainingUpdated': '[zz] training updated', 'common.ok': '[zz] OK'}, '[zz] training updated', '[zz] OK'),
      ('zz', const <String, String>{}, 'The training has been updated. Start the new modules.', 'OK'),
    ]) {
      testWidgets('shows once, in the learner\'s language ($lang, ${published.isEmpty ? 'English fallback' : 'published'})',
          (tester) async {
        L10n.instance.apply(lang, published);
        addTearDown(() => L10n.instance.apply('en', const {}));
        await tester.runAsync(() async {
          await db.setSetting('selected_language_code', lang);
          await db.setSetting(kPendingTrainingNoticeKey, 'hfw-2026');
        });
        late BuildContext ctx;
        await tester.pumpWidget(MaterialApp(home: Builder(builder: (c) {
          ctx = c;
          return const Scaffold();
        })));
        final first = showTrainingNoticeIfPending(ctx, db); // not awaited: it waits for the tap
        for (var i = 0; i < 5; i++) {
          await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 20)));
          await tester.pump();
        }
        expect(find.text(text), findsOneWidget);
        await tester.tap(find.text(button));
        for (var i = 0; i < 5; i++) {
          await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 20)));
          await tester.pump();
        }
        expect(await tester.runAsync(() => first), isTrue);
        expect(find.text(text), findsNothing);
        expect(await tester.runAsync(() => hasPendingTrainingNotice(db)), isFalse);
        expect(await tester.runAsync(() => showTrainingNoticeIfPending(ctx, db)), isFalse, reason: 'one time only');
      });
    }
  });

  group('version gating', () {
    test('version comparison', () {
      expect(isOlderVersion('0.1.9', '0.1.10'), isTrue);
      expect(isOlderVersion('0.1.9+10', '0.1.10'), isTrue);
      expect(isOlderVersion('0.1.10', '0.1.10'), isFalse);
      expect(isOlderVersion('0.2.0', '0.1.10'), isFalse);
      expect(isOlderVersion('1.0', '0.9.9'), isFalse);
    });

    test('update required only when the server sets a higher minimum', () async {
      expect(await updateRequired(db, appVersion: () async => '0.1.9'), isFalse, reason: 'no minimum set');
      await db.setSetting(kMinAppVersionKey, '0.1.10');
      expect(await updateRequired(db, appVersion: () async => '0.1.9'), isTrue);
      expect(await updateRequired(db, appVersion: () async => '0.1.10'), isFalse);
      await db.setSetting(kMinAppVersionKey, '');
      expect(await updateRequired(db, appVersion: () async => '0.1.9'), isFalse);
    });

    testWidgets('the update screen says the training was updated', (tester) async {
      await tester.pumpWidget(ProviderScope(
        overrides: [localDatabaseProvider.overrideWithValue(db)],
        child: const MaterialApp(home: UpdateRequiredScreen()),
      ));
      for (var i = 0; i < 3; i++) {
        await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 20)));
        await tester.pump();
      }
      expect(find.text('Training updated, please update the app.'), findsOneWidget);
      expect(find.text('Check again'), findsOneWidget);
      await tester.pumpWidget(const SizedBox());
    });
  });
}
