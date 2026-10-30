import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:sarmaan_eplaybook/quiz/quiz_grader.dart';

/// Replays backend/tests/quiz_vectors.json (copied to test/quiz_vectors.json by
/// backend/scripts/generate_quiz_vectors.py), the SAME file the Python suite
/// replays, so the phone and the server grade identically.
void main() {
  final vectors = jsonDecode(File('test/quiz_vectors.json').readAsStringSync()) as Map<String, dynamic>;

  test('pass mark is 90', () => expect(kQuizPassMark, vectors['pass_mark']));

  group('answers', () {
    for (final c in (vectors['answers'] as List).cast<Map<String, dynamic>>()) {
      test('${c['type']} answer=${jsonEncode(c['answer'])}', () {
        final content = Map<String, dynamic>.from(c['content'] as Map);
        expect(isQuestionCorrect(c['type'] as String, content, c['answer']), c['correct']);
      });
    }
  });

  group('90% rule', () {
    for (final c in (vectors['passing'] as List).cast<Map<String, dynamic>>()) {
      test('${c['correct']} of ${c['total']}', () {
        expect(quizPassed(c['correct'] as int, c['total'] as int), c['passed']);
        expect(quizScorePercent(c['correct'] as int, c['total'] as int), c['score_percent']);
      });
    }
  });
}
