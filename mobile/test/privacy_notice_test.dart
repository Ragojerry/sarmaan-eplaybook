import 'dart:io';

import 'package:dio/dio.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarmaan_eplaybook/db/local_database.dart';
import 'package:sarmaan_eplaybook/models/consent_text.dart';
import 'package:sarmaan_eplaybook/offline/content_sync_service.dart' show localDatabaseProvider;
import 'package:sarmaan_eplaybook/screens/consent_screen.dart';
import 'package:sarmaan_eplaybook/services/api_client.dart';
import 'package:sarmaan_eplaybook/services/auth_service.dart';
import 'package:sarmaan_eplaybook/services/settings_service.dart';

/// The consent screen carries the full privacy notice
/// (content/privacy_notice/consent_body_en.txt), folded with See more / See less.
final _notice = File('../content/privacy_notice/consent_body_en.txt').readAsStringSync().trim();

ApiClient _offlineApi() {
  final api = ApiClient();
  api.dio.interceptors.insert(0, InterceptorsWrapper(onRequest: (o, h) => h.reject(DioException(requestOptions: o))));
  return api;
}

Future<LocalDatabase> _pump(WidgetTester tester, String body) async {
  final db = LocalDatabase.forTesting(NativeDatabase.memory());
  await tester.runAsync(() => SettingsService(db).setCachedConsent([
        ConsentText(language: 'en', title: 'Before you start', body: body, usageLabel: 'Usage', buttonLabel: 'Agree and continue', version: 3),
      ]));
  await tester.pumpWidget(ProviderScope(
    overrides: [
      localDatabaseProvider.overrideWithValue(db),
      apiClientProvider.overrideWithValue(_offlineApi()),
    ],
    child: const MaterialApp(home: ConsentScreen()),
  ));
  for (var i = 0; i < 5; i++) {
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 20)));
    await tester.pump();
  }
  return db;
}

int? _bodyLines(WidgetTester tester) => tester.widget<Text>(find.byKey(const Key('consentBody'))).maxLines;

void main() {
  test('the copy built into the app is the full privacy notice', () {
    expect(kBundledConsent.body, _notice);
    expect(_notice, contains('dpo.ng@malariaconsortium.org'));
    expect(_notice, contains('18. Contact Us'));
  });

  testWidgets('the notice starts folded; See more opens it all, See less folds it again', (tester) async {
    final db = await _pump(tester, _notice);
    addTearDown(db.close);
    expect(find.text('See more'), findsOneWidget);
    expect(_bodyLines(tester), isNotNull, reason: 'folded');

    await tester.tap(find.text('See more'));
    await tester.pump();
    expect(_bodyLines(tester), isNull, reason: 'the whole notice');
    expect(find.text('See less'), findsOneWidget);
    expect(find.widgetWithText(FilledButton, 'Agree and continue'), findsOneWidget, reason: 'still reachable');
    expect(find.byType(CheckboxListTile), findsOneWidget);

    await tester.tap(find.text('See less'));
    await tester.pump();
    expect(_bodyLines(tester), isNotNull);
    expect(find.text('See more'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
    await tester.pump(const Duration(seconds: 15)); // let the (failed) fetch's timers finish
  });

  testWidgets('a short text has no See more', (tester) async {
    final db = await _pump(tester, 'This app delivers AZM training to CDDs, and nothing else here.');
    addTearDown(db.close);
    expect(find.text('See more'), findsNothing);
    expect(find.text('See less'), findsNothing);
    await tester.pumpWidget(const SizedBox());
    await tester.pump(const Duration(seconds: 15));
  });
}
