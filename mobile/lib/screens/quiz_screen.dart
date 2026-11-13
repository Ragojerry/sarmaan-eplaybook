import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../db/local_database.dart';
import '../learning/learning_service.dart';
import '../offline/content_sync_service.dart';
import '../theme/app_theme.dart';
import '../l10n/l10n.dart';

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
      blocked = L10n.t('general.notOnPhoneSync');
    } else if (_isPre && !g.canTakePre) {
      blocked = L10n.t('general.preAlreadyTaken');
    } else if (!_isPre && !g.canTakePost) {
      blocked = g.post != null
          ? L10n.t('general.postAlreadyTaken')
          : L10n.t('general.postOpensLater', {'done': g.modulesCompleted, 'modules': g.modulesTotal});
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
      if (mounted) setState(() => _blocked = L10n.t('general.noLongerOpen'));
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final qs = _qs;
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
          title: Text(_isPre ? context.t('general.preTestTitle') : context.t('general.postTitle')),
          leading: BackButton(onPressed: () => context.go('/modules'))),
      body: _outcome != null
          ? _result(_outcome!)
          : _blocked != null
              ? _message(_blocked!)
              : qs == null
                  ? const Center(child: CircularProgressIndicator())
                  : qs.isEmpty
                      ? _message(context.t('general.notOnPhone'))
                      : _question(qs),
    );
  }

  Widget _message(String text) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(text, textAlign: TextAlign.center, style: const TextStyle(fontSize: 14, height: 1.45, color: AppColors.textStrong)),
              const SizedBox(height: 16),
              OutlinedButton(onPressed: () => context.go('/modules'), child: Text(context.t('reader.backToModules'))),
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
          backgroundColor: AppColors.progressTrack,
          valueColor: const AlwaysStoppedAnimation(AppColors.primary),
        ),
        Expanded(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(22, 20, 22, 20),
            children: [
              if (_index == 0)
                Padding(
                  padding: const EdgeInsets.only(bottom: 14),
                  child: Text(
                    _isPre ? context.t('general.preIntro') : context.t('general.postIntro'),
                    style: const TextStyle(fontSize: 12.5, height: 1.45, color: AppColors.textMuted),
                  ),
                ),
              Text(
                context.t('general.questionOf', {'number': _index + 1, 'total': qs.length}),
                style: const TextStyle(fontFamily: AppFonts.mono, fontSize: 10.5, letterSpacing: 0.6, color: AppColors.textMuted),
              ),
              const SizedBox(height: 10),
              Text(
                q.prompt,
                style: const TextStyle(
                    fontFamily: AppFonts.serif, fontSize: 19, fontWeight: FontWeight.w600, height: 1.3, color: AppColors.primaryText),
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
                        color: chosen == i ? AppColors.surfaceSelected : AppColors.surface,
                        borderRadius: BorderRadius.circular(AppRadius.standard),
                        border: Border.all(color: chosen == i ? AppColors.primary : AppColors.divider, width: chosen == i ? 1.5 : 1),
                      ),
                      child: Row(
                        children: [
                          Icon(chosen == i ? Icons.radio_button_checked : Icons.radio_button_unchecked,
                              size: 18, color: chosen == i ? AppColors.primary : AppColors.textMuted),
                          const SizedBox(width: 10),
                          Expanded(child: Text(q.options[i], style: const TextStyle(fontSize: 13.5, color: AppColors.textStrong))),
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
                  OutlinedButton(onPressed: () => setState(() => _index--), child: Text(context.t('common.back')))
                else
                  const SizedBox.shrink(),
                const Spacer(),
                FilledButton(
                  onPressed: chosen == null || _submitting ? null : () => last ? _submit() : setState(() => _index++),
                  style: FilledButton.styleFrom(backgroundColor: AppColors.primary, foregroundColor: AppColors.onPrimary),
                  child: Text(last
                      ? (_submitting ? context.t('general.submitting') : context.t('general.submit'))
                      : context.t('common.next')),
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
    // The certificate follows the post-test pass mark stored with the attempt.
    final certified = !_isPre && o.passed;
    return ListView(
      padding: const EdgeInsets.fromLTRB(22, 28, 22, 28),
      children: [
        Text(_isPre ? context.t('general.startingPoint') : context.t('general.yourResult'),
            style: const TextStyle(fontFamily: AppFonts.serif, fontSize: 21, fontWeight: FontWeight.w600, color: AppColors.primaryText)),
        const SizedBox(height: 12),
        Text(context.t('general.score', {'correct': o.correct, 'total': o.total, 'percent': o.percent}),
            style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: AppColors.textStrong)),
        const SizedBox(height: 10),
        _Verdict(passed: o.passed, passMark: o.passMark, needed: o.needed, total: o.total),
        const SizedBox(height: 12),
        Text(
          _isPre
              ? context.t('general.preDone')
              : [
                  pre == null
                      ? context.t('general.postDone')
                      : context.t('general.postDoneWithPre', {'correct': pre.correct, 'total': pre.total, 'percent': pre.percent}),
                  certified ? context.t('cert.earnedLine') : context.t('cert.notEarnedLine', {'passMark': o.passMark}),
                ].join(' '),
          style: const TextStyle(fontSize: 13.5, height: 1.5, color: AppColors.textMuted),
        ),
        const SizedBox(height: 22),
        if (certified) ...[
          FilledButton.icon(
            onPressed: () => context.go('/certificate'),
            icon: const Icon(Icons.emoji_events_outlined),
            style: FilledButton.styleFrom(backgroundColor: AppColors.primary, foregroundColor: AppColors.onPrimary),
            label: Text(context.t('cert.get')),
          ),
          const SizedBox(height: 10),
          OutlinedButton(onPressed: () => context.go('/modules'), child: Text(context.t('reader.backToModules'))),
        ] else
          FilledButton(
            onPressed: () => context.go('/modules'),
            style: FilledButton.styleFrom(backgroundColor: AppColors.primary, foregroundColor: AppColors.onPrimary),
            child: Text(_isPre ? context.t('general.goToModules') : context.t('reader.backToModules')),
          ),
      ],
    );
  }
}


/// Passed or Not passed with an icon and words (never colour alone), and the pass
/// mark that applied: "Pass mark 80% (20 of 25 correct)".
class _Verdict extends StatelessWidget {
  final bool passed;
  final int passMark;
  final int needed;
  final int total;

  const _Verdict({required this.passed, required this.passMark, required this.needed, required this.total});

  @override
  Widget build(BuildContext context) {
    final verdict = passed ? context.t('general.passed') : context.t('general.notPassed');
    final mark = context.t('general.passMarkLine', {'passMark': passMark, 'needed': needed, 'total': total});
    return Semantics(
      label: '$verdict. $mark',
      excludeSemantics: true,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: passed ? AppColors.successSurface : AppColors.surfaceMuted,
          borderRadius: BorderRadius.circular(AppRadius.small),
          border: Border.all(color: passed ? AppColors.success : AppColors.controlBorder),
        ),
        child: Row(
          children: [
            Icon(passed ? Icons.check_circle_rounded : Icons.cancel_outlined,
                size: 22, color: passed ? AppColors.successText : AppColors.textMuted),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(verdict, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: AppColors.textStrong)),
                  Text(mark, style: const TextStyle(fontSize: 12.5, color: AppColors.text)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
