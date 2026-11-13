import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../db/local_database.dart';
import '../offline/content_sync_service.dart';
import '../quiz/quiz_grader.dart';
import '../sync/analytics_recorder.dart';
import 'learning_rules.dart';
import '../l10n/l10n.dart';

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

/// Server refusals that only mean "arrived before the completion that opened it"
/// (backend app/learning/revalidate.py). The server re-checks them once that
/// completion arrives, so the phone keeps counting them meanwhile: a learner who
/// passed is never sent back to retake a quiz or the post-test because of upload order.
const kOrderOnlyReasons = {
  'take the General pre-test first',
  'module is locked: complete the previous module first',
  'complete all your modules first',
};

bool _refusedForGood(bool? serverValid, String? reason) => serverValid == false && !kOrderOnlyReasons.contains(reason);

/// Module-quiz attempts that count: not rejected by the server for good. (PRE/POST
/// and LEGACY rows are the retired per-module tests: history only.)
bool attemptCounts(LocalQuizAttemptRow a) => a.testType == 'MODULE_QUIZ' && !_refusedForGood(a.serverValid, a.invalidReason);

/// General pre/post-test attempts that count (the same rule).
bool generalAttemptCounts(LocalGeneralAttemptRow a) => !_refusedForGood(a.serverValid, a.invalidReason);

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
      passMark: a.passMark,
    );

/// app_settings key: this learner's current General pass mark, from GET /sync/learning.
const kGeneralPassMarkKey = 'general_pass_mark';

/// The pass mark a General test taken now is graded against.
Future<int> currentGeneralPassMark(LocalDatabase db) async {
  final stored = int.tryParse(await db.getSetting(kGeneralPassMarkKey) ?? '');
  return (stored != null && stored >= 1 && stored <= 100) ? stored : defaultGeneralPassMark(db.activeLearnerRole);
}

Future<LearningSnapshot> loadLearning(LocalDatabase db) async {
  final modules = await db.getAllModules();
  final quizCounts = await db.quizStatementCountsByModule();
  final progress = {for (final p in await db.getAllProgress()) p.moduleId: p};
  final attempts = (await db.getQuizAttempts()).where(attemptCounts).toList();
  final generalAttempts = [
    for (final a in await db.getGeneralAttempts())
      if (generalAttemptCounts(a)) generalScoreOf(a),
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

/// The outcome of one module-quiz attempt. [correct] is the effective score: the
/// statements answered correctly now plus those kept from earlier attempts.
class QuizResult {
  final int correct;
  final int total;
  final bool passed;
  final bool completedModuleQuiz; // the module's quiz is passed now (this or an earlier attempt)

  const QuizResult(this.correct, this.total, this.passed, this.completedModuleQuiz);

  /// Statements still wrong, asked again at the next try.
  int get remaining => total - correct;
}

/// Statements of [moduleId] already answered correctly in the latest counted attempt,
/// while its quiz is not passed yet: a retry asks only the others, and these keep
/// their credit. Empty when there is no attempt, the quiz is passed or the module is
/// completed (attempts restored from the server carry no per-statement detail).
Future<Set<String>> quizCredit(LocalDatabase db, String moduleId) async {
  final state = (await loadLearning(db)).of(moduleId);
  if (state == null || state.completed || state.quizPassed) return {};
  final mine = (await db.getQuizAttempts()).where((a) => a.moduleId == moduleId && attemptCounts(a)).toList()
    ..sort((a, b) => a.takenAt.compareTo(b.takenAt));
  if (mine.isEmpty) return {};
  try {
    final results = (jsonDecode(mine.last.resultsJson) as List).cast<Map<String, dynamic>>();
    return {for (final r in results) if (r['correct'] == true) r['question_id'] as String};
  } catch (_) {
    return {};
  }
}

/// Grades one attempt at a module's inline quiz ([answers]: section id -> the
/// learner's True/False for the statements shown) against the cached statements and
/// saves it for upload. A retry shows only the statements still wrong: the others keep
/// their credit from the latest attempt ([quizCredit]), so the attempt's score is the
/// effective score, graded with the unchanged pass rule. Each attempt records which
/// statements were shown and the answers. Retakes are unlimited until the module is
/// completed; every attempt is kept.
Future<QuizResult> recordModuleQuiz(LocalDatabase db, {required String moduleId, required Map<String, bool> answers}) async {
  final before = (await loadLearning(db)).of(moduleId);
  if (before == null) throw StateError('module not available');
  if (!before.canTakeQuiz) throw StateError('the quiz is not open');
  final statements = (await db.getSectionsForModule(moduleId)).map(QuizStatement.fromSection).whereType<QuizStatement>().toList();
  final credit = await quizCredit(db, moduleId);
  final results = [
    for (final q in statements)
      if (credit.contains(q.sectionId) && !answers.containsKey(q.sectionId))
        {'question_id': q.sectionId, 'correct': true, 'shown': false}
      else
        {
          'question_id': q.sectionId,
          'correct': answers[q.sectionId] == q.answer,
          'shown': true,
          if (answers[q.sectionId] != null) 'answer': answers[q.sectionId],
        },
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
  if (state == null) return L10n.t('learning.notAvailable');
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
    return s.lockedByGeneralTest ? L10n.t('learning.takePreTestFirst') : L10n.t('learning.previousModuleFirst');
  }
  if (!s.quizPassed) return L10n.t('learning.passQuizFirst');
  if (!s.timeMet) {
    return L10n.t('learning.spendMoreTime', {'minimum': formatDuration(s.minSeconds), 'left': formatDuration(s.secondsLeft)});
  }
  return null;
}

/// The outcome of a General test.
class GeneralOutcome {
  final String testType;
  final int correct;
  final int total;
  final TestScore? pre; // the learner's pre-test, for the post-test result
  final int passMark; // stored with the attempt: a later change never alters this result

  const GeneralOutcome(this.testType, this.correct, this.total, this.pre, {this.passMark = 80});

  int get percent => quizScorePercent(correct, total);
  bool get passed => generalPasses(correct, total, passMark);
  int get needed => generalNeeded(total, passMark);
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
  final passMark = await currentGeneralPassMark(db);
  await db.insertGeneralAttempt(
    passMark: passMark,
    clientId: newClientId('general-${testType.toLowerCase()}'),
    testType: testType,
    correct: correct,
    total: questions.length,
    answersJson: jsonEncode([
      for (final q in questions) {'question_id': q.id, 'choice': answers[q.id]},
    ]),
  );
  return GeneralOutcome(testType, correct, questions.length, before.pre, passMark: passMark);
}

int _seq = 0;

String newClientId(String prefix) =>
    '$prefix-${DateTime.now().microsecondsSinceEpoch}-${(_seq++).toRadixString(36)}';

/// Plain-language state of a module, shown on cards and in the reader.
String stageLabel(ModuleStage stage) => switch (stage) {
      ModuleStage.locked => L10n.t('stage.locked'),
      ModuleStage.reading => L10n.t('stage.open'),
      ModuleStage.completed => L10n.t('stage.completed'),
    };
