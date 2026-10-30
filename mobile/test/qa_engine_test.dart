import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:sarmaan_eplaybook/qa/qa_engine.dart';

/// Replays backend/tests/qa_vectors.json (copied to test/qa_vectors.json by
/// backend/scripts/generate_qa_vectors.py) against the Dart engine. These
/// are the SAME vectors the Python suite replays, so a passing run here
/// proves the phone and the server give identical answers.
void main() {
  final vectors = jsonDecode(File('test/qa_vectors.json').readAsStringSync()) as Map<String, dynamic>;

  test('stopwords match the Python engine', () {
    expect(kStopwords.toList()..sort(), equals(List<String>.from(vectors['stopwords'] as List)));
  });

  test('synonym groups match the Python engine', () {
    final expected = [for (final g in vectors['synonym_groups'] as List) List<String>.from(g as List)];
    expect(kSynonymGroups, equals(expected));
  });

  group('tokenize', () {
    for (final c in vectors['tokenize'] as List) {
      test(c['input'] as String, () {
        expect(tokenize(c['input'] as String), equals(List<String>.from(c['expected'] as List)));
      });
    }
  });

  group('stem', () {
    for (final c in vectors['stem'] as List) {
      test(c['input'] as String, () {
        expect(stem(c['input'] as String), equals(c['expected'] as String));
      });
    }
  });

  group('contentTerms', () {
    for (final c in vectors['content_terms'] as List) {
      test(c['input'] as String, () {
        expect(contentTerms(c['input'] as String), equals(List<String>.from(c['expected'] as List)));
      });
    }
  });

  group('answers', () {
    final chunks = [for (final c in vectors['chunks'] as List) QaChunk.fromJson(c as Map<String, dynamic>)];
    for (final c in vectors['answers'] as List) {
      test(c['question'] as String, () {
        final expected = c['expected'] as Map<String, dynamic>;
        final r = answerQuestion(c['question'] as String, chunks);
        expect(r.matched, equals(expected['matched'] as bool));
        expect(r.confidence, equals((expected['confidence'] as num).toDouble()));
        expect(r.answer, equals(expected['answer'] as String));
        expect(r.sources.map((s) => s.chunkId).toList(), equals(List<String>.from(expected['source_ids'] as List)));
      });
    }
  });
}
