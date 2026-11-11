import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../db/local_database.dart';
import '../offline/content_sync_service.dart';
import '../quiz/quiz_grader.dart';
import '../sync/analytics_recorder.dart';
import 'learning_rules.dart';

/// The signed-in learner's modules (only those their learner role may see), each
/// one's state, and the General test, read from the local database so it works
/// offline.
class LearningSnapshot {
  final List<CachedModuleRow> modules;
  final Map<String, ModuleLearning> byId;
  final GeneralLearning general;

  const LearningSnapshot(this.modules, this.byId, this.general);

  ModuleLearning? of(String moduleId) => byId[moduleId];

  /// The module that must be completed before [moduleId] unlocks.
  CachedModuleRow? blockerOf(String moduleId) {
    for (final m in modules) {
      if (m.id == moduleId) return null;
      if (byId[m.id]?.completed != true) return m;
    }
    return null;
  }

  int get completedCount => byId.values.where((s) => s.completed).length;
}

/// Module-quiz attempts that count: not rejected by the server. (PRE/POST and
/// LEGACY rows are the retired per-module tests: history only.)
bool attemptCounts(LocalQuizAttemptRow a) => a.testType == 'MODULE_QUIZ' && a.serverValid != false;

TestScore scoreOf(LocalQuizAttemptRow a) => TestScore(
      clientId: a.clientId,
      testType: a.testType,
      correct: a.correctCount,
      total: a.totalCount,
      takenAt: a.takenAt,
    );

TestScore generalScoreOf(LocalGeneralAttemptRow a) => TestScore(
      clientId: a.clientId,
      testType: a.testType,
      correct: a.correctCount,
      total: a.totalCount,
      takenAt: a.takenAt,
    );

Future<LearningSnapshot> loadLearning(LocalDatabase db) async {
  final modules = await db.getAllModules();
  final quizCounts = await db.quizStatementCountsByModule();
  final progress = {for (final p in await db.getAllProgress()) p.moduleId: p};
  final attempts = (await db.getQuizAttempts()).where(attemptCounts).toList();
  final generalAttempts = [
    for (final a in await db.getGeneralAttempts())
      if (a.serverValid != false) generalScoreOf(a),
  ];
  final active = await db.isGeneralTestActive();
  final pre = firstOf(generalAttempts, 'PRE');
  final states = computeLearning(
    minSeconds: await db.getModuleMinSeconds(),
    gateOpen: !active || pre != null,
    [
      for (final m in modules)
        ModuleInput(
          moduleId: m.id,
          quizStatements: quizCounts[m.id] ?? 0,
          completed: progress[m.id]?.completed ?? false,
          readingDone: progress[m.id]?.readingCompletedAt != null,
          secondsSpent: progress[m.id]?.secondsSpent ?? 0,
          quizAttempts: [for (final a in attempts) if (a.moduleId == m.id) scoreOf(a)],
        ),
    ],
  );
  final general = GeneralLearning(
    active: active,
    questions: (await db.getGeneralQuestions()).where((q) => q.correctIndex != null).length,
    pre: pre,
    post: firstOf(generalAttempts, 'POST'),
    modulesTotal: states.length,
    modulesCompleted: states.where((s) => s.completed).length,
  );
  return LearningSnapshot(modules, {for (final s in states) s.moduleId: s}, general);
}

/// autoDispose: re-read whenever a screen opens, so it is never stale.
final learningProvider = FutureProvider.autoDispose<LearningSnapshot>((ref) => loadLearning(ref.read(localDatabaseProvider)));

/// One inline True/False statement of a module, from its cached section.
class QuizStatement {
  final String sectionId;
  final String statement;
  final bool answer;
  final String? explanation;

  const QuizStatement(this.sectionId, this.statement, this.answer, this.explanation);

  static QuizStatement? fromSection(CachedSectionRow s) {
    if (s.contentType != 'TRUE_FALSE') return null;
    final c = jsonDecode(s.contentJson) as Map<String, dynamic>;
    final answer = c['answer'];
    if (answer is! bool) return null;
    return QuizStatement(s.id, (c['statement'] as String?) ?? '', answer, c['explanation'] as String?);
  }
}

/// The outcome of one module-quiz attempt.
class QuizResult {
  final int correct;
  final int total;
  final bool passed;
  final bool completedModuleQuiz; // the module's quiz is passed now (this or an earlier attempt)

  const QuizResult(this.correct, this.total, this.passed, this.completedModuleQuiz);
}

/// Grades one attempt at a module's inline quiz ([answers]: section id -> the
/// learner's True/False) against the cached statements and saves it for upload.
/// Retakes are unlimited until the module is completed; every attempt is kept.
Future<QuizResult> recordModuleQuiz(LocalDatabase db, {required String moduleId, required Map<String, bool> answers}) async {
  final before = (await loadLearning(db)).of(moduleId);
  if (before == null) throw StateError('module not available');
  if (!before.canTakeQuiz) throw StateError('the quiz is not open');
  final statements = (await db.getSectionsForModule(moduleId)).map(QuizStatement.fromSection).whereType<QuizStatement>().toList();
  final results = [
    for (final q in statements) {'question_id': q.sectionId, 'correct': answers[q.sectionId] == q.answer},
  ];
  final correct = results.where((r) => r['correct'] == true).length;
  await db.insertQuizAttempt(
    moduleId: moduleId,
    clientId: newClientId('quiz'),
    correct: correct,
    total: statements.length,
    scorePercent: quizScorePercent(correct, statements.length),
    passed: moduleQuizPasses(correct, statements.length),
    resultsJson: jsonEncode(results),
    testType: 'MODULE_QUIZ',
  );
  final after = (await loadLearning(db)).of(moduleId)!;
  return QuizResult(correct, statements.length, moduleQuizPasses(correct, statements.length), after.quizPassed);
}

/// Completes a module when the rules allow it (quiz passed, minimum time spent),
/// offline too; the server checks the same when the progress reaches it.
/// Returns null when completed, or the plain reason it is not allowed yet.
Future<String?> completeModule(LocalDatabase db, String moduleId) async {
  final state = (await loadLearning(db)).of(moduleId);
  if (state == null) return 'This module is not available.';
  if (state.completed) return null;
  if (!state.canComplete) return completionMessage(state);
  await db.upsertProgress(moduleId: moduleId, progressPercent: 100, completed: true);
  await db.enqueueSync(
    'progress',
    jsonEncode({'module_id': moduleId, 'completed': true, 'completed_at': DateTime.now().toUtc().toIso8601String()}),
  );
  await recordAnalyticsEvent(db, 'MODULE_COMPLETE', moduleId: moduleId);
  return null;
}

/// What still stands between the learner and completing the module, in plain words.
String? completionMessage(ModuleLearning s) {
  if (s.completed) return null;
  if (!s.unlocked) {
    return s.lockedByGeneralTest ? 'Take the General pre-test first.' : 'Complete the previous module first.';
  }
  if (!s.quizPassed) return 'Answer the module quiz correctly to finish this module.';
  if (!s.timeMet) {
    return 'Please spend at least ${formatDuration(s.minSeconds)} in this module. '
        '${formatDuration(s.secondsLeft)} to go.';
  }
  return null;
}

/// The outcome of a General test.
class GeneralOutcome {
  final String testType;
  final int correct;
  final int total;
  final TestScore? pre; // the learner's pre-test, for the post-test result

  const GeneralOutcome(this.testType, this.correct, this.total, this.pre);

  int get percent => quizScorePercent(correct, total);
}

/// Grades a General test ([answers]: question id -> chosen option index; missing
/// = not answered, which counts as wrong) and saves it for upload. Each test is
/// taken once: the pre-test before any module, the post-test after all of them.
Future<GeneralOutcome> recordGeneralTest(LocalDatabase db,
    {required String testType, required Map<String, int> answers}) async {
  final before = (await loadLearning(db)).general;
  final allowed = testType == 'PRE' ? before.canTakePre : before.canTakePost;
  if (!allowed) throw StateError('this test is not open');
  final questions = (await db.getGeneralQuestions()).where((q) => q.correctIndex != null).toList();
  final correct = questions.where((q) => answers[q.id] == q.correctIndex).length;
  await db.insertGeneralAttempt(
    clientId: newClientId('general-${testType.toLowerCase()}'),
    testType: testType,
    correct: correct,
    total: questions.length,
    answersJson: jsonEncode([
      for (final q in questions) {'question_id': q.id, 'choice': answers[q.id]},
    ]),
  );
  return GeneralOutcome(testType, correct, questions.length, before.pre);
}

int _seq = 0;

String newClientId(String prefix) =>
    '$prefix-${DateTime.now().microsecondsSinceEpoch}-${(_seq++).toRadixString(36)}';

/// Plain-language state of a module, shown on cards and in the reader.
String stageLabel(ModuleStage stage) => switch (stage) {
      ModuleStage.locked => 'Locked',
      ModuleStage.reading => 'Open',
      ModuleStage.completed => 'Completed',
    };
