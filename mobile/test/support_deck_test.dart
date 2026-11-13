import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarmaan_eplaybook/db/local_database.dart';
import 'package:sarmaan_eplaybook/offline/content_sync_service.dart' show localDatabaseProvider;
import 'package:sarmaan_eplaybook/support/support_contacts.dart';
import 'package:sarmaan_eplaybook/widgets/support_deck.dart';

import 'support/fake_server.dart' show FakeServer, fakeApi;

// Reserved test values only (555-01xx numbers, example.org), never real contacts.
const _phone = SupportContact(id: 'p', type: SupportContactType.phone, label: 'Call the support line', value: '+15550100001',
    availability: 'Mon-Fri 8am-5pm', languages: 'English, Hausa');
const _email = SupportContact(id: 'e', type: SupportContactType.email, label: 'Email the team', value: 'help@example.org',
    emailSubject: 'e-Playbook question');

/// Answers GET /sync/support-contacts with the next queued JSON body and records the query.
class _JsonServer extends FakeServer {
  final List<Map<String, dynamic>> replies = [];
  final List<Map<String, dynamic>> queries = [];

  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    if (options.path != '/sync/support-contacts' || replies.isEmpty) return ResponseBody.fromString('not found', 404);
    queries.add(Map.of(options.queryParameters));
    return ResponseBody.fromString(jsonEncode(replies.removeAt(0)), 200, headers: {
      Headers.contentTypeHeader: ['application/json'],
    });
  }
}

Map<String, dynamic> _row(String id, String type, String value, {int order = 0}) => {
      'id': id,
      'type': type,
      'label': 'Label $id',
      'value': value,
      'whatsapp_message': null,
      'email_subject': null,
      'include_app_version': false,
      'availability': null,
      'languages': null,
      'display_order': order,
    };

void main() {
  group('links', () {
    test('call and SMS use the number as entered', () {
      expect(supportUri(_phone).toString(), 'tel:+15550100001');
      expect(supportUri(const SupportContact(id: 's', type: SupportContactType.sms, label: 'SMS', value: '+15550100002')).toString(),
          'sms:+15550100002');
    });

    test('email carries only the subject, and the app version when enabled', () {
      expect(supportUri(_email).toString(), 'mailto:help@example.org?subject=e-Playbook%20question');
      const withVersion = SupportContact(id: 'e2', type: SupportContactType.email, label: 'x', value: 'help@example.org',
          includeAppVersion: true);
      expect(supportUri(withVersion, appVersionLine: 'App version: 0.1.15').toString(),
          'mailto:help@example.org?body=App%20version%3A%200.1.15');
      expect(supportUri(_email, appVersionLine: 'App version: 0.1.15').toString(), isNot(contains('version')),
          reason: 'not enabled by the admin');
    });

    test('WhatsApp opens wa.me with the digits and the encoded message', () {
      const wa = SupportContact(id: 'w', type: SupportContactType.whatsapp, label: 'Chat', value: '+15550100003',
          whatsappMessage: 'Hello & thanks?', includeAppVersion: true);
      expect(supportUri(wa, appVersionLine: 'App version: 0.1.15').toString(),
          'https://wa.me/15550100003?text=Hello%20%26%20thanks%3F%0AApp%20version%3A%200.1.15');
      const plain = SupportContact(id: 'w2', type: SupportContactType.whatsapp, label: 'Chat', value: '+15550100003');
      expect(supportUri(plain).toString(), 'https://wa.me/15550100003');
    });

    test('links must be https', () {
      const ok = SupportContact(id: 'l', type: SupportContactType.link, label: 'Help', value: 'https://example.org/help');
      expect(supportUri(ok).toString(), 'https://example.org/help');
      const bad = SupportContact(id: 'l2', type: SupportContactType.link, label: 'Help', value: 'http://example.org');
      expect(supportUri(bad), isNull);
    });

    test('only email, WhatsApp and links need internet', () {
      expect(SupportContactType.values.where(needsInternet),
          [SupportContactType.email, SupportContactType.whatsapp, SupportContactType.link]);
    });
  });

  group('cache and sync', () {
    late LocalDatabase db;
    late _JsonServer server;
    late SupportContactsService service;

    setUp(() {
      db = LocalDatabase.forTesting(NativeDatabase.memory());
      server = _JsonServer();
      service = SupportContactsService(fakeApi(server), db);
    });
    tearDown(() => db.close());

    test('downloads everything first, then only changes; removes what the server removed', () async {
      expect((await service.load()).contacts, isEmpty, reason: 'nothing cached: the deck is hidden');
      server.replies.add({
        'server_time': '2026-11-13T10:00:00+00:00',
        'full': true,
        'contacts': [_row('a', 'PHONE', '+15550100001', order: 1), _row('b', 'EMAIL', 'help@example.org', order: 0)],
        'removed': [],
        'note': 'For a medical emergency, go to the nearest health facility.',
      });
      await service.sync('learner:CDD');
      var deck = await service.load();
      expect(deck.contacts.map((c) => c.id), ['b', 'a'], reason: 'display order');
      expect(deck.note, startsWith('For a medical emergency'));
      expect(server.queries.single, isEmpty, reason: 'first download has no since');

      server.replies.add({
        'server_time': '2026-11-13T11:00:00+00:00',
        'full': false,
        'contacts': [_row('c', 'LINK', 'https://example.org', order: 2), _row('x', 'FAX', '123')],
        'removed': ['b'],
        'note': null,
      });
      await service.sync('learner:CDD');
      expect(server.queries.last, {'since': '2026-11-13T10:00:00+00:00'});
      deck = await service.load();
      expect(deck.contacts.map((c) => c.id), ['a', 'c'], reason: 'b removed; an unknown type is skipped');
      expect(deck.note, isNull, reason: 'empty note = hidden');

      // Another audience (role change, other account): a full download again.
      server.replies.add({'server_time': '2026-11-13T12:00:00+00:00', 'full': true, 'contacts': [], 'removed': [], 'note': null});
      await service.sync('learner:HEALTH_WORKER');
      expect(server.queries.last, isEmpty);
      expect((await service.load()).contacts, isEmpty);
    });

    test('offline or an older server keeps the cache', () async {
      server.replies.add({'server_time': 't1', 'full': true, 'contacts': [_row('a', 'PHONE', '+15550100001')], 'removed': [], 'note': null});
      await service.sync('staff');
      await service.sync('staff'); // no reply queued -> 404
      expect((await service.load()).contacts.single.id, 'a');
    });

    test('upgrading from schema 9 adds the table and keeps existing data', () async {
      final dir = await Directory.systemTemp.createTemp('sarmaan-db-');
      addTearDown(() => dir.delete(recursive: true));
      final file = File('${dir.path}/app.sqlite');
      var old = LocalDatabase.forTesting(NativeDatabase(file));
      await old.setSetting('selected_language_code', 'ha');
      await old.customStatement('DROP TABLE cached_support_contacts');
      await old.customStatement('PRAGMA user_version = 9');
      await old.close();

      final upgraded = LocalDatabase.forTesting(NativeDatabase(file));
      addTearDown(upgraded.close);
      expect(await upgraded.getSetting('selected_language_code'), 'ha');
      expect(await upgraded.getSupportContacts(), isEmpty);
      await upgraded.applySupportContacts([
        CachedSupportContactsCompanion.insert(id: 'a', type: 'PHONE', label: 'Call', value: '+15550100001'),
      ], const []);
      expect((await upgraded.getSupportContacts()).single.id, 'a');
    });
  });

  group('deck', () {
    late LocalDatabase db;
    late List<Uri> launched;
    var online = true;
    var launchWorks = true;

    setUp(() {
      db = LocalDatabase.forTesting(NativeDatabase.memory());
      launched = [];
      online = true;
      launchWorks = true;
    });
    tearDown(() => db.close());

    Future<void> pump(WidgetTester tester, List<SupportContact> contacts, {bool collapsible = false, String? note}) async {
      await tester.pumpWidget(ProviderScope(
        overrides: [
          localDatabaseProvider.overrideWithValue(db),
          supportDeckProvider.overrideWith((ref) async => SupportDeckData(contacts, note)),
          supportLauncherProvider.overrideWithValue((uri) async {
            launched.add(uri);
            return launchWorks;
          }),
          supportOnlineCheckProvider.overrideWithValue(() async => online),
        ],
        child: MaterialApp(home: Scaffold(body: ListView(children: [SupportDeck(collapsible: collapsible)]))),
      ));
      await tester.pumpAndSettle();
    }

    testWidgets('is hidden when there is no active contact', (tester) async {
      await pump(tester, const []);
      expect(find.text('Need help from a person?'), findsNothing);
      expect(find.byType(InkWell), findsNothing);
    });

    testWidgets('shows each contact with its type written out, and a copy button', (tester) async {
      await pump(tester, const [_phone, _email], note: 'Admin note');
      expect(find.text('Need help from a person?'), findsOneWidget);
      expect(find.text('Call · +15550100001'), findsOneWidget);
      expect(find.text('Email · help@example.org'), findsOneWidget);
      expect(find.text('Mon-Fri 8am-5pm'), findsOneWidget);
      expect(find.text('Languages: English, Hausa'), findsOneWidget);
      expect(find.text('Admin note'), findsOneWidget);
      expect(find.byTooltip('Copy'), findsNWidgets(2));
      expect(find.bySemanticsLabel(RegExp(r'^Call: Call the support line, \+15550100001')), findsOneWidget);
      for (final row in tester.widgetList<InkWell>(find.byType(InkWell))) {
        expect(tester.getSize(find.byWidget(row)).height, greaterThanOrEqualTo(44));
      }
    });

    testWidgets('the folded deck opens on tap', (tester) async {
      await pump(tester, const [_phone], collapsible: true);
      expect(find.text('Call the support line'), findsNothing);
      await tester.tap(find.text('Need help from a person?'));
      await tester.pumpAndSettle();
      expect(find.text('Call the support line'), findsOneWidget);
    });

    testWidgets('a call opens the dialer, also offline', (tester) async {
      online = false;
      await pump(tester, const [_phone]);
      await tester.tap(find.text('Call the support line'));
      await tester.pumpAndSettle();
      expect(launched.single.toString(), 'tel:+15550100001');
      expect(find.byType(AlertDialog), findsNothing);
    });

    testWidgets('email offline says internet is needed and offers to copy', (tester) async {
      String? copied;
      tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(SystemChannels.platform, (call) async {
        if (call.method == 'Clipboard.setData') copied = (call.arguments as Map)['text'] as String;
        return null;
      });
      online = false;
      await pump(tester, const [_email]);
      await tester.tap(find.text('Email the team'));
      await tester.pumpAndSettle();
      expect(launched, isEmpty);
      expect(find.textContaining('needs an internet connection'), findsOneWidget);
      await tester.tap(find.text('Copy details'));
      await tester.pumpAndSettle();
      expect(copied, 'help@example.org');
      expect(find.text('Copied help@example.org'), findsOneWidget);
    });

    testWidgets('a missing app shows a friendly message', (tester) async {
      launchWorks = false;
      await pump(tester, const [_email]);
      await tester.tap(find.text('Email the team'));
      await tester.pumpAndSettle();
      expect(launched.single.scheme, 'mailto');
      expect(find.textContaining("couldn't open Email"), findsOneWidget);
      await tester.tap(find.text('Close'));
      await tester.pumpAndSettle();
      expect(find.byType(AlertDialog), findsNothing);
    });

    testWidgets('the copy button and a long press copy the value', (tester) async {
      final copies = <String>[];
      tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(SystemChannels.platform, (call) async {
        if (call.method == 'Clipboard.setData') copies.add((call.arguments as Map)['text'] as String);
        return null;
      });
      await pump(tester, const [_phone]);
      await tester.tap(find.byTooltip('Copy'));
      await tester.pumpAndSettle();
      await tester.longPress(find.text('Call the support line'));
      await tester.pumpAndSettle();
      expect(copies, ['+15550100001', '+15550100001']);
      expect(launched, isEmpty);
    });
  });
}
