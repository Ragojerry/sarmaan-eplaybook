import 'dart:async';

import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarmaan_eplaybook/db/local_database.dart';
import 'package:sarmaan_eplaybook/qa/question_answer_service.dart';

Map<String, dynamic> _serverAnswer({String kind = 'module'}) => {
      'answer': 'AZM is given only to healthy children between 1 and 59 months.',
      'matched': true,
      'confidence': 0.82,
      'offline': false,
      'sources': [
        {
          'chunk_id': 'c1',
          'module_id': kind == 'module' ? 'm1' : null,
          'section_id': null,
          'module_code': kind == 'module' ? 'M2' : 'REF',
          'module_title': kind == 'module' ? 'Eligibility' : 'National AZM guideline',
          'section_title': 'Age eligibility',
          'snippet': 'AZM is given only to healthy children between 1 and 59 months.',
          'kind': kind,
        },
      ],
      'suggestions': <String>[],
    };

void main() {
  late LocalDatabase db;

  setUp(() {
    db = LocalDatabase.forTesting(NativeDatabase.memory());
    db.setActiveUser('user-1');
  });
  tearDown(() => db.close());

  Future<int> queued() => db.countPending(entityTypes: ['ai_question']);

  test('online: the server answers, and the question is not queued twice', () async {
    final service = QuestionAnswerService(db, (q, lang) async => _serverAnswer(), maybeOnline: () async => true);
    final r = await service.ask('Which kids can take the drug?');
    expect(r.matched, isTrue);
    expect(r.offline, isFalse);
    expect(r.sources.single.moduleCode, 'M2');
    expect(await queued(), 0, reason: 'the server already logged it');
  });

  test('reference library sources are recognised', () async {
    final service =
        QuestionAnswerService(db, (q, lang) async => _serverAnswer(kind: 'reference'), maybeOnline: () async => true);
    final r = await service.ask('What does the guideline say?');
    expect(r.sources.single.isReference, isTrue);
    expect(r.sources.single.moduleId, isNull);
  });

  test('no network: nothing downloaded gives the download message and is queued', () async {
    var called = false;
    final service = QuestionAnswerService(db, (q, lang) async {
      called = true;
      return _serverAnswer();
    }, maybeOnline: () async => false);
    final r = await service.ask('Who is eligible?');
    expect(called, isFalse, reason: 'airplane mode skips the server');
    expect(r.answer, kNothingDownloadedMessage);
    expect(await queued(), 1);
  });

  test('a server error or a slow server falls back without hanging', () async {
    final failing = QuestionAnswerService(db, (q, lang) async => throw Exception('502'), maybeOnline: () async => true);
    expect((await failing.ask('Who is eligible?')).offline, isTrue);

    final slow = QuestionAnswerService(
      db,
      (q, lang) => Completer<Map<String, dynamic>>().future, // never answers
      maybeOnline: () async => true,
      serverTimeoutWithoutContent: const Duration(milliseconds: 50),
    );
    final r = await slow.ask('Who is eligible?');
    expect(r.offline, isTrue);
    expect(await queued(), 2);
  });
}
