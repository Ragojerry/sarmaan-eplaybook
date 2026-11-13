import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:sarmaan_eplaybook/db/local_database.dart';
import 'package:sarmaan_eplaybook/offline/content_sync_service.dart' show localDatabaseProvider;
import 'package:sarmaan_eplaybook/screens/tools_screen.dart';
import 'package:sarmaan_eplaybook/tools/tools_service.dart';
import 'package:sarmaan_eplaybook/widgets/support_deck.dart' show supportLauncherProvider, supportOnlineCheckProvider;
import 'package:sarmaan_eplaybook/widgets/tools_entry.dart';

import 'support/fake_server.dart' show FakeServer, fakeApi;

/// Answers GET /sync/tools with the next queued JSON body and records the query.
class _JsonServer extends FakeServer {
  final List<Map<String, dynamic>> replies = [];
  final List<Map<String, dynamic>> queries = [];

  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    if (options.path != '/sync/tools' || replies.isEmpty) return ResponseBody.fromString('not found', 404);
    queries.add(Map.of(options.queryParameters));
    return ResponseBody.fromString(jsonEncode(replies.removeAt(0)), 200, headers: {
      Headers.contentTypeHeader: ['application/json'],
    });
  }
}

Map<String, dynamic> _mod(String id, {int order = 0}) => {'id': id, 'title': 'Module $id', 'description': null, 'display_order': order};

Map<String, dynamic> _item(String id, String module, {String type = 'PDF', String? category, int order = 0}) => {
      'id': id,
      'tool_module_id': module,
      'title': 'Item $id',
      'description': 'About $id',
      'type': type,
      'url': 'https://example.org/$id',
      'host': null,
      'category': category,
      'languages': null,
      'display_order': order,
    };

const _drive = ToolLink(id: 'd', moduleId: 'm', title: 'Referral form', description: 'Fill in for each referral', type: ToolType.form,
    url: 'https://docs.google.com/forms/d/x', host: 'GOOGLE_DRIVE', category: 'Forms');
const _aid = ToolLink(id: 'a', moduleId: 'm', title: 'Dosing job aid', type: ToolType.pdf, url: 'https://example.org/aid.pdf',
    category: 'Job aids', languages: 'English, Hausa');

void main() {
  group('cache and sync', () {
    late LocalDatabase db;
    late _JsonServer server;
    late ToolsService service;

    setUp(() {
      db = LocalDatabase.forTesting(NativeDatabase.memory());
      server = _JsonServer();
      service = ToolsService(fakeApi(server), db);
    });
    tearDown(() => db.close());

    test('downloads everything first, then only changes; drops removed items and modules', () async {
      expect((await service.load()).isEmpty, isTrue, reason: 'nothing cached: no Tools section');
      server.replies.add({
        'server_time': '2026-11-13T10:00:00+00:00',
        'full': true,
        'modules': [_mod('g'), _mod('s', order: 1)],
        'items': [_item('1', 'g', category: 'Forms', order: 1), _item('2', 'g', order: 0), _item('3', 's')],
        'removed': [],
      });
      await service.sync('learner:MONITOR_SUPERVISOR');
      var data = await service.load();
      expect(data.sections.map((s) => s.id), ['g', 's']);
      expect(data.sections.first.links.map((l) => l.id), ['2', '1'], reason: 'display order');
      expect(data.linkCount, 3);
      expect(data.categories, ['Forms']);
      expect(server.queries.single, isEmpty);

      server.replies.add({
        'server_time': '2026-11-13T11:00:00+00:00',
        'full': false,
        'modules': [_mod('g')], // the supervisor module was switched off
        'items': [_item('4', 'g', type: 'SOMETHING_NEW', order: 2)],
        'removed': ['1'],
      });
      await service.sync('learner:MONITOR_SUPERVISOR');
      expect(server.queries.last, {'since': '2026-11-13T10:00:00+00:00'});
      data = await service.load();
      expect(data.sections.map((s) => s.id), ['g']);
      expect(data.sections.single.links.map((l) => l.id), ['2', '4']);
      expect(data.sections.single.links.last.type, ToolType.other, reason: 'an unknown type still shows');

      server.replies.add({'server_time': 't3', 'full': true, 'modules': [], 'items': [], 'removed': []});
      await service.sync('learner:CDD');
      expect(server.queries.last, isEmpty, reason: 'another audience downloads everything');
      expect((await service.load()).isEmpty, isTrue);
    });

    test('offline or an older server keeps the cache', () async {
      server.replies.add({'server_time': 't1', 'full': true, 'modules': [_mod('g')], 'items': [_item('1', 'g')], 'removed': []});
      await service.sync('staff');
      await service.sync('staff'); // no reply queued -> 404
      expect((await service.load()).linkCount, 1);
    });

    test('upgrading from schema 10 adds the tables and keeps existing data', () async {
      final dir = await Directory.systemTemp.createTemp('sarmaan-db-');
      addTearDown(() => dir.delete(recursive: true));
      final file = File('${dir.path}/app.sqlite');
      final old = LocalDatabase.forTesting(NativeDatabase(file));
      await old.setSetting('selected_language_code', 'ha');
      await old.applySupportContacts([CachedSupportContactsCompanion.insert(id: 'c', type: 'PHONE', label: 'Call', value: '+15550100001')], const []);
      await old.customStatement('DROP TABLE cached_tool_items');
      await old.customStatement('DROP TABLE cached_tool_modules');
      await old.customStatement('PRAGMA user_version = 10');
      await old.close();

      final upgraded = LocalDatabase.forTesting(NativeDatabase(file));
      addTearDown(upgraded.close);
      expect(await upgraded.getSetting('selected_language_code'), 'ha');
      expect((await upgraded.getSupportContacts()).single.id, 'c');
      expect(await upgraded.getToolItems(), isEmpty);
    });

    test('tool links never reach the question index or training tables', () async {
      server.replies.add({'server_time': 't1', 'full': true, 'modules': [_mod('g')], 'items': [_item('1', 'g')], 'removed': []});
      await service.sync('staff');
      expect(await db.getChunks('en'), isEmpty);
      expect(await db.select(db.cachedModules).get(), isEmpty);
      expect(await db.select(db.localProgress).get(), isEmpty);
    });
  });

  group('screens', () {
    late LocalDatabase db;
    late List<Uri> launched;
    late List<String> shared;
    var online = true;
    var launchWorks = true;

    setUp(() {
      db = LocalDatabase.forTesting(NativeDatabase.memory());
      launched = [];
      shared = [];
      online = true;
      launchWorks = true;
    });
    tearDown(() => db.close());

    Future<void> pump(WidgetTester tester, ToolsData data, Widget home) async {
      final router = GoRouter(routes: [
        GoRoute(path: '/', builder: (_, __) => home),
        GoRoute(path: '/tools', builder: (_, __) => const ToolsScreen()),
      ]);
      await tester.pumpWidget(ProviderScope(
        overrides: [
          localDatabaseProvider.overrideWithValue(db),
          toolsProvider.overrideWith((ref) async => data),
          supportLauncherProvider.overrideWithValue((uri) async {
            launched.add(uri);
            return launchWorks;
          }),
          supportOnlineCheckProvider.overrideWithValue(() async => online),
          toolSharerProvider.overrideWithValue((text, subject) async => shared.add(text)),
        ],
        child: MaterialApp.router(routerConfig: router),
      ));
      await tester.pumpAndSettle();
    }

    const twoModules = ToolsData([
      ToolSection('m', 'General tools', null, [_drive, _aid]),
      ToolSection('s', 'Supervisor tools', null, [
        ToolLink(id: 's1', moduleId: 's', title: 'Supervision checklist', type: ToolType.spreadsheet, url: 'https://example.org/s1'),
      ]),
    ]);

    testWidgets('the Tools entry is hidden without links', (tester) async {
      await pump(tester, ToolsData.empty, const Scaffold(body: ToolsEntry()));
      expect(find.text('Tools repository'), findsNothing);
      expect(find.text('TOOLS'), findsNothing);
    });

    testWidgets('the Tools entry has no progress, tick or lock, and opens the Tools screen', (tester) async {
      await pump(tester, twoModules, const Scaffold(body: ToolsEntry()));
      expect(find.text('TOOLS'), findsOneWidget);
      expect(find.text('Tools repository'), findsOneWidget);
      expect(find.text('3 links · open online'), findsOneWidget);
      expect(find.byType(LinearProgressIndicator), findsNothing);
      expect(find.byIcon(Icons.lock_outline_rounded), findsNothing);
      expect(find.byIcon(Icons.check_rounded), findsNothing);
      await tester.tap(find.text('Tools repository'));
      await tester.pumpAndSettle();
      expect(find.byType(ToolsScreen), findsOneWidget);
    });

    testWidgets('lists links by module with type written out, filters by category and search', (tester) async {
      await pump(tester, twoModules, const ToolsScreen());
      expect(find.text('General tools'), findsOneWidget);
      expect(find.text('Supervisor tools'), findsOneWidget);
      expect(find.text('Form · Google Drive · Opens online'), findsOneWidget);
      expect(find.text('PDF · Opens online'), findsOneWidget);
      expect(find.text('Languages: English, Hausa'), findsOneWidget);
      expect(find.byTooltip('Copy link'), findsNWidgets(3));
      expect(find.byTooltip('Share link'), findsNWidgets(3));
      expect(find.bySemanticsLabel(RegExp(r'^Form: Referral form\. Fill in for each referral\. Opens online$')), findsOneWidget);
      for (final row in tester.widgetList<InkWell>(find.descendant(of: find.byType(ToolRow), matching: find.byType(InkWell)))) {
        expect(tester.getSize(find.byWidget(row)).height, greaterThanOrEqualTo(44));
      }

      await tester.tap(find.widgetWithText(ChoiceChip, 'Job aids'));
      await tester.pumpAndSettle();
      expect(find.text('Dosing job aid'), findsOneWidget);
      expect(find.text('Referral form'), findsNothing);
      expect(find.text('Supervision checklist'), findsNothing);

      await tester.tap(find.widgetWithText(ChoiceChip, 'All'));
      await tester.enterText(find.byType(TextField), 'checklist');
      await tester.pumpAndSettle();
      expect(find.text('Supervision checklist'), findsOneWidget);
      expect(find.text('Dosing job aid'), findsNothing);

      await tester.enterText(find.byType(TextField), 'nothing like this');
      await tester.pumpAndSettle();
      expect(find.text('No tools match your search.'), findsOneWidget);
    });

    testWidgets('a tap opens the https link outside the app', (tester) async {
      await pump(tester, twoModules, const ToolsScreen());
      await tester.tap(find.text('Referral form'));
      await tester.pumpAndSettle();
      expect(launched.single.toString(), 'https://docs.google.com/forms/d/x');
      expect(find.byType(AlertDialog), findsNothing);
    });

    testWidgets('offline: a friendly message and Copy link', (tester) async {
      String? copied;
      tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(SystemChannels.platform, (call) async {
        if (call.method == 'Clipboard.setData') copied = (call.arguments as Map)['text'] as String;
        return null;
      });
      online = false;
      await pump(tester, twoModules, const ToolsScreen());
      await tester.tap(find.text('Dosing job aid'));
      await tester.pumpAndSettle();
      expect(launched, isEmpty);
      expect(find.textContaining('You need an internet connection'), findsOneWidget);
      await tester.tap(find.descendant(of: find.byType(AlertDialog), matching: find.text('Copy link')));
      await tester.pumpAndSettle();
      expect(copied, 'https://example.org/aid.pdf');
      expect(find.text('Link copied'), findsOneWidget);
    });

    testWidgets('no app for the link: a friendly message', (tester) async {
      launchWorks = false;
      await pump(tester, twoModules, const ToolsScreen());
      await tester.tap(find.text('Dosing job aid'));
      await tester.pumpAndSettle();
      expect(find.textContaining("couldn't open this link"), findsOneWidget);
    });

    testWidgets('copy and share buttons on every row', (tester) async {
      final copies = <String>[];
      tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(SystemChannels.platform, (call) async {
        if (call.method == 'Clipboard.setData') copies.add((call.arguments as Map)['text'] as String);
        return null;
      });
      await pump(tester, twoModules, const ToolsScreen());
      await tester.tap(find.byTooltip('Copy link').first);
      await tester.tap(find.byTooltip('Share link').first);
      await tester.pumpAndSettle();
      expect(copies, ['https://docs.google.com/forms/d/x']);
      expect(shared, ['Referral form\nhttps://docs.google.com/forms/d/x']);
      expect(launched, isEmpty);
    });

    test('only https links are opened', () {
      const bad = ToolLink(id: 'x', moduleId: 'm', title: 'x', type: ToolType.website, url: 'javascript:alert(1)');
      expect(bad.uri, isNull);
      expect(_aid.uri.toString(), 'https://example.org/aid.pdf');
    });
  });
}
