import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarmaan_eplaybook/db/local_database.dart';
import 'package:sarmaan_eplaybook/l10n/app_strings_en.g.dart';
import 'package:sarmaan_eplaybook/l10n/app_strings_service.dart';
import 'package:sarmaan_eplaybook/l10n/l10n.dart';
import 'package:sarmaan_eplaybook/learning/learning_rules.dart';
import 'package:sarmaan_eplaybook/screens/modules_screen.dart' show GeneralTestCard;
import 'package:sarmaan_eplaybook/services/api_client.dart';
import 'package:sarmaan_eplaybook/widgets/app_bottom_nav.dart';

/// Interface text: English built in, published translations replace it string by
/// string, and anything missing or unsafe falls back to English. Uses the fake
/// language "zz" and "[zz]" text: this checks the plumbing only.
void main() {
  tearDown(() => L10n.instance.apply('en', const {}));

  group('lookup and fallback', () {
    test('English is built in and used by default', () {
      expect(L10n.t('nav.home'), 'Home');
      expect(L10n.t('home.title'), 'Welcome to SARMAAN II Training Session');
    });

    test('a published translation replaces English; missing keys fall back to English', () {
      L10n.instance.apply('zz', {'nav.home': '[zz] Home'});
      expect(L10n.t('nav.home'), '[zz] Home');
      expect(L10n.t('nav.modules'), 'Modules', reason: 'not translated: English');
    });

    test('an empty or blank translation never shows: English instead', () {
      L10n.instance.apply('zz', {'nav.home': '', 'nav.modules': '   '});
      expect(L10n.t('nav.home'), 'Home');
      expect(L10n.t('nav.modules'), 'Modules');
    });

    test('English mode ignores any stored strings', () {
      L10n.instance.apply('en', {'nav.home': '[zz] Home'});
      expect(L10n.t('nav.home'), 'Home');
    });

    test('every English string is non-empty, so a key or blank can never be shown', () {
      for (final e in kEnglishStrings.entries) {
        expect(e.value.trim(), isNotEmpty, reason: e.key);
      }
    });
  });

  group('placeholders', () {
    test('filled from the arguments, in English and in a translation', () {
      expect(L10n.t('modules.noMatches', {'query': 'muac'}), 'No matches for "muac".');
      L10n.instance.apply('zz', {'modules.noMatches': '[zz] "{query}" babu'});
      expect(L10n.t('modules.noMatches', {'query': 'muac'}), '[zz] "muac" babu');
    });

    test('a translation with an unknown placeholder is not shown (English instead)', () {
      L10n.instance.apply('zz', {'modules.noMatches': '[zz] {qurey}'});
      expect(L10n.t('modules.noMatches', {'query': 'muac'}), 'No matches for "muac".');
    });

    test('a translation may leave a placeholder out (word order differs by language)', () {
      L10n.instance.apply('zz', {'reader.goTo': '[zz] go'});
      expect(L10n.t('reader.goTo', {'code': 'M2'}), '[zz] go');
    });
  });

  group('plurals', () {
    test('English picks one/other', () {
      expect(L10n.n('home.sectionCount', 1), '1 section');
      expect(L10n.n('home.sectionCount', 0), '0 sections');
      expect(L10n.n('home.sectionCount', 12), '12 sections');
    });

    test('Fulfulde treats 0 and 1 as singular; Hausa and Kanuri only 1', () {
      expect(L10n.pluralFormOf('ff', 0), 'one');
      expect(L10n.pluralFormOf('ff', 1), 'one');
      expect(L10n.pluralFormOf('ff', 2), 'other');
      expect(L10n.pluralFormOf('ha', 0), 'other');
      expect(L10n.pluralFormOf('ha', 1), 'one');
      expect(L10n.pluralFormOf('kr', 3), 'other');
    });

    test('a translated plural uses its own forms', () {
      L10n.instance.apply('zz', {'home.sectionCount': '[zz] {count} many', 'home.sectionCount#one': '[zz] {count} one'});
      expect(L10n.n('home.sectionCount', 1), '[zz] 1 one');
      expect(L10n.n('home.sectionCount', 5), '[zz] 5 many');
    });
  });

  group('widgets', () {
    testWidgets('screens re-render in the new language at once', (tester) async {
      await tester.pumpWidget(MaterialApp(
        builder: (context, child) => L10nScope(child: child!),
        home: Builder(builder: (context) => Text(context.t('nav.home'))),
      ));
      expect(find.text('Home'), findsOneWidget);
      L10n.instance.apply('zz', {'nav.home': '[zz] Home'});
      await tester.pump();
      expect(find.text('[zz] Home'), findsOneWidget);
    });
  });

  group('long translations', () {
    // Pseudo-locale: every string about 2.5x longer (Hausa and Fulfulde often run
    // 30-60% longer than English), on a small 360 dp phone. A layout overflow fails.
    Map<String, String> longStrings() => {
          for (final e in kEnglishStrings.entries) e.key: '${e.value} ${e.value.replaceAll(RegExp(r'\{\w+\}'), 'xxxx')} ẹ̀ɓɗƙ',
        };

    Future<void> pumpSmall(WidgetTester tester, Widget child) async {
      tester.view.physicalSize = const Size(360 * 3, 740 * 3);
      tester.view.devicePixelRatio = 3;
      addTearDown(tester.view.reset);
      L10n.instance.apply('zz', longStrings());
      await tester.pumpWidget(MaterialApp(
        builder: (context, c) => L10nScope(child: c!),
        home: Scaffold(body: SingleChildScrollView(child: child), bottomNavigationBar: const AppBottomNav(currentRoute: '/home')),
      ));
      await tester.pump();
      expect(tester.takeException(), isNull);
    }

    testWidgets('bottom navigation and the General test card fit', (tester) async {
      for (final general in [
        const GeneralLearning(active: true, questions: 25, pre: null, post: null, modulesTotal: 6, modulesCompleted: 0),
        GeneralLearning(
            active: true,
            questions: 25,
            pre: TestScore(clientId: 'a', testType: 'PRE', correct: 12, total: 25, takenAt: DateTime(2026)),
            post: null,
            modulesTotal: 6,
            modulesCompleted: 2),
      ]) {
        await pumpSmall(tester, GeneralTestCard(general: general));
      }
    });
  });

  group('local cache', () {
    late LocalDatabase db;
    setUp(() => db = LocalDatabase.forTesting(NativeDatabase.memory()));
    tearDown(() => db.close());

    test('stores, updates and removes strings per language; safe to repeat', () async {
      await db.applyAppStrings('zz', {'nav.home': 'a', 'home.sectionCount': 'b', 'home.sectionCount#one': 'c'}, const []);
      await db.applyAppStrings('zz', {'nav.home': 'a2'}, const ['home.sectionCount']);
      await db.applyAppStrings('zz', {'nav.home': 'a2'}, const ['home.sectionCount']); // repeat: no change
      expect(await db.getAppStrings('zz'), {'nav.home': 'a2'});
      await db.applyAppStrings('yy', {'nav.home': 'y'}, const []);
      await db.applyAppStrings('zz', {'nav.about': 'n'}, const [], replaceAll: true);
      expect(await db.getAppStrings('zz'), {'nav.about': 'n'}, reason: 'a full download replaces the language');
      expect(await db.getAppStrings('yy'), {'nav.home': 'y'}, reason: 'other languages untouched');
    });

    test('upgrading a version 8 database adds the table and keeps existing data', () async {
      final dir = await Directory.systemTemp.createTemp('sarmaan-v8-');
      addTearDown(() => dir.delete(recursive: true));
      final file = File('${dir.path}/db.sqlite');
      var v8 = LocalDatabase.forTesting(NativeDatabase(file));
      await v8.setSetting('selected_language_code', 'ha');
      await v8.upsertProgress(moduleId: 'm1', progressPercent: 40);
      // Make it look exactly like an app 0.1.12 database: no app-strings table, version 8.
      await v8.customStatement('DROP TABLE cached_app_strings');
      await v8.customStatement('PRAGMA user_version = 8');
      await v8.close();

      final upgraded = LocalDatabase.forTesting(NativeDatabase(file));
      addTearDown(upgraded.close);
      expect(await upgraded.getSetting('selected_language_code'), 'ha');
      expect((await upgraded.getAllProgress()).single.progressPercent, 40);
      await upgraded.applyAppStrings('ha', {'nav.home': '[zz] x'}, const []);
      expect(await upgraded.getAppStrings('ha'), {'nav.home': '[zz] x'});
    });
  });

  group('download', () {
    late LocalDatabase db;
    late _AppStringsServer server;
    late AppStringsService service;

    setUp(() {
      db = LocalDatabase.forTesting(NativeDatabase.memory());
      server = _AppStringsServer();
      FlutterSecureStorage.setMockInitialValues({});
      final api = ApiClient();
      api.dio.httpClientAdapter = server;
      service = AppStringsService(api, db);
    });
    tearDown(() => db.close());

    test('first download is full, later ones ask only for changes since the last', () async {
      L10n.instance.apply('zz', const {});
      server.reply = {
        'language': 'zz',
        'server_time': '2026-11-12T10:00:00+00:00',
        'full': true,
        'strings': [
          {'key': 'nav.home', 'text': '[zz] Home', 'text_one': null},
          {'key': 'home.sectionCount', 'text': '[zz] {count} many', 'text_one': '[zz] {count} one'},
        ],
        'removed': [],
      };
      await service.sync('zz');
      expect(server.lastQuery, {'language': 'zz'});
      expect(L10n.t('nav.home'), '[zz] Home', reason: 'shown as soon as it arrives');
      expect(L10n.n('home.sectionCount', 1), '[zz] 1 one');

      server.reply = {
        'language': 'zz',
        'server_time': '2026-11-12T11:00:00+00:00',
        'full': false,
        'strings': [
          {'key': 'nav.modules', 'text': '[zz] Modules'},
        ],
        'removed': ['home.sectionCount'],
      };
      await service.sync('zz');
      expect(server.lastQuery, {'language': 'zz', 'since': '2026-11-12T10:00:00+00:00'});
      expect(await db.getAppStrings('zz'), {'nav.home': '[zz] Home', 'nav.modules': '[zz] Modules'});
      expect(L10n.n('home.sectionCount', 1), '1 section', reason: 'retired on the server: English again');
    });

    test('offline: keeps what is cached and does not throw', () async {
      await db.applyAppStrings('zz', {'nav.home': '[zz] Home'}, const []);
      await service.show('zz');
      server.fail = true;
      await service.sync('zz');
      expect(L10n.t('nav.home'), '[zz] Home');
    });

    test('nothing is downloaded for English', () async {
      await service.sync('en');
      expect(server.calls, 0);
    });
  });
}

class _AppStringsServer implements HttpClientAdapter {
  Map<String, dynamic> reply = const {};
  Map<String, dynamic>? lastQuery;
  bool fail = false;
  int calls = 0;

  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    calls++;
    if (fail) throw DioException.connectionError(requestOptions: options, reason: 'offline');
    expect(options.path, '/sync/app-strings');
    lastQuery = Map.of(options.queryParameters);
    return ResponseBody.fromString(jsonEncode(reply), 200, headers: {
      Headers.contentTypeHeader: ['application/json'],
    });
  }

  @override
  void close({bool force = false}) {}
}
