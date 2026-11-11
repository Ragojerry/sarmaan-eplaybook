import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../db/local_database.dart';
import '../learning/learning_service.dart';
import '../offline/content_sync_service.dart';
import '../theme/app_theme.dart';

/// The General pre-/post-test (since 2026-11 it replaces the per-module tests):
/// the same multiple-choice questions, one at a time with the options in the
/// printed order. The PRE-test is taken once before any module opens; the
/// POST-test once after every module is completed. Graded offline and uploaded
/// by the sync engine; the result shows the score only, not the answers.
class GeneralTestScreen extends ConsumerStatefulWidget {
  final String testType; // PRE or POST

  const GeneralTestScreen({super.key, required this.testType});

  @override
  ConsumerState<GeneralTestScreen> createState() => _GeneralTestScreenState();
}

class _Question {
  final String id;
  final String prompt;
  final List<String> options;

  _Question(CachedGeneralQuestionRow r)
      : id = r.id,
        prompt = r.prompt,
        options = (jsonDecode(r.optionsJson) as List).map((o) => o.toString()).toList();
}

class _GeneralTestScreenState extends ConsumerState<GeneralTestScreen> {
  List<_Question>? _qs;
  String? _blocked;
  final Map<String, int> _answers = {};
  int _index = 0;
  bool _submitting = false;
  GeneralOutcome? _outcome;

  bool get _isPre => widget.testType == 'PRE';
  String get _title => _isPre ? 'General pre-test' : 'General post-test';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final db = ref.read(localDatabaseProvider);
    final learning = await loadLearning(db);
    final g = learning.general;
    String? blocked;
    if (!g.active || g.questions == 0) {
      blocked = 'The General test is not available on this phone yet. Sync on Home when you are online.';
    } else if (_isPre && !g.canTakePre) {
      blocked = 'You have already taken the General pre-test. It is taken once.';
    } else if (!_isPre && !g.canTakePost) {
      blocked = g.post != null
          ? 'You have already taken the General post-test. It is taken once.'
          : 'The General post-test opens when you have completed all your modules '
              '(${g.modulesCompleted} of ${g.modulesTotal} so far).';
    }
    final rows = (await db.getGeneralQuestions()).where((q) => q.correctIndex != null).map(_Question.new).toList();
    if (mounted) {
      setState(() {
        _blocked = blocked;
        _qs = rows;
      });
    }
  }

  Future<void> _submit() async {
    setState(() => _submitting = true);
    try {
      final outcome =
          await recordGeneralTest(ref.read(localDatabaseProvider), testType: widget.testType, answers: Map.of(_answers));
      ref.invalidate(learningProvider);
      if (mounted) setState(() => _outcome = outcome);
    } catch (_) {
      if (mounted) setState(() => _blocked = 'This test is no longer open.');
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final qs = _qs;
    return Scaffold(
      backgroundColor: AppColors.sand,
      appBar: AppBar(title: Text(_title), leading: BackButton(onPressed: () => context.go('/modules'))),
      body: _outcome != null
          ? _result(_outcome!)
          : _blocked != null
              ? _message(_blocked!)
              : qs == null
                  ? const Center(child: CircularProgressIndicator())
                  : qs.isEmpty
                      ? _message('The General test is not available on this phone yet.')
                      : _question(qs),
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
              OutlinedButton(onPressed: () => context.go('/modules'), child: const Text('Back to modules')),
            ],
          ),
        ),
      );

  Widget _question(List<_Question> qs) {
    final q = qs[_index];
    final last = _index == qs.length - 1;
    final chosen = _answers[q.id];
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
              if (_index == 0)
                Padding(
                  padding: const EdgeInsets.only(bottom: 14),
                  child: Text(
                    _isPre
                        ? 'Answer what you already know. It is not a pass or fail: it is your starting point, '
                            'and you take it once. Your modules open after you submit.'
                        : 'The same questions as your pre-test, now that you have completed your modules. '
                            'You take it once.',
                    style: const TextStyle(fontSize: 12.5, height: 1.45, color: AppColors.textSecondary),
                  ),
                ),
              Text(
                'QUESTION ${_index + 1} OF ${qs.length} · CHOOSE ONE',
                style: const TextStyle(fontFamily: AppFonts.mono, fontSize: 10.5, letterSpacing: 0.6, color: AppColors.textSecondary),
              ),
              const SizedBox(height: 10),
              Text(
                q.prompt,
                style: const TextStyle(
                    fontFamily: AppFonts.serif, fontSize: 19, fontWeight: FontWeight.w600, height: 1.3, color: AppColors.tealDeep),
              ),
              const SizedBox(height: 16),
              for (var i = 0; i < q.options.length; i++)
                Padding(
                  padding: const EdgeInsets.only(bottom: 9),
                  child: InkWell(
                    onTap: () => setState(() => _answers[q.id] = i),
                    borderRadius: BorderRadius.circular(AppRadius.standard),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                      decoration: BoxDecoration(
                        color: chosen == i ? AppColors.tealSoft : AppColors.white,
                        borderRadius: BorderRadius.circular(AppRadius.standard),
                        border: Border.all(color: chosen == i ? AppColors.teal : AppColors.line, width: chosen == i ? 1.5 : 1),
                      ),
                      child: Row(
                        children: [
                          Icon(chosen == i ? Icons.radio_button_checked : Icons.radio_button_unchecked,
                              size: 18, color: chosen == i ? AppColors.teal : AppColors.textMuted),
                          const SizedBox(width: 10),
                          Expanded(child: Text(q.options[i], style: const TextStyle(fontSize: 13.5, color: AppColors.ink))),
                        ],
                      ),
                    ),
                  ),
                ),
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
                  onPressed: chosen == null || _submitting ? null : () => last ? _submit() : setState(() => _index++),
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

  Widget _result(GeneralOutcome o) {
    final pre = o.pre;
    return ListView(
      padding: const EdgeInsets.fromLTRB(22, 28, 22, 28),
      children: [
        Text(_isPre ? 'Your starting point' : 'Your result',
            style: const TextStyle(fontFamily: AppFonts.serif, fontSize: 21, fontWeight: FontWeight.w600, color: AppColors.tealDeep)),
        const SizedBox(height: 12),
        Text('${o.correct} of ${o.total} (${o.percent}%)',
            style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: AppColors.ink)),
        const SizedBox(height: 10),
        Text(
          _isPre
              ? 'Thank you. Your modules are now open. At the end of the training you will answer the same questions again.'
              : pre == null
                  ? 'Well done for completing the training.'
                  : 'Your pre-test was ${pre.correct} of ${pre.total} (${pre.percent}%). Well done for completing the training.',
          style: const TextStyle(fontSize: 13.5, height: 1.5, color: AppColors.textSecondary),
        ),
        const SizedBox(height: 22),
        FilledButton(
          onPressed: () => context.go('/modules'),
          style: FilledButton.styleFrom(backgroundColor: AppColors.tealDeep, foregroundColor: AppColors.sand),
          child: Text(_isPre ? 'Go to my modules' : 'Back to modules'),
        ),
      ],
    );
  }
}
