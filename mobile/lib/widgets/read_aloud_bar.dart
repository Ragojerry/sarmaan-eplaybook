import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../l10n/l10n.dart';
import '../models/api_models.dart';
import '../offline/content_sync_service.dart' show localDatabaseProvider;
import '../services/narration_builder.dart';
import '../services/read_aloud_service.dart';
import '../theme/app_theme.dart';

/// Whether Read aloud is offered: only with English as the content language.
final readAloudAllowedProvider = FutureProvider.autoDispose<bool>((ref) async {
  final code = await ref.read(localDatabaseProvider).getSetting('selected_language_code');
  return readAloudAllowedFor(code);
});

/// The reader's Read aloud bar: one button until reading starts, then the player
/// (previous section, play/pause, next section, speed, stop). The narration is
/// built from the sections on screen ([NarrationSource]; the phone's own builder
/// for now).
class ReadAloudBar extends ConsumerStatefulWidget {
  final String moduleId;
  final String title;
  final String? description;
  final List<ContentSection> sections;
  final NarrationSource narration;

  const ReadAloudBar({
    super.key,
    required this.moduleId,
    required this.title,
    required this.description,
    required this.sections,
    this.narration = const LocalNarrationBuilder(),
  });

  @override
  ConsumerState<ReadAloudBar> createState() => _ReadAloudBarState();
}

class _ReadAloudBarState extends ConsumerState<ReadAloudBar> {
  bool _needsVoice = false;
  bool _starting = false;

  Future<void> _start() async {
    setState(() => _starting = true);
    final service = ref.read(readAloudServiceProvider);
    final max = await service.maxChunkLength();
    final chunks = widget.narration.build(title: widget.title, description: widget.description, sections: widget.sections, maxLength: max);
    final check = await service.start(widget.moduleId, chunks);
    if (mounted) {
      setState(() {
        _starting = false;
        _needsVoice = check == VoiceCheck.noEnglishVoice;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final service = ref.watch(readAloudServiceProvider);
    final mine = service.active && service.moduleId == widget.moduleId;

    return Container(
      key: const Key('readAloudBar'),
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
      decoration: BoxDecoration(
        color: mine ? AppColors.highlightSurface : AppColors.surface,
        border: Border.all(color: mine ? AppColors.accent : AppColors.divider, width: 1.5),
        borderRadius: BorderRadius.circular(AppRadius.standard),
      ),
      child: mine ? _player(service) : _idle(),
    );
  }

  Widget _idle() {
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, mainAxisSize: MainAxisSize.min, children: [
      Row(children: [
        _roundButton(
          icon: Icons.play_arrow_rounded,
          tooltip: context.t('readAloud.play'),
          onTap: _starting ? null : _start,
          filled: true,
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(context.t('reader.readAloud'), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.textStrong)),
            Text(context.t('reader.onDeviceAudio'), style: const TextStyle(fontFamily: AppFonts.mono, fontSize: 9.5, color: AppColors.textMuted)),
          ]),
        ),
        if (_starting)
          const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, valueColor: AlwaysStoppedAnimation(AppColors.primary))),
      ]),
      if (_needsVoice) ...[
        const SizedBox(height: 8),
        Text(context.t('readAloud.needsVoice'), style: const TextStyle(fontSize: 12, color: AppColors.warningText)),
        Align(
          alignment: Alignment.centerLeft,
          child: TextButton.icon(
            icon: const Icon(Icons.settings_voice_outlined, size: 18),
            label: Text(context.t('readAloud.openVoiceSettings')),
            onPressed: openVoiceSettings,
          ),
        ),
      ],
    ]);
  }

  Widget _player(ReadAloudService s) {
    final reading = s.status == ReadAloudStatus.reading;
    final label = switch (s.status) {
      ReadAloudStatus.reading => context.t('readAloud.reading'),
      ReadAloudStatus.quizPause => context.t('readAloud.quizPause'),
      _ => context.t('readAloud.paused'),
    };
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, mainAxisSize: MainAxisSize.min, children: [
      Text(label,
          style: TextStyle(
              fontSize: 11.5,
              fontWeight: FontWeight.w600,
              color: s.status == ReadAloudStatus.quizPause ? AppColors.warningText : AppColors.textStrong)),
      const SizedBox(height: 6),
      Row(children: [
        _roundButton(icon: Icons.skip_previous_rounded, tooltip: context.t('readAloud.previous'), onTap: s.previous),
        const SizedBox(width: 6),
        _roundButton(
          icon: reading ? Icons.pause_rounded : Icons.play_arrow_rounded,
          tooltip: reading ? context.t('readAloud.pause') : context.t('readAloud.play'),
          onTap: reading ? s.pause : s.resume,
          filled: true,
        ),
        const SizedBox(width: 6),
        _roundButton(icon: Icons.skip_next_rounded, tooltip: context.t('readAloud.next'), onTap: s.next),
        const Spacer(),
        OutlinedButton(
          key: const Key('readAloudSpeed'),
          style: OutlinedButton.styleFrom(
            visualDensity: VisualDensity.compact,
            foregroundColor: AppColors.primary,
            side: const BorderSide(color: AppColors.accent),
          ),
          onPressed: () => s.setSpeed(s.speed.next),
          child: Text(context.t('readAloud.speed', {'speed': s.speed.label})),
        ),
        const SizedBox(width: 6),
        _roundButton(icon: Icons.stop_rounded, tooltip: context.t('readAloud.stop'), onTap: s.stop),
      ]),
    ]);
  }

  Widget _roundButton({required IconData icon, required String tooltip, required VoidCallback? onTap, bool filled = false}) {
    return Tooltip(
      message: tooltip,
      child: Semantics(
        button: true,
        label: tooltip,
        child: InkResponse(
          onTap: onTap,
          radius: 22,
          child: Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: filled ? AppColors.primary : AppColors.surface,
              border: filled ? null : Border.all(color: AppColors.controlBorder),
            ),
            alignment: Alignment.center,
            child: Icon(icon, size: 18, color: filled ? AppColors.onPrimary : AppColors.primary),
          ),
        ),
      ),
    );
  }
}

/// Wraps a section: tinted while it is read aloud; a tap while reading continues from it.
class ReadAloudHighlight extends ConsumerWidget {
  final String moduleId;
  final String sectionId;
  final Widget child;

  const ReadAloudHighlight({super.key, required this.moduleId, required this.sectionId, required this.child});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final service = ref.watch(readAloudServiceProvider);
    final mine = service.active && service.moduleId == moduleId;
    final current = mine && service.currentSectionId == sectionId;
    return GestureDetector(
      behavior: HitTestBehavior.deferToChild,
      onTap: mine ? () => service.jumpToSection(sectionId) : null,
      // A tint and a gold bar in the margin: the text never moves.
      child: Stack(clipBehavior: Clip.none, children: [
        AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          color: current ? AppColors.highlightSurface : Colors.transparent,
          child: child,
        ),
        if (current)
          const Positioned(left: -10, top: 0, bottom: 0, width: 3, child: ColoredBox(color: AppColors.accent)),
      ]),
    );
  }
}
