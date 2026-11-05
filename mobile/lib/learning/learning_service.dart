import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../db/local_database.dart';
import '../offline/content_sync_service.dart';
import '../quiz/quiz_grader.dart';
import '../sync/analytics_recorder.dart';
import 'learning_rules.dart';

/// The signed-in learner's modules (only those their learner role may see)
/// with each one's pre-test / reading / post-test state, read from the local
/// database so it works offline.
class LearningSnapshot {
  final List<CachedModuleRow> modules;
  final Map<String, ModuleLearning> byId;

  const LearningSnapshot(this.modules, this.byId);

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

/// Attempts that count: pre/post (not legacy) and not rejected by the server.
bool attemptCounts(LocalQuizAttemptRow a) => (a.testType == 'PRE' || a.testType == 'POST') && a.serverValid != false;

TestScore scoreOf(LocalQuizAttemptRow a) => TestScore(
      clientId: a.clientId,
      testType: a.testType,
      correct: a.correctCount,
      total: a.totalCount,
      takenAt: a.takenAt,
    );

Future<LearningSnapshot> loadLearning(LocalDatabase db) async {
  final modules = await db.getAllModules();
  final usages = await db.questionUsagesByModule();
  final progress = {for (final p in await db.getAllProgress()) p.moduleId: p};
  final attempts = (await db.getQuizAttempts()).where(attemptCounts).toList();
  final states = computeLearning(autoApprovePercent: await db.getAutoApprovePercent(), [
    for (final m in modules)
      ModuleInput(
        moduleId: m.id,
        questionUsages: usages[m.id] ?? const [],
        completed: progress[m.id]?.completed ?? false,
        readingDone: progress[m.id]?.readingCompletedAt != null,
        attempts: [for (final a in attempts) if (a.moduleId == m.id) scoreOf(a)],
      ),
  ]);
  return LearningSnapshot(modules, {for (final s in states) s.moduleId: s});
}

/// autoDispose: re-read whenever a screen opens, so it is never stale.
final learningProvider = FutureProvider.autoDispose<LearningSnapshot>((ref) => loadLearning(ref.read(localDatabaseProvider)));

/// What happened when a test was submitted.
class TestOutcome {
  final String testType;
  final int correct;
  final int total;
  final ModuleLearning before;
  final ModuleLearning after;

  const TestOutcome(this.testType, this.correct, this.total, this.before, this.after);

  int get percent => quizScorePercent(correct, total);
  bool get reachedPassMark => quizPassed(correct, total);

  /// The pre-test was 100%: the auto-approval threshold is the only rule.
  bool get autoApproval => after.prePerfect;
  bool get reachedAutoApproval => reaches(correct, total, after.autoApprovePercent);
  bool get beatPreTest {
    final pre = after.pre;
    return pre != null && beats(correct, total, pre.correct, pre.total);
  }

  bool get completedNow => !before.completed && after.completed;
}

/// Saves one attempt locally (uploaded by the sync engine), and when a
/// post-test meets both rules completes the module at once, offline too; the
/// server confirms the same decision when the attempt reaches it.
Future<TestOutcome> recordTestAttempt(
  LocalDatabase db, {
  required String moduleId,
  required String testType,
  required int correct,
  required int total,
  required String resultsJson,
  required String clientId,
}) async {
  final before = (await loadLearning(db)).of(moduleId);
  if (before == null) throw StateError('module not available');
  final allowed = testType == 'PRE' ? before.canTakePreTest : before.canTakePostTest;
  if (!allowed) throw StateError('this test is not open');
  await db.insertQuizAttempt(
    moduleId: moduleId,
    clientId: clientId,
    correct: correct,
    total: total,
    scorePercent: quizScorePercent(correct, total),
    passed: quizPassed(correct, total),
    resultsJson: resultsJson,
    testType: testType,
  );
  var after = (await loadLearning(db)).of(moduleId)!;
  if (testType == 'POST' && !after.completed && after.completingPost != null) {
    await db.upsertProgress(moduleId: moduleId, progressPercent: 100, completed: true);
    await db.enqueueSync(
      'progress',
      jsonEncode({'module_id': moduleId, 'completed': true, 'completed_at': DateTime.now().toUtc().toIso8601String()}),
    );
    await recordAnalyticsEvent(db, 'MODULE_COMPLETE', moduleId: moduleId);
    after = (await loadLearning(db)).of(moduleId)!;
  }
  return TestOutcome(testType, correct, total, before, after);
}

/// Plain-language next step for a module's state, shown on cards and in the reader.
String stageLabel(ModuleStage stage) => switch (stage) {
      ModuleStage.locked => 'Locked',
      ModuleStage.preTest => 'Pre-test first',
      ModuleStage.reading => 'Reading',
      ModuleStage.postTest => 'Post-test ready',
      ModuleStage.completed => 'Completed',
    };
