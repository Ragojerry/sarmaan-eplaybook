/// Quiz grading, mirrored from backend/app/quiz/grading.py and held to it by
/// the shared vectors (test/quiz_vectors.json, replayed by
/// test/quiz_grader_test.dart). Change both together.
///
/// Answer shapes (indexes refer to the ORIGINAL order in the question, not the
/// shuffled order the learner saw):
///   MULTIPLE_CHOICE / IMAGE_CHOICE  int
///   TRUE_FALSE                      bool
///   MULTIPLE_SELECT                 List<int> (any order)
///   MATCHING                        List<int>: answer[i] = right-hand pair matched to left i
///   ORDERING                        List<int>: item indexes in the learner's order
///   NUMERIC                         num
library;

const int kQuizPassMark = 90;

bool _isNum(Object? v) => v is num && v.isFinite;

List<int>? _intList(Object? v) {
  if (v is! List) return null;
  final out = <int>[];
  for (final x in v) {
    if (x is! int) return null;
    out.add(x);
  }
  return out;
}

bool isQuestionCorrect(String type, Map<String, dynamic> content, Object? answer) {
  switch (type) {
    case 'MULTIPLE_CHOICE':
    case 'IMAGE_CHOICE':
      return answer is int && answer == content['correct'];
    case 'TRUE_FALSE':
      return answer is bool && answer == content['correct'];
    case 'MULTIPLE_SELECT':
      final given = _intList(answer);
      final want = _intList(content['correct']);
      if (given == null || want == null || given.toSet().length != given.length) return false;
      final a = [...given]..sort();
      final b = [...want]..sort();
      if (a.length != b.length) return false;
      for (var i = 0; i < a.length; i++) {
        if (a[i] != b[i]) return false;
      }
      return true;
    case 'MATCHING':
      final n = (content['pairs'] as List).length;
      return _isIdentity(_intList(answer), n);
    case 'ORDERING':
      final n = (content['items'] as List).length;
      return _isIdentity(_intList(answer), n);
    case 'NUMERIC':
      if (!_isNum(answer)) return false;
      final tol = content['tolerance'];
      final tolerance = tol is num ? tol.toDouble() : 0.0;
      return ((answer as num) - (content['correct'] as num)).abs() <= tolerance + 1e-9;
  }
  return false;
}

bool _isIdentity(List<int>? list, int n) {
  if (list == null || list.length != n) return false;
  for (var i = 0; i < n; i++) {
    if (list[i] != i) return false;
  }
  return true;
}

/// Exact integer arithmetic, no rounding at the 90% edge.
bool quizPassed(int correct, int total) => total > 0 && correct * 100 >= kQuizPassMark * total;

int quizScorePercent(int correct, int total) => total <= 0 ? 0 : (correct * 100) ~/ total;
