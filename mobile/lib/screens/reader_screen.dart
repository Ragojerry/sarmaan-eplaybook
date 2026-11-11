import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:go_router/go_router.dart';

import '../sync/analytics_recorder.dart';
import '../db/local_database.dart';
import '../learning/learning_rules.dart';
import '../learning/learning_service.dart';
import '../models/api_models.dart';
import '../offline/content_sync_service.dart';
import '../quiz/quiz_grader.dart';
import '../theme/app_theme.dart';
import '../widgets/offline_aware_image.dart';
import '../widgets/section_audio_player.dart';

/// Phase 8: reads from the LOCAL cache — never the network — matching
/// master prompt §18's offline-first requirement exactly ("module reading"
/// and "job aid access" must work with no internet). Content gets into the
/// cache via ContentSyncService (triggered from Home); this screen is a
/// pure local reader on top of it. Adapts cached Drift rows back into the
/// same ContentSection/ModuleTranslation shapes Phase 7 used, so the
/// per-ContentType rendering switch below doesn't need to change at all.
final localModuleTranslationProvider = FutureProvider.autoDispose.family<ModuleTranslation?, String>((ref, moduleId) async {
  final db = ref.read(localDatabaseProvider);
  // The person's language when a published translation is cached, else English.
  final code = (await db.getSetting('selected_language_code')) ?? 'en';
  final row = (code != 'en' ? await db.getTranslationForModule(moduleId, code) : null) ??
      await db.getTranslationForModule(moduleId, 'en');
  if (row == null) return null;
  return ModuleTranslation(
    id: row.id,
    moduleId: row.moduleId,
    languageId: row.languageId,
    title: row.title,
    description: row.description,
    body: row.body,
    audioText: row.audioText,
    status: row.status,
  );
});

final localModuleSectionsProvider = FutureProvider.autoDispose.family<List<ContentSection>, String>((ref, moduleId) async {
  final db = ref.read(localDatabaseProvider);
  final rows = await db.getSectionsForModule(moduleId);
  // Translated sections replace the English text per section; structure
  // (type, order, pictures) always comes from the English section, and any
  // section without a published translation stays in English.
  final code = (await db.getSetting('selected_language_code')) ?? 'en';
  final translated = {
    if (code != 'en')
      for (final s in await db.getSectionTranslations(moduleId, code)) s.sectionId: s,
  };
  return [
    for (final row in rows)
      () {
        final english = Map<String, dynamic>.from(jsonDecode(row.contentJson) as Map);
        final tr = translated[row.id];
        final content = tr == null
            ? english
            : {...english, ...Map<String, dynamic>.from(jsonDecode(tr.contentJson) as Map)};
        final trTitle = tr?.title;
        return ContentSection(
          id: row.id,
          moduleId: row.moduleId,
          sectionNumber: row.sectionNumber,
          title: (trTitle != null && trTitle.isNotEmpty) ? trTitle : row.title,
          contentType: row.contentType,
          content: content,
          sortOrder: row.sortOrder,
        );
      }(),
  ];
});

// autoDispose: re-read each time a module is opened, never a stale copy.
final localProgressProvider = FutureProvider.autoDispose.family<LocalProgressRow?, String>((ref, moduleId) async {
  final db = ref.read(localDatabaseProvider);
  return db.getProgressForModule(moduleId);
});

/// Real content reader: renders cached content per ContentType (no raw
/// HTML, per master prompt §16), real on-device TTS via flutter_tts,
/// offline-first image loading via OfflineAwareImage, and a real
/// "mark as complete" that writes to the local `local_progress` table and
/// queues a `pending_sync` entry. Visual language matches the prototype's
/// `.reader-body` styles exactly: serif teal-deep h3 headings, clay-soft
/// (warning) / teal-soft (positive) callouts with a colored left border,
/// a dark-gradient `.video-inline` card, a bordered dose table, and a
/// pill-shaped audio bar with a filled play/stop button.
class ReaderScreen extends ConsumerStatefulWidget {
  final String moduleId;

  const ReaderScreen({super.key, required this.moduleId});

  @override
  ConsumerState<ReaderScreen> createState() => _ReaderScreenState();
}

class _ReaderScreenState extends ConsumerState<ReaderScreen> with WidgetsBindingObserver {
  final FlutterTts _tts = FlutterTts();
  bool _speaking = false;
  final ScrollController _scroll = ScrollController();
  late final LocalDatabase _db;
  List<ContentSection> _loadedSections = const [];
  int _savedPercent = 0;
  int _pendingPercent = 0;
  String? _pendingWhere;
  bool _canRead = false; // false while the module is locked
  bool _readingRecorded = false;

  // Active time: counted only while this module is on screen and the app is in front.
  bool _timing = false; // the module is open and not completed yet
  int _baseSeconds = 0; // stored before this visit
  int _savedThisVisit = 0; // already added to the database during this visit
  DateTime? _activeSince; // null while paused (app in the background, screen locked)
  Timer? _ticker;

  // The inline quiz: this attempt's answers (section id -> True/False) and its result.
  final Map<String, bool> _answers = {};
  QuizResult? _quizResult;
  bool _submittingQuiz = false;

  @override
  void initState() {
    super.initState();
    _db = ref.read(localDatabaseProvider);
    _scroll.addListener(_onScroll);
    WidgetsBinding.instance.addObserver(this);
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final db = ref.read(localDatabaseProvider);
      final state = (await loadLearning(db)).of(widget.moduleId);
      _canRead = state?.canRead ?? false;
      _readingRecorded = state?.readingDone ?? false;
      if (!_canRead) return; // a locked module is not opened (and its time not counted)
      final existing = await db.getProgressForModule(widget.moduleId);
      _savedPercent = existing?.progressPercent ?? 0;
      await db.upsertProgress(moduleId: widget.moduleId);
      recordAnalyticsEvent(db, 'MODULE_OPEN', moduleId: widget.moduleId);
      _checkShortModule();
      if (mounted && state != null && !state.completed) {
        _baseSeconds = state.secondsSpent;
        _timing = true;
        _resumeTimer();
      }
    });
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState lifecycle) {
    if (lifecycle == AppLifecycleState.resumed) {
      _resumeTimer();
    } else {
      _pauseTimer(); // background, screen locked, or another app on top: time stops
    }
  }

  void _resumeTimer() {
    if (!_timing || _activeSince != null) return;
    _activeSince = DateTime.now();
    _ticker ??= Timer.periodic(const Duration(seconds: 1), (t) {
      if (!mounted) return;
      if (t.tick % 10 == 0) _saveTime(); // saved every 10 seconds, so little is lost if the phone dies
      setState(() {});
    });
  }

  void _pauseTimer() {
    _saveTime();
    _activeSince = null;
    _ticker?.cancel();
    _ticker = null;
  }

  /// Moves the whole seconds counted since the last save into the database.
  Future<void> _saveTime() async {
    final since = _activeSince;
    if (since == null) return;
    final whole = DateTime.now().difference(since).inSeconds;
    if (whole <= 0) return;
    _activeSince = since.add(Duration(seconds: whole));
    _savedThisVisit += whole;
    await _db.addModuleSeconds(widget.moduleId, whole);
  }

  int get _secondsNow {
    final since = _activeSince;
    final running = since == null ? 0 : DateTime.now().difference(since).inSeconds;
    return _baseSeconds + _savedThisVisit + running;
  }

  /// A module short enough to fit on the screen is read as soon as it shows.
  void _checkShortModule() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted || !_scroll.hasClients || _loadedSections.isEmpty) return;
      if (_scroll.position.maxScrollExtent <= 0) _recordReadingDone();
    });
  }

  /// Reaching the end of the module finishes reading: the post-test opens.
  Future<void> _recordReadingDone() async {
    if (!_canRead || _readingRecorded) return;
    _readingRecorded = true;
    _savedPercent = LocalDatabase.readingPercent;
    await _db.markReadingComplete(widget.moduleId, lastSection: _pendingWhere);
    ref.invalidate(learningProvider);
  }

  /// Reading progress = how far down the module the learner has scrolled,
  /// scaled to 0-50% (the post-test earns the rest).
  void _onScroll() {
    if (!_scroll.hasClients || !_canRead) return;
    final max = _scroll.position.maxScrollExtent;
    if (max <= 0) return;
    final fraction = (_scroll.position.pixels / max).clamp(0.0, 1.0);
    if (fraction >= 0.98) _recordReadingDone();
    final percent = (fraction * LocalDatabase.readingPercent).round();
    if (percent <= _pendingPercent) return;
    _pendingPercent = percent;
    if (_loadedSections.isNotEmpty) {
      var i = (fraction * (_loadedSections.length - 1)).floor().clamp(0, _loadedSections.length - 1);
      for (; i >= 0; i--) {
        if (_loadedSections[i].contentType == 'HEADING') {
          _pendingWhere = _loadedSections[i].content['text'] as String?;
          break;
        }
      }
    }
    if (percent >= _savedPercent + 5) _flushProgress();
  }

  Future<void> _flushProgress() async {
    if (!_canRead || _pendingPercent <= _savedPercent) return;
    _savedPercent = _pendingPercent;
    await _db.raiseProgress(widget.moduleId, _pendingPercent, lastSection: _pendingWhere);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _pauseTimer();
    _flushProgress();
    _scroll.dispose();
    _tts.stop();
    super.dispose();
  }

  Future<void> _toggleSpeak(String? audioText) async {
    if (audioText == null || audioText.isEmpty) return;
    if (_speaking) {
      await _tts.stop();
      setState(() => _speaking = false);
    } else {
      setState(() => _speaking = true);
      _tts.setCompletionHandler(() {
        if (mounted) setState(() => _speaking = false);
      });
      await _tts.speak(audioText);
    }
  }

  /// "Complete module": allowed when the quiz is passed (if the module has one) and
  /// the minimum time is reached; otherwise a plain message says what is missing.
  Future<void> _complete() async {
    final db = ref.read(localDatabaseProvider);
    await _saveTime();
    final problem = await completeModule(db, widget.moduleId);
    if (problem == null) {
      _pauseTimer();
      _timing = false;
    }
    ref.invalidate(localProgressProvider(widget.moduleId));
    ref.invalidate(learningProvider);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(problem ?? 'Module completed. It will sync to your account when online.'),
      ));
    }
  }

  /// Records the learner's answer; when every statement is answered, the attempt
  /// is graded and saved (offline too).
  Future<void> _answer(String sectionId, bool value, int statements) async {
    if (_quizResult != null || _answers.containsKey(sectionId) || _submittingQuiz) return;
    setState(() => _answers[sectionId] = value);
    if (_answers.length < statements) return;
    _submittingQuiz = true;
    try {
      final result = await recordModuleQuiz(ref.read(localDatabaseProvider), moduleId: widget.moduleId, answers: Map.of(_answers));
      if (mounted) setState(() => _quizResult = result);
      ref.invalidate(learningProvider);
    } catch (_) {
      // The quiz closed meanwhile (e.g. the module was completed on another device).
    } finally {
      _submittingQuiz = false;
    }
  }

  /// "Try again": every statement is answered again (unlimited until the module is completed).
  void _retryQuiz() => setState(() {
        _answers.clear();
        _quizResult = null;
      });

  Widget _card({required IconData icon, required String title, required String body, Widget? action, bool good = false}) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(AppRadius.medium),
        border: Border.all(color: good ? AppColors.teal : AppColors.line),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 20, color: AppColors.teal),
              const SizedBox(width: 8),
              Expanded(
                child: Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15, color: AppColors.tealDeep)),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(body, style: const TextStyle(fontSize: 12.5, height: 1.45, color: AppColors.textSecondary)),
          if (action != null) ...[const SizedBox(height: 12), SizedBox(width: double.infinity, child: action)],
        ],
      ),
    );
  }

  Widget _primary(String label, VoidCallback? onPressed) => FilledButton(
        onPressed: onPressed,
        style: FilledButton.styleFrom(backgroundColor: AppColors.tealDeep, foregroundColor: AppColors.sand),
        child: Text(label),
      );

  /// Shown instead of the module when it cannot be read yet.
  Widget _gate(LearningSnapshot learning, ModuleLearning? state) {
    final Widget card;
    if (state == null) {
      card = _card(
        icon: Icons.block,
        title: 'Not available',
        body: 'This module is not part of your current training. The training may have been updated, '
            'or the module is for another role. Go back to Modules to continue.',
        action: OutlinedButton(onPressed: () => context.go('/modules'), child: const Text('Back to modules')),
      );
    } else if (state.lockedByGeneralTest) {
      card = _card(
        icon: Icons.quiz_outlined,
        title: 'Start with the General pre-test',
        body: 'Before the modules, answer ${learning.general.questions} questions to show what you already know. '
            'It is not a pass or fail: it is your starting point, and you take it once.',
        action: _primary('Start the General pre-test', () => context.go('/general-test/pre')),
      );
    } else {
      final blocker = learning.blockerOf(widget.moduleId);
      card = _card(
        icon: Icons.lock_outline,
        title: 'Locked',
        body: 'Complete ${blocker?.title ?? 'the previous module'} first. Modules open one after another, '
            'when the previous one is completed.',
        action: blocker == null ? null : _primary('Go to ${blocker.moduleCode}', () => context.go('/reader/${blocker.id}')),
      );
    }
    return ListView(padding: const EdgeInsets.fromLTRB(22, 22, 22, 28), children: [card]);
  }

  /// "Time in this module: 1:20 / 3:00", until the module is completed.
  Widget _timeIndicator(ModuleLearning state) {
    if (state.completed || !_timing) return const SizedBox.shrink();
    final secs = _secondsNow;
    final done = secs >= state.minSeconds;
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
      decoration: BoxDecoration(color: AppColors.tealSoft, borderRadius: BorderRadius.circular(10)),
      child: Row(
        children: [
          Icon(done ? Icons.check_circle_outline : Icons.timer_outlined, size: 16, color: AppColors.tealDeep),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              'Time in this module: ${formatDuration(done ? state.minSeconds : secs)} / ${formatDuration(state.minSeconds)}',
              style: const TextStyle(fontSize: 12, color: AppColors.calloutGoodText),
            ),
          ),
        ],
      ),
    );
  }

  /// The end of the module: the quiz status, the time, and "Complete module".
  Widget _completionArea(ModuleLearning state, int statements) {
    if (state.completed) {
      return _card(
        icon: Icons.check_circle,
        good: true,
        title: 'Module completed',
        body: 'You can re-read it, play its audio and video and view its pictures; the result stays as it is.',
      );
    }
    final secs = _secondsNow;
    final ready = canCompleteModule(
        unlocked: state.unlocked, hasQuiz: state.hasQuiz, quizPassed: state.quizPassed, seconds: secs, minSeconds: state.minSeconds);
    final lines = [
      if (state.hasQuiz)
        state.quizPassed
            ? 'Module quiz: passed.'
            : 'Module quiz: answer all $statements statements correctly ($kQuizPassMark% pass mark). '
                'You can try again as often as you need.',
      secs >= state.minSeconds
          ? 'Time: ${formatDuration(state.minSeconds)} reached.'
          : 'Time: ${formatDuration(secs)} of ${formatDuration(state.minSeconds)}. Please stay a little longer in this module.',
    ];
    return _card(
      icon: ready ? Icons.flag_outlined : Icons.hourglass_bottom,
      title: 'Finish this module',
      body: lines.join('\n'),
      action: _primary('Complete module', _complete),
    );
  }

  /// One inline True/False statement. Answered once per attempt; when every
  /// statement is answered the attempt is graded, and "Try again" starts a new one.
  Widget _quizCard(ContentSection section, ModuleLearning? state, int statements) {
    final statement = section.content['statement'] as String? ?? '';
    final correctAnswer = section.content['answer'] as bool?;
    final explanation = section.content['explanation'] as String?;
    final review = state == null || state.completed || (state.hasQuiz && state.quizPassed && _quizResult == null);
    final mine = _answers[section.id];
    final answered = mine != null;
    final right = answered && mine == correctAnswer;
    final graded = _quizResult != null;
    Widget choice(bool value) {
      final chosen = mine == value;
      return Expanded(
        child: OutlinedButton(
          onPressed: review || answered ? null : () => _answer(section.id, value, statements),
          style: OutlinedButton.styleFrom(
            backgroundColor: chosen ? (right ? AppColors.tealSoft : AppColors.claySoft) : null,
            side: BorderSide(color: chosen ? (right ? AppColors.teal : AppColors.clay) : AppColors.line),
          ),
          child: Text(value ? 'True' : 'False'),
        ),
      );
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.teal),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('QUICK CHECK · TRUE OR FALSE?',
              style: TextStyle(fontWeight: FontWeight.w700, fontSize: 10.5, letterSpacing: 0.5, color: AppColors.tealDeep)),
          const SizedBox(height: 6),
          Text(statement, style: const TextStyle(fontSize: 13, height: 1.5, color: AppColors.readerBody)),
          const SizedBox(height: 10),
          if (review)
            Text('Answer: ${correctAnswer == true ? 'True' : 'False'}',
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.tealDeep))
          else
            Row(children: [choice(true), const SizedBox(width: 10), choice(false)]),
          if (!review && answered)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(
                right ? 'Correct.' : 'Not quite. The answer is ${correctAnswer == true ? 'True' : 'False'}.',
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: right ? AppColors.tealDeep : AppColors.clay),
              ),
            ),
          if ((review || answered) && explanation != null && explanation.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(explanation, style: const TextStyle(fontSize: 11.5, height: 1.4, color: AppColors.textSecondary)),
            ),
          if (graded && section.id == _lastStatementId)
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: _quizResult!.passed
                  ? const Text('Quiz passed. Well done!',
                      style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.w800, color: AppColors.tealDeep))
                  : Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text(
                          'You got ${_quizResult!.correct} of ${_quizResult!.total}. All need to be right to pass. '
                          'Try again: you answer all ${_quizResult!.total} statements again.',
                          style: const TextStyle(fontSize: 12, color: AppColors.calloutWarningText),
                        ),
                        const SizedBox(height: 8),
                        _primary('Try again', _retryQuiz),
                      ],
                    ),
            ),
        ],
      ),
    );
  }

  String? _lastStatementId;

  @override
  Widget build(BuildContext context) {
    final translationAsync = ref.watch(localModuleTranslationProvider(widget.moduleId));
    final sectionsAsync = ref.watch(localModuleSectionsProvider(widget.moduleId));
    final learningAsync = ref.watch(learningProvider);

    return Scaffold(
      appBar: AppBar(
        title: translationAsync.maybeWhen(data: (t) => Text(t?.title ?? 'Module'), orElse: () => const Text('Module')),
        leading: BackButton(onPressed: () => context.go('/modules')),
      ),
      body: sectionsAsync.when(
        data: (sections) {
          final learning = learningAsync.valueOrNull;
          if (learning == null) return const Center(child: CircularProgressIndicator());
          final state = learning.of(widget.moduleId);
          if (state == null || !state.canRead) return _gate(learning, state);
          _canRead = true;
          final statements = sections.where((x) => x.contentType == 'TRUE_FALSE').toList();
          _lastStatementId = statements.isEmpty ? null : statements.last.id;
          if (_loadedSections.isEmpty && sections.isNotEmpty) _checkShortModule();
          _loadedSections = sections;
          return sections.isEmpty
            ? const Center(
                child: Padding(
                  padding: EdgeInsets.all(24),
                  child: Text(
                    'No content downloaded for this module yet. Go to Home and pull down to sync.',
                    textAlign: TextAlign.center,
                  ),
                ),
              )
            : ListView(
                controller: _scroll,
                padding: const EdgeInsets.fromLTRB(22, 18, 22, 28),
                children: [
                  translationAsync.maybeWhen(
                    data: (t) => (t?.audioText != null && t!.audioText!.isNotEmpty)
                        ? _AudioBar(speaking: _speaking, onToggle: () => _toggleSpeak(t.audioText))
                        : const SizedBox.shrink(),
                    orElse: () => const SizedBox.shrink(),
                  ),
                  _timeIndicator(state),
                  for (final section in sections)
                    section.contentType == 'TRUE_FALSE'
                        ? _quizCard(section, state, statements.length)
                        : _buildSection(context, section),
                  const SizedBox(height: 22),
                  _completionArea(state, statements.length),
                ],
              );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Could not load content: $e')),
      ),
    );
  }

  Widget _buildSection(BuildContext context, ContentSection section) {
    switch (section.contentType) {
      case 'HEADING':
        return Padding(
          padding: const EdgeInsets.only(top: 20, bottom: 8),
          child: Text(
            section.content['text'] as String? ?? '',
            style: const TextStyle(fontFamily: AppFonts.serif, fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.tealDeep),
          ),
        );

      case 'TEXT':
        return Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: Text(
            section.content['text'] as String? ?? '',
            style: const TextStyle(fontSize: 12.8, height: 1.65, color: AppColors.readerBody),
          ),
        );

      case 'LIST':
        final items = (section.content['items'] as List?)?.cast<String>() ?? [];
        return Padding(
          padding: const EdgeInsets.only(bottom: 14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (final item in items)
                Padding(
                  padding: const EdgeInsets.only(bottom: 5),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('•  ', style: TextStyle(color: AppColors.readerBody)),
                      Expanded(
                        child: Text(item, style: const TextStyle(fontSize: 12.5, height: 1.6, color: AppColors.readerBody)),
                      ),
                    ],
                  ),
                ),
            ],
          ),
        );

      case 'IMAGE':
        final assetId = section.content['media_asset_id'] as String?;
        if (assetId == null) return const SizedBox.shrink();
        return Container(
          margin: const EdgeInsets.only(bottom: 14),
          decoration: BoxDecoration(
            color: AppColors.white,
            borderRadius: BorderRadius.circular(AppRadius.standard),
            border: Border.all(color: AppColors.line),
          ),
          clipBehavior: Clip.antiAlias,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              OfflineAwareImage(mediaAssetId: assetId, alt: section.content['alt'] as String?),
              if (section.content['caption'] is String)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 8),
                  child: Text(
                    section.content['caption'] as String,
                    style: const TextStyle(fontSize: 10.8, color: AppColors.textSecondary, height: 1.5),
                  ),
                ),
            ],
          ),
        );

      case 'CALLOUT':
      case 'WARNING':
      case 'JOB_AID':
        final isWarning = section.contentType == 'WARNING';
        final isJobAid = section.contentType == 'JOB_AID';
        final accent = (isWarning || isJobAid) ? AppColors.clay : AppColors.teal;
        final bg = (isWarning || isJobAid) ? AppColors.claySoft : AppColors.tealSoft;
        final labelColor = (isWarning || isJobAid) ? AppColors.clay : AppColors.tealDeep;
        final bodyColor = (isWarning || isJobAid) ? AppColors.calloutWarningText : AppColors.calloutGoodText;
        return Container(
          margin: const EdgeInsets.only(bottom: 14),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            color: bg,
            borderRadius: BorderRadius.circular(10),
            border: Border(left: BorderSide(color: accent, width: 3)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (section.content['heading'] is String)
                Text(
                  (section.content['heading'] as String).toUpperCase(),
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 11, letterSpacing: 0.5, color: labelColor),
                ),
              if (section.content['text'] is String)
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(
                    section.content['text'] as String,
                    style: TextStyle(fontSize: 12, height: 1.55, color: bodyColor),
                  ),
                ),
            ],
          ),
        );

      case 'TABLE':
        final headers = ((section.content['headers'] as List?) ?? const []).map((h) => h.toString()).toList();
        final rows = ((section.content['rows'] as List?) ?? const [])
            .map((r) => r is List ? r.map((c) => c.toString()).toList() : <String>[r.toString()])
            .toList();
        // DataTable asserts at least one column and equal cell counts per row,
        // so size to the widest row/header and pad the rest with blanks.
        var width = headers.length;
        for (final r in rows) {
          if (r.length > width) width = r.length;
        }
        if (width == 0) return const SizedBox.shrink();
        final hasHeaders = headers.any((h) => h.trim().isNotEmpty);
        return Container(
          margin: const EdgeInsets.only(bottom: 16),
          decoration: BoxDecoration(border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(10)),
          clipBehavior: Clip.antiAlias,
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              headingRowHeight: hasHeaders ? null : 0,
              headingRowColor: WidgetStateProperty.all(AppColors.tealSoft),
              headingTextStyle: const TextStyle(
                fontWeight: FontWeight.w700,
                fontSize: 10.5,
                color: AppColors.tealDeep,
                letterSpacing: 0.3,
              ),
              dataTextStyle: const TextStyle(fontSize: 11.5, color: AppColors.readerBody),
              columns: [
                for (var i = 0; i < width; i++)
                  DataColumn(label: Text(i < headers.length ? headers[i].toUpperCase() : '')),
              ],
              rows: [
                for (final row in rows)
                  DataRow(cells: [
                    for (var i = 0; i < width; i++) DataCell(Text(i < row.length ? row[i] : '')),
                  ]),
              ],
            ),
          ),
        );

      case 'VIDEO':
        final videoId = section.content['video_id'] as String?;
        if (videoId == null) return const SizedBox.shrink();
        return Container(
          margin: const EdgeInsets.only(bottom: 16),
          padding: const EdgeInsets.all(11),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFF123F38), AppColors.teal],
            ),
            borderRadius: BorderRadius.circular(AppRadius.standard),
          ),
          child: InkWell(
            onTap: () => context.go('/videos/$videoId'),
            child: Row(
              children: [
                Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white.withValues(alpha: 0.18),
                    border: Border.all(color: Colors.white.withValues(alpha: 0.4)),
                  ),
                  alignment: Alignment.center,
                  child: const Icon(Icons.play_arrow_rounded, color: Colors.white, size: 18),
                ),
                const SizedBox(width: 11),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        section.content['title'] as String? ?? 'Watch video',
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: Colors.white),
                      ),
                      if (section.content['duration'] is String)
                        Padding(
                          padding: const EdgeInsets.only(top: 2),
                          child: Text(
                            section.content['duration'] as String,
                            style: TextStyle(fontSize: 10, color: Colors.white.withValues(alpha: 0.75)),
                          ),
                        ),
                    ],
                  ),
                ),
                Icon(Icons.chevron_right, color: Colors.white.withValues(alpha: 0.6)),
              ],
            ),
          ),
        );

      case 'AUDIO':
        final audioId = section.content['media_asset_id'] as String?;
        if (audioId == null) return const SizedBox.shrink();
        final description = section.content['text'];
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            SectionAudioPlayer(
              mediaAssetId: audioId,
              title: section.title ?? section.content['title'] as String? ?? 'Listen',
            ),
            if (description is String && description.trim().isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(bottom: 14),
                child: Text(description, style: const TextStyle(fontSize: 13, color: AppColors.ink)),
              ),
          ],
        );

      default:
        return const SizedBox.shrink();
    }
  }
}

/// Matches the prototype's `.audio-bar`: pill-shaped card, filled
/// teal-deep play button (or a small clay "stop" state while speaking).
class _AudioBar extends StatelessWidget {
  final bool speaking;
  final VoidCallback onToggle;

  const _AudioBar({required this.speaking, required this.onToggle});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
      decoration: BoxDecoration(
        color: AppColors.white,
        border: Border.all(color: AppColors.line, width: 1.5),
        borderRadius: BorderRadius.circular(AppRadius.standard),
      ),
      child: Row(
        children: [
          GestureDetector(
            onTap: onToggle,
            child: Container(
              width: speaking ? 28 : 34,
              height: speaking ? 28 : 34,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: speaking ? AppColors.claySoft : AppColors.tealDeep,
              ),
              alignment: Alignment.center,
              child: Icon(
                speaking ? Icons.stop_rounded : Icons.play_arrow_rounded,
                size: speaking ? 14 : 16,
                color: speaking ? AppColors.clay : Colors.white,
              ),
            ),
          ),
          const SizedBox(width: 10),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Read aloud', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.ink)),
                Text('ON-DEVICE AUDIO', style: TextStyle(fontFamily: AppFonts.mono, fontSize: 9.5, color: AppColors.textMuted)),
              ],
            ),
          ),
          if (speaking)
            const SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(strokeWidth: 2, valueColor: AlwaysStoppedAnimation(AppColors.teal)),
            ),
        ],
      ),
    );
  }
}
