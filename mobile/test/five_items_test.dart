import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarmaan_eplaybook/db/local_database.dart';
import 'package:sarmaan_eplaybook/learning/certificate.dart';
import 'package:sarmaan_eplaybook/learning/learning_rules.dart';
import 'package:sarmaan_eplaybook/learning/learning_service.dart';
import 'package:sarmaan_eplaybook/services/api_client.dart';
import 'package:sarmaan_eplaybook/services/device_identity.dart';
import 'package:sarmaan_eplaybook/theme/brand_identity.g.dart';
import 'package:sarmaan_eplaybook/tour/app_tour.dart';
import 'package:sarmaan_eplaybook/widgets/brand_mark.dart';

import 'support/fake_server.dart' show FakeServer, fakeApi;

GeneralLearning _general({TestScore? pre, TestScore? post}) =>
    GeneralLearning(active: true, questions: 25, pre: pre, post: post, modulesTotal: 6, modulesCompleted: 6);

TestScore _post(int correct, {int? passMark}) =>
    TestScore(clientId: 'post-1', testType: 'POST', correct: correct, total: 25, takenAt: DateTime.utc(2026, 11, 13), passMark: passMark);

/// Every request answers 401 with the "deactivated" header, as the server does for a deactivated account.
class _DeactivatedServer extends FakeServer {
  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async =>
      ResponseBody.fromString('{"detail": "Your account has been deactivated. Please contact support."}', 401, headers: {
        Headers.contentTypeHeader: ['application/json'],
        'x-account-status': ['deactivated'],
      });
}

void main() {
  group('Item 1: device identity', () {
    test('a random install id, created once, plus OS and nothing personal', () async {
      final db = LocalDatabase.forTesting(NativeDatabase.memory());
      addTearDown(db.close);
      final a = await deviceInfoPayload(db);
      final b = await deviceInfoPayload(db);
      expect(a['install_id'], hasLength(32));
      expect(a['install_id'], matches(RegExp(r'^[0-9a-f]{32}$')));
      expect(b['install_id'], a['install_id'], reason: 'the same install keeps its id');
      expect(a['os'], Platform.operatingSystem);
      expect(a.keys.toSet().difference({'install_id', 'os', 'os_version', 'app_version'}), isEmpty,
          reason: 'no model, IMEI, advertising id or phone number');
    });
  });

  group('Item 2: deactivated account', () {
    test('the header is recognised, tokens are cleared and the app is told once', () async {
      final api = fakeApi(_DeactivatedServer());
      await api.saveTokens(accessToken: 'a', refreshToken: 'r');
      var told = 0;
      api.onAccountDeactivated = () => told++;
      await expectLater(api.dio.get('/sync/learning'), throwsA(isA<DioException>()));
      expect(told, 1);
      expect(await api.getAccessToken(), isNull);
      expect(await api.getRefreshToken(), isNull);
    });

    test('a refused login is recognised without signing anyone out', () async {
      final api = fakeApi(_DeactivatedServer());
      var told = 0;
      api.onAccountDeactivated = () => told++;
      try {
        await api.dio.post('/auth/login', data: {'username': 'x', 'password': 'y'});
        fail('should throw');
      } on DioException catch (e) {
        expect(ApiClient.isDeactivated(e.response), isTrue, reason: 'the sign-in screen shows its own message');
      }
      expect(told, 0);
    });
  });

  group('Item 3: General test pass marks', () {
    test('whole numbers: CDD 60% = 15 of 25, others 80% = 20 of 25', () {
      expect(defaultGeneralPassMark('CDD'), 60);
      for (final role in ['HEALTH_WORKER', 'LOGISTICIAN', 'MONITOR_SUPERVISOR', 'OTHER', null]) {
        expect(defaultGeneralPassMark(role), 80, reason: '$role');
      }
      expect(generalPasses(15, 25, 60), isTrue);
      expect(generalPasses(14, 25, 60), isFalse);
      expect(generalPasses(20, 25, 80), isTrue);
      expect(generalPasses(19, 25, 80), isFalse);
      expect(generalPasses(57, 100, 58), isFalse, reason: 'exact at the edge');
      expect(generalNeeded(25, 80), 20);
      expect(generalNeeded(25, 60), 15);
      expect(generalNeeded(3, 60), 2);
    });

    test('the certificate follows the stored mark; old attempts keep 90%', () {
      expect(hasCertificate(_general(post: _post(15, passMark: 60))), isTrue);
      expect(hasCertificate(_general(post: _post(19, passMark: 80))), isFalse);
      expect(hasCertificate(_general(post: _post(20))), isFalse, reason: 'no stored mark: 90% as before');
      expect(hasCertificate(_general(post: _post(23))), isTrue);
      expect(_post(21, passMark: 80).passed, isTrue);
      expect(_post(21).passed, isNull, reason: 'no verdict without a stored mark');
    });

    test('each attempt stores its mark; the server mark replaces it; settings never re-grade', () async {
      final db = LocalDatabase.forTesting(NativeDatabase.memory());
      addTearDown(db.close);
      db.setActiveUser('u1', learnerRole: 'CDD');
      expect(await currentGeneralPassMark(db), 60, reason: 'default before the first sync');
      await db.setSetting(kGeneralPassMarkKey, '70');
      expect(await currentGeneralPassMark(db), 70);
      await db.insertGeneralAttempt(clientId: 'pre-1', testType: 'PRE', correct: 17, total: 25, answersJson: '[]', passMark: 70);
      await db.setSetting(kGeneralPassMarkKey, '90');
      final row = (await db.getGeneralAttempts()).single;
      expect(generalScoreOf(row).passMark, 70, reason: 'a later change never alters this result');
      expect(generalScoreOf(row).passed, isFalse);
      await db.restoreGeneralAttemptFromServer(clientId: 'pre-1', testType: 'PRE', correct: 17, total: 25,
          takenAt: DateTime.utc(2026, 11, 13), passMark: 60);
      expect((await db.getGeneralAttempts()).single.passMark, 60, reason: 'the server stored mark counts');
    });

    test('upgrading the database from schema 11 keeps attempts and adds an empty mark', () async {
      final dir = await Directory.systemTemp.createTemp('sarmaan-db-');
      addTearDown(() => dir.delete(recursive: true));
      final file = File('${dir.path}/app.sqlite');
      final old = LocalDatabase.forTesting(NativeDatabase(file));
      old.setActiveUser('u1');
      await old.insertGeneralAttempt(clientId: 'old-pre', testType: 'PRE', correct: 12, total: 25, answersJson: '[]');
      await old.customStatement('ALTER TABLE local_general_attempts DROP COLUMN pass_mark');
      await old.customStatement('PRAGMA user_version = 11');
      await old.close();
      final upgraded = LocalDatabase.forTesting(NativeDatabase(file));
      addTearDown(upgraded.close);
      upgraded.setActiveUser('u1');
      final row = (await upgraded.getGeneralAttempts()).single;
      expect((row.clientId, row.correctCount, row.passMark), ('old-pre', 12, null));
    });
  });

  group('Item 4: tour', () {
    test('only areas this learner has', () {
      final without = tourSteps(hasTools: false, hasSupport: false);
      expect(without.map((s) => s.title), ['Home', 'Modules', 'Videos', 'Ask', 'About']);
      expect(without[3].body, isNot(contains('Need help from a person')));
      final all = tourSteps(hasTools: true, hasSupport: true);
      expect(all.map((s) => s.title), ['Home', 'Modules', 'Videos', 'Ask', 'Tools', 'About']);
      expect(all[3].body, contains('Need help from a person'));
    });

    test('the seen flag is per account on this phone', () async {
      final db = LocalDatabase.forTesting(NativeDatabase.memory());
      addTearDown(db.close);
      expect(await tourSeen(db, 'u1'), isFalse);
      await markTourSeen(db, 'u1');
      expect(await tourSeen(db, 'u1'), isTrue);
      expect(await tourSeen(db, 'u2'), isFalse, reason: 'another account on the same phone still sees it once');
    });

    testWidgets('Skip on every step, Back/Next, progress, large buttons', (tester) async {
      final steps = tourSteps(hasTools: false, hasSupport: false);
      await tester.pumpWidget(MaterialApp(home: Scaffold(body: Builder(builder: (context) {
        return TextButton(
          onPressed: () => showDialog<void>(context: context, builder: (_) => AppTourDialog(steps: steps)),
          child: const Text('open'),
        );
      }))));
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();
      expect(find.text('1 of 5'), findsOneWidget);
      expect(find.text('Skip'), findsOneWidget);
      expect(find.text('Back'), findsNothing);
      await tester.tap(find.text('Next'));
      await tester.pumpAndSettle();
      expect(find.text('2 of 5'), findsOneWidget);
      expect(find.text('Modules'), findsOneWidget);
      expect(find.text('Skip'), findsOneWidget);
      for (final label in ['Skip', 'Back', 'Next']) {
        expect(tester.getSize(find.ancestor(of: find.text(label), matching: find.byWidgetPredicate((w) => w is ButtonStyleButton))).height,
            greaterThanOrEqualTo(44), reason: label);
      }
      await tester.tap(find.text('Back'));
      await tester.pumpAndSettle();
      expect(find.text('1 of 5'), findsOneWidget);
      await tester.tap(find.text('Skip'));
      await tester.pumpAndSettle();
      expect(find.byType(AppTourDialog), findsNothing, reason: 'skipping closes the tour at once');
    });
  });

  group('Item 5: brand', () {
    test('one title for the whole app', () {
      expect(BrandIdentity.title, 'SARMAAN II Multi-lingual e-Playbook');
      expect(BrandIdentity.shortTitle, 'SARMAAN II', reason: 'approved short form (sidebar, launcher label)');
      expect(BrandIdentity.logoAsset, 'assets/brand/sarmaan_ii_project.png');
    });

    testWidgets('the title wraps on a small phone instead of overflowing', (tester) async {
      tester.view.physicalSize = const Size(320, 640);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(const MaterialApp(home: Scaffold(body: Padding(padding: EdgeInsets.all(24), child: BrandTitle()))));
      expect(find.text(BrandIdentity.title), findsOneWidget);
      expect(tester.takeException(), isNull);
      final lineHeight = tester.getSize(find.text(BrandIdentity.title)).height;
      expect(lineHeight, greaterThan(40), reason: 'two or more lines at 320 px');
    });
  });
}
