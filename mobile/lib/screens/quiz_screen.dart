import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../db/local_database.dart';
import '../learning/learning_rules.dart';
import '../learning/learning_service.dart';
import '../offline/content_sync_service.dart';
import '../quiz/quiz_grader.dart';
import '../sync/sync_engine.dart';
import '../theme/app_theme.dart';
import '../widgets/offline_aware_image.dart';

/// One question plus the learner's in-progress answer. Option/right-hand/item
/// order is shuffled per attempt; answers are kept in ORIGINAL index space so
/// they grade exactly like the vectors.
class _Q {
  final String id;
  final String type;
  final String prompt;
  final String? explanation;
  final Map<String, dynamic> content;

  late List<int> order; // display order (options, right-hand sides, or the learner's sequence)
  int? choice;
  final Set<int> picks = {};
  bool? tf;
  late List<int?> matches;
  final TextEditingController numeric = TextEditingController();

  _Q(CachedQuizQuestionRow row, Random rng)
      : id = row.id,
        type = row.questionType,
        prompt = row.prompt,
        explanation = row.explanation,
        content = Map<String, dynamic>.from(jsonDecode(row.contentJson) as Map) {
    final n = switch (type) {
      'MATCHING' => (content['pairs'] as List).length,
      'ORDERING' => (content['items'] as List).length,
      'MULTIPLE_CHOICE' || 'IMAGE_CHOICE' || 'MULTIPLE_SELECT' => (content['options'] as List).length,
      _ => 0,
    };
    order = List<int>.generate(n, (i) => i);
    if (n > 1) {
      // A sequence question must not start already solved.
      for (var tries = 0; tries < 8; tries++) {
        order.shuffle(rng);
        final solved = List<int>.generate(n, (i) => i);
        if (type != 'ORDERING' || !_same(order, solved)) break;
      }
    }
    matches = List<int?>.filled(type == 'MATCHING' ? n : 0, null);
  }

  static bool _same(List<int> a, List<int> b) {
    for (var i = 0; i < a.length; i++) {
      if (a[i] != b[i]) return false;
    }
    return true;
  }

  List<String> get options => (content['options'] as List).cast<String>();
  List<Map<String, dynamic>> get pairs => (content['pairs'] as List).cast<Map<String, dynamic>>();
  List<String> get items => (content['items'] as List).cast<String>();

  double? get numericValue => double.tryParse(numeric.text.trim().replaceAll(',', '.'));

  bool get answered => switch (type) {
        'MULTIPLE_CHOICE' || 'IMAGE_CHOICE' => choice != null,
        'TRUE_FALSE' => tf != null,
        'MULTIPLE_SELECT' => picks.isNotEmpty,
        'MATCHING' => matches.every((m) => m != null),
        'ORDERING' => true,
        'NUMERIC' => numericValue != null,
        _ => false,
      };

  Object? get answer => switch (type) {
        'MULTIPLE_CHOICE' || 'IMAGE_CHOICE' => choice,
        'TRUE_FALSE' => tf,
        'MULTIPLE_SELECT' => (picks.toList()..sort()),
        'MATCHING' => [for (final m in matches) m ?? -1],
        'ORDERING' => List<int>.from(order),
        'NUMERIC' => numericValue,
        _ => null,
      };

  bool get correct => isQuestionCorrect(type, content, answer);

  String _num(num v) => v == v.truncateToDouble() ? v.toInt().toString() : v.toString();

  String describe(Object? a) {
    switch (type) {
      case 'MULTIPLE_CHOICE':
      case 'IMAGE_CHOICE':
        return a is int && a >= 0 && a < options.length ? options[a] : '—';
      case 'TRUE_FALSE':
        return a is bool ? (a ? 'True' : 'False') : '—';
      case 'MULTIPLE_SELECT':
        return a is List && a.isNotEmpty ? a.map((i) => options[i as int]).join('\n') : '—';
      case 'MATCHING':
        if (a is! List) return '—';
        return [
          for (var i = 0; i < pairs.length; i++)
            '${pairs[i]['left']} → ${a[i] is int && (a[i] as int) >= 0 ? pairs[a[i] as int]['right'] : '—'}',
        ].join('\n');
      case 'ORDERING':
        if (a is! List) return '—';
        return [for (var i = 0; i < a.length; i++) '${i + 1}. ${items[a[i] as int]}'].join('\n');
      case 'NUMERIC':
        final unit = content['unit'];
        return a is num ? '${_num(a)}${unit is String && unit.isNotEmpty ? ' $unit' : ''}' : '—';
    }
    return '—';
  }

  String describeCorrect() {
    switch (type) {
      case 'MATCHING':
        return describe(List<int>.generate(pairs.length, (i) => i));
      case 'ORDERING':
        return describe(List<int>.generate(items.length, (i) => i));
      default:
        return describe(content['correct']);
    }
  }
}

/// The pre-test (before reading; score only, no answers shown, since the
/// same questions may come back in the post-test) or the post-test (after
/// reading; completes the module when it reaches 90% and beats the pre-test).
/// Works offline: the attempt is saved on the phone and uploaded later.
class QuizScreen extends ConsumerStatefulWidget {
  final String moduleId;

  /// PRE or POST.
  final String testType;
  const QuizScreen({super.key, required this.moduleId, this.testType = 'POST'});

  @override
  ConsumerState<QuizScreen> createState() => _QuizScreenState();
}

class _QuizScreenState extends ConsumerState<QuizScreen> {
  final _rng = Random();
  List<_Q>? _qs;
  int _index = 0;
  bool _submitting = false;
  String? _blocked; // why this test cannot be taken now
  TestOutcome? _outcome;
  String? _nextModuleId;
  String? _nextModuleTitle;

  bool get _isPre => widget.testType == 'PRE';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final db = ref.read(localDatabaseProvider);
    final learning = await loadLearning(db);
    final state = learning.of(widget.moduleId);
    String? blocked;
    if (state == null) {
      blocked = 'This module is not part of your current training. Go back to Modules to continue.';
    } else if (state.stage == ModuleStage.locked) {
      blocked = 'Complete ${learning.blockerOf(widget.moduleId)?.title ?? 'the previous module'} first.';
    } else if (_isPre && !state.canTakePreTest) {
      blocked = state.pre != null
          ? 'You have already taken the pre-test (${state.pre!.percent}%). It is taken once, before reading.'
          : 'This module has no pre-test.';
    } else if (!_isPre && !state.canTakePostTest) {
      blocked = state.completed
          ? 'You have completed this module. Your result is kept and cannot be changed; you can still re-read the module.'
          : state.pre == null
              ? 'Take the pre-test first, then read the module.'
              : 'Read the module to the end first. The post-test opens after reading.';
    }
    final rows = blocked == null ? await db.getQuizQuestions(widget.moduleId, testType: widget.testType) : const <CachedQuizQuestionRow>[];
    // Starting the post-test takes the module to 80% (never lowers it).
    if (!_isPre && rows.isNotEmpty) await db.raiseProgress(widget.moduleId, LocalDatabase.quizStartedPercent);
    if (!mounted) return;
    setState(() {
      _blocked = blocked;
      _qs = [for (final r in rows) _Q(r, _rng)];
      _index = 0;
      _outcome = null;
    });
  }

  @override
  void dispose() {
    for (final q in _qs ?? const <_Q>[]) {
      q.numeric.dispose();
    }
    super.dispose();
  }

  Future<void> _submit() async {
    final qs = _qs!;
    setState(() => _submitting = true);
    final db = ref.read(localDatabaseProvider);
    final correct = qs.where((q) => q.correct).length;
    final clientId = '${_isPre ? 'pre' : 'post'}-${DateTime.now().microsecondsSinceEpoch}-${_rng.nextInt(1 << 32).toRadixString(36)}';
    TestOutcome outcome;
    try {
      outcome = await recordTestAttempt(
        db,
        moduleId: widget.moduleId,
        testType: widget.testType,
        correct: correct,
        total: qs.length,
        clientId: clientId,
        resultsJson: jsonEncode([for (final q in qs) {'question_id': q.id, 'correct': q.correct}]),
      );
    } on StateError {
      if (mounted) setState(() => _submitting = false);
      await _load(); // the state changed underneath (e.g. a sync); show why
      return;
    }
    String? nextId;
    String? nextTitle;
    if (outcome.completedNow) {
      final after = await loadLearning(db);
      final i = after.modules.indexWhere((m) => m.id == widget.moduleId);
      if (i >= 0 && i + 1 < after.modules.length) {
        nextId = after.modules[i + 1].id;
        nextTitle = after.modules[i + 1].title;
      }
    }
    ref.invalidate(learningProvider);
    // Upload now if we can; otherwise the sync engine retries automatically.
    unawaited(ref.read(syncEngineProvider.notifier).syncNow().catchError((_) {}));
    if (!mounted) return;
    setState(() {
      _submitting = false;
      _outcome = outcome;
      _nextModuleId = nextId;
      _nextModuleTitle = nextTitle;
    });
  }

  @override
  Widget build(BuildContext context) {
    final qs = _qs;
    return Scaffold(
      backgroundColor: AppColors.sand,
      appBar: AppBar(
        title: Text(_isPre ? 'Pre-test' : 'Post-test'),
        leading: BackButton(onPressed: () => context.go('/reader/${widget.moduleId}')),
      ),
      body: _blocked != null
          ? _message(_blocked!)
          : qs == null
              ? const Center(child: CircularProgressIndicator())
              : qs.isEmpty
                  ? _message('This module has no test on this phone yet.')
                  : _outcome != null
                      ? (_isPre ? _buildPreResult(_outcome!) : _buildResult(qs, _outcome!))
                      : _buildQuestion(qs),
    );
  }

  Widget _message(String text) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(text, textAlign: TextAlign.center, style: const TextStyle(fontSize: 14, height: 1.45, color: AppColors.ink)),
              const SizedBox(height: 16),
              OutlinedButton(onPressed: () => context.go('/reader/${widget.moduleId}'), child: const Text('Back to module')),
            ],
          ),
        ),
      );

  // ---------------------------------------------------------------- question

  Widget _buildQuestion(List<_Q> qs) {
    final q = qs[_index];
    final last = _index == qs.length - 1;
    return Column(
      children: [
        LinearProgressIndicator(
          value: (_index + 1) / qs.length,
          minHeight: 4,
          backgroundColor: AppColors.sandDeep,
          valueColor: const AlwaysStoppedAnimation(AppColors.teal),
        ),
        Expanded(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(22, 20, 22, 20),
            children: [
              Text(
                'QUESTION ${_index + 1} OF ${qs.length} · ${_typeLabel(q.type)}',
                style: const TextStyle(
                  fontFamily: AppFonts.mono, fontSize: 10.5, letterSpacing: 0.6, color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                q.prompt,
                style: const TextStyle(fontFamily: AppFonts.serif, fontSize: 19, fontWeight: FontWeight.w600, height: 1.3, color: AppColors.tealDeep),
              ),
              const SizedBox(height: 16),
              _answerArea(q),
            ],
          ),
        ),
        SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(22, 8, 22, 12),
            child: Row(
              children: [
                if (_index > 0)
                  OutlinedButton(onPressed: () => setState(() => _index--), child: const Text('Back'))
                else
                  const SizedBox.shrink(),
                const Spacer(),
                FilledButton(
                  onPressed: !q.answered || _submitting
                      ? null
                      : () => last ? _submit() : setState(() => _index++),
                  style: FilledButton.styleFrom(backgroundColor: AppColors.tealDeep, foregroundColor: AppColors.sand),
                  child: Text(last ? (_submitting ? 'Submitting…' : 'Submit') : 'Next'),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  static String _typeLabel(String t) => switch (t) {
        'MULTIPLE_CHOICE' => 'CHOOSE ONE',
        'TRUE_FALSE' => 'TRUE OR FALSE',
        'MULTIPLE_SELECT' => 'SELECT ALL THAT APPLY',
        'MATCHING' => 'MATCH THE PAIRS',
        'ORDERING' => 'PUT IN ORDER',
        'IMAGE_CHOICE' => 'LOOK AND CHOOSE',
        'NUMERIC' => 'TYPE THE NUMBER',
        _ => 'QUESTION',
      };

  Widget _answerArea(_Q q) {
    switch (q.type) {
      case 'MULTIPLE_CHOICE':
      case 'IMAGE_CHOICE':
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (q.type == 'IMAGE_CHOICE' && q.content['media_asset_id'] is String)
              Padding(
                padding: const EdgeInsets.only(bottom: 14),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(AppRadius.standard),
                  child: SizedBox(
                    height: 190,
                    width: double.infinity,
                    child: OfflineAwareImage(mediaAssetId: q.content['media_asset_id'] as String, fit: BoxFit.cover),
                  ),
                ),
              ),
            for (final i in q.order)
              _optionTile(
                label: q.options[i],
                selected: q.choice == i,
                multi: false,
                onTap: () => setState(() => q.choice = i),
              ),
          ],
        );
      case 'TRUE_FALSE':
        return Column(
          children: [
            _optionTile(label: 'True', selected: q.tf == true, multi: false, onTap: () => setState(() => q.tf = true)),
            _optionTile(label: 'False', selected: q.tf == false, multi: false, onTap: () => setState(() => q.tf = false)),
          ],
        );
      case 'MULTIPLE_SELECT':
        return Column(
          children: [
            for (final i in q.order)
              _optionTile(
                label: q.options[i],
                selected: q.picks.contains(i),
                multi: true,
                onTap: () => setState(() => q.picks.contains(i) ? q.picks.remove(i) : q.picks.add(i)),
              ),
          ],
        );
      case 'MATCHING':
        return Column(
          children: [
            for (var i = 0; i < q.pairs.length; i++)
              Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.white,
                  borderRadius: BorderRadius.circular(AppRadius.standard),
                  border: Border.all(color: AppColors.line),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(q.pairs[i]['left'] as String, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.ink)),
                    const SizedBox(height: 6),
                    DropdownButton<int>(
                      isExpanded: true,
                      value: q.matches[i],
                      hint: const Text('Choose the match…'),
                      items: [
                        for (final r in q.order)
                          // a right-hand side already used by another row is not offered again
                          if (r == q.matches[i] || !q.matches.contains(r))
                            DropdownMenuItem(value: r, child: Text(q.pairs[r]['right'] as String, overflow: TextOverflow.ellipsis, maxLines: 2)),
                      ],
                      onChanged: (v) => setState(() => q.matches[i] = v),
                    ),
                  ],
                ),
              ),
          ],
        );
      case 'ORDERING':
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Drag the handles to arrange the steps in the correct order.',
                style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
            const SizedBox(height: 10),
            ReorderableListView(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              onReorder: (from, to) => setState(() {
                if (to > from) to--;
                q.order.insert(to, q.order.removeAt(from));
              }),
              children: [
                for (var pos = 0; pos < q.order.length; pos++)
                  Container(
                    key: ValueKey('${q.id}-${q.order[pos]}'),
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                    decoration: BoxDecoration(
                      color: AppColors.white,
                      borderRadius: BorderRadius.circular(AppRadius.standard),
                      border: Border.all(color: AppColors.line),
                    ),
                    child: Row(
                      children: [
                        Text('${pos + 1}', style: const TextStyle(fontFamily: AppFonts.mono, color: AppColors.textMuted)),
                        const SizedBox(width: 12),
                        Expanded(child: Text(q.items[q.order[pos]], style: const TextStyle(color: AppColors.ink, height: 1.3))),
                        ReorderableDragStartListener(
                          index: pos,
                          child: const Icon(Icons.drag_handle, color: AppColors.textMuted),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ],
        );
      case 'NUMERIC':
        final unit = q.content['unit'];
        return TextField(
          controller: q.numeric,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          onChanged: (_) => setState(() {}),
          decoration: InputDecoration(
            hintText: 'Type your answer',
            suffixText: unit is String && unit.isNotEmpty ? unit : null,
            filled: true,
            fillColor: AppColors.white,
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(AppRadius.standard)),
          ),
        );
    }
    return const SizedBox.shrink();
  }

  Widget _optionTile({required String label, required bool selected, required bool multi, required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
        decoration: BoxDecoration(
          color: selected ? AppColors.tealSoft : AppColors.white,
          borderRadius: BorderRadius.circular(AppRadius.standard),
          border: Border.all(color: selected ? AppColors.teal : AppColors.line, width: selected ? 1.6 : 1),
        ),
        child: Row(
          children: [
            Icon(
              multi
                  ? (selected ? Icons.check_box : Icons.check_box_outline_blank)
                  : (selected ? Icons.radio_button_checked : Icons.radio_button_unchecked),
              size: 20,
              color: selected ? AppColors.teal : AppColors.textMuted,
            ),
            const SizedBox(width: 12),
            Expanded(child: Text(label, style: const TextStyle(fontSize: 14, height: 1.35, color: AppColors.ink))),
          ],
        ),
      ),
    );
  }

  // ------------------------------------------------------------------ result

  /// Pre-test: the score is the learner's starting point. No answers are
  /// shown, because the same questions may be in the post-test.
  Widget _buildPreResult(TestOutcome o) {
    final perfect = isPerfect(o.correct, o.total);
    return ListView(
      padding: const EdgeInsets.fromLTRB(22, 22, 22, 28),
      children: [
        Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(color: AppColors.tealDeep, borderRadius: BorderRadius.circular(AppRadius.medium)),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Pre-test done',
                  style: TextStyle(fontFamily: AppFonts.serif, fontSize: 24, fontWeight: FontWeight.w700, color: AppColors.sand)),
              const SizedBox(height: 4),
              Text('${o.correct} of ${o.total} correct · ${o.percent}%',
                  style: const TextStyle(fontFamily: AppFonts.mono, fontSize: 13, color: AppColors.sand)),
              const SizedBox(height: 8),
              Text(
                perfect
                    ? 'You already know this module well. Now read the module. When you reach the end, a post-test of '
                        '${o.after.autoApprovePercent}% or more completes it automatically.'
                    : 'This is your starting point, not a pass or fail. Now read the module. The post-test opens when you '
                        'reach the end: you need at least $kQuizPassMark% and more than ${o.percent}% to complete the module.',
                style: const TextStyle(fontSize: 13, height: 1.45, color: AppColors.sand),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        FilledButton(
          onPressed: () => context.go('/reader/${widget.moduleId}'),
          style: FilledButton.styleFrom(backgroundColor: AppColors.tealDeep, foregroundColor: AppColors.sand),
          child: const Text('Read the module'),
        ),
      ],
    );
  }

  /// Post-test: both conditions, whether each was met, and what to do next.
  Widget _buildResult(List<_Q> qs, TestOutcome o) {
    final done = o.after.completed;
    final pre = o.after.pre;
    Widget check(bool ok, String text) => Padding(
          padding: const EdgeInsets.only(top: 6),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(ok ? Icons.check_circle : Icons.cancel, size: 18, color: done ? AppColors.sand : (ok ? AppColors.teal : AppColors.danger)),
              const SizedBox(width: 8),
              Expanded(
                child: Text(text, style: TextStyle(fontSize: 13, height: 1.35, color: done ? AppColors.sand : AppColors.calloutWarningText)),
              ),
            ],
          ),
        );
    final String next;
    if (done) {
      next = _nextModuleTitle != null ? 'The next module is now unlocked.' : 'You have completed this module.';
    } else if (o.autoApproval) {
      next = 'You need at least ${o.after.autoApprovePercent}%. Look at the answers below, re-read the module, and try '
          'the post-test again.';
    } else if (!o.reachedPassMark) {
      next = 'You need at least $kQuizPassMark%. Look at the answers below, re-read the module, and try the post-test again.';
    } else {
      next = 'You reached $kQuizPassMark%, but you need more than your pre-test score (${pre?.percent ?? 0}%). '
          'Re-read the parts you missed and try the post-test again.';
    }
    return ListView(
      padding: const EdgeInsets.fromLTRB(22, 22, 22, 28),
      children: [
        Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: done ? AppColors.tealDeep : AppColors.claySoft,
            borderRadius: BorderRadius.circular(AppRadius.medium),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                done ? 'Module complete' : 'Not yet',
                style: TextStyle(
                  fontFamily: AppFonts.serif, fontSize: 24, fontWeight: FontWeight.w700,
                  color: done ? AppColors.sand : AppColors.calloutWarningText,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                '${o.correct} of ${o.total} correct · ${o.percent}%',
                style: TextStyle(fontFamily: AppFonts.mono, fontSize: 13, color: done ? AppColors.sand : AppColors.calloutWarningText),
              ),
              const SizedBox(height: 6),
              if (o.autoApproval)
                // A 100% pre-test cannot be beaten: the threshold is the only rule.
                check(o.reachedAutoApproval,
                    'At least ${o.after.autoApprovePercent}% after a 100% pre-test: completes automatically (you scored ${o.percent}%)')
              else ...[
                check(o.reachedPassMark, 'At least $kQuizPassMark% (you scored ${o.percent}%)'),
                check(o.beatPreTest, 'Higher than your pre-test (${pre?.percent ?? 0}%)'),
              ],
              const SizedBox(height: 10),
              Text(next, style: TextStyle(fontSize: 13, height: 1.4, color: done ? AppColors.sand : AppColors.calloutWarningText)),
            ],
          ),
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            if (!done)
              Expanded(
                child: FilledButton(
                  onPressed: _load,
                  style: FilledButton.styleFrom(backgroundColor: AppColors.tealDeep, foregroundColor: AppColors.sand),
                  child: const Text('Try again'),
                ),
              ),
            if (done && _nextModuleId != null)
              Expanded(
                child: FilledButton(
                  onPressed: () => context.go('/reader/$_nextModuleId'),
                  style: FilledButton.styleFrom(backgroundColor: AppColors.tealDeep, foregroundColor: AppColors.sand),
                  child: const Text('Next module'),
                ),
              ),
            const SizedBox(width: 10),
            Expanded(
              child: OutlinedButton(
                onPressed: () => context.go('/reader/${widget.moduleId}'),
                child: Text(done ? 'Back to module' : 'Re-read the module'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 22),
        const Text(
          'REVIEW',
          style: TextStyle(fontFamily: AppFonts.sans, fontSize: 11, fontWeight: FontWeight.w800, letterSpacing: 0.9, color: AppColors.textSecondary),
        ),
        const SizedBox(height: 10),
        for (var i = 0; i < qs.length; i++) _reviewCard(i, qs[i]),
      ],
    );
  }

  Widget _reviewCard(int i, _Q q) {
    final ok = q.correct;
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(13),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(AppRadius.medium),
        border: Border.all(color: ok ? AppColors.teal : AppColors.danger.withValues(alpha: 0.6)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(ok ? Icons.check_circle : Icons.cancel, size: 18, color: ok ? AppColors.teal : AppColors.danger),
              const SizedBox(width: 8),
              Expanded(
                child: Text('${i + 1}. ${q.prompt}', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, height: 1.35, color: AppColors.ink)),
              ),
            ],
          ),
          if (!ok) ...[
            const SizedBox(height: 8),
            Text('Your answer', style: const TextStyle(fontSize: 10.5, fontWeight: FontWeight.w700, color: AppColors.textMuted)),
            Text(q.describe(q.answer), style: const TextStyle(fontSize: 12.5, color: AppColors.danger, height: 1.35)),
          ],
          const SizedBox(height: 8),
          const Text('Correct answer', style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.w700, color: AppColors.textMuted)),
          Text(q.describeCorrect(), style: const TextStyle(fontSize: 12.5, color: AppColors.calloutGoodText, height: 1.35)),
          if (q.explanation != null && q.explanation!.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(q.explanation!, style: const TextStyle(fontSize: 11.5, color: AppColors.textSecondary, height: 1.4)),
          ],
        ],
      ),
    );
  }
}
