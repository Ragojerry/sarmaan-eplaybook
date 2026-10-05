import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:go_router/go_router.dart';

import '../db/local_database.dart';
import '../models/api_models.dart';
import '../offline/content_sync_service.dart';
import '../theme/app_theme.dart';
import '../widgets/offline_aware_image.dart';

/// Phase 8: reads from the LOCAL cache — never the network — matching
/// master prompt §18's offline-first requirement exactly ("module reading"
/// and "job aid access" must work with no internet). Content gets into the
/// cache via ContentSyncService (triggered from Home); this screen is a
/// pure local reader on top of it. Adapts cached Drift rows back into the
/// same ContentSection/ModuleTranslation shapes Phase 7 used, so the
/// per-ContentType rendering switch below doesn't need to change at all.
final localModuleTranslationProvider = FutureProvider.family<ModuleTranslation?, String>((ref, moduleId) async {
  final db = ref.read(localDatabaseProvider);
  final row = await db.getTranslationForModule(moduleId, 'en');
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

final localModuleSectionsProvider = FutureProvider.family<List<ContentSection>, String>((ref, moduleId) async {
  final db = ref.read(localDatabaseProvider);
  final rows = await db.getSectionsForModule(moduleId);
  return [
    for (final row in rows)
      ContentSection(
        id: row.id,
        moduleId: row.moduleId,
        sectionNumber: row.sectionNumber,
        title: row.title,
        contentType: row.contentType,
        content: Map<String, dynamic>.from(jsonDecode(row.contentJson) as Map),
        sortOrder: row.sortOrder,
      ),
  ];
});

final localProgressProvider = FutureProvider.family<LocalProgressRow?, String>((ref, moduleId) async {
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

class _ReaderScreenState extends ConsumerState<ReaderScreen> {
  final FlutterTts _tts = FlutterTts();
  bool _speaking = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(localDatabaseProvider).upsertProgress(moduleId: widget.moduleId);
    });
  }

  @override
  void dispose() {
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

  Future<void> _markComplete() async {
    final db = ref.read(localDatabaseProvider);
    await db.upsertProgress(moduleId: widget.moduleId, progressPercent: 100, completed: true);
    await db.enqueueSync(
      'progress',
      jsonEncode({'module_id': widget.moduleId, 'completed': true, 'completed_at': DateTime.now().toIso8601String()}),
    );
    ref.invalidate(localProgressProvider(widget.moduleId));
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Marked complete. Will sync to your account when online.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final translationAsync = ref.watch(localModuleTranslationProvider(widget.moduleId));
    final sectionsAsync = ref.watch(localModuleSectionsProvider(widget.moduleId));
    final progressAsync = ref.watch(localProgressProvider(widget.moduleId));

    return Scaffold(
      appBar: AppBar(
        title: translationAsync.maybeWhen(data: (t) => Text(t?.title ?? 'Module'), orElse: () => const Text('Module')),
        leading: BackButton(onPressed: () => context.go('/modules')),
      ),
      body: sectionsAsync.when(
        data: (sections) => sections.isEmpty
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
                padding: const EdgeInsets.fromLTRB(22, 18, 22, 28),
                children: [
                  translationAsync.maybeWhen(
                    data: (t) => (t?.audioText != null && t!.audioText!.isNotEmpty)
                        ? _AudioBar(speaking: _speaking, onToggle: () => _toggleSpeak(t.audioText))
                        : const SizedBox.shrink(),
                    orElse: () => const SizedBox.shrink(),
                  ),
                  for (final section in sections) _buildSection(context, section),
                  const SizedBox(height: 22),
                  progressAsync.when(
                    data: (progress) {
                      final completed = progress?.completed ?? false;
                      return Row(
                        children: [
                          Expanded(
                            child: OutlinedButton.icon(
                              onPressed: completed ? null : _markComplete,
                              icon: Icon(completed ? Icons.check_circle : Icons.check_circle_outline, size: 18),
                              label: Text(completed ? 'Completed' : 'Mark as complete'),
                              style: completed
                                  ? OutlinedButton.styleFrom(
                                      backgroundColor: AppColors.tealDeep,
                                      foregroundColor: AppColors.sand,
                                      side: const BorderSide(color: AppColors.tealDeep),
                                    )
                                  : null,
                            ),
                          ),
                        ],
                      );
                    },
                    loading: () => const SizedBox.shrink(),
                    error: (_, __) => const SizedBox.shrink(),
                  ),
                ],
              ),
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
        final headers = (section.content['headers'] as List?)?.cast<String>() ?? [];
        final rows = (section.content['rows'] as List?)?.cast<List>() ?? [];
        return Container(
          margin: const EdgeInsets.only(bottom: 16),
          decoration: BoxDecoration(border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(10)),
          clipBehavior: Clip.antiAlias,
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              headingRowColor: WidgetStateProperty.all(AppColors.tealSoft),
              headingTextStyle: const TextStyle(
                fontWeight: FontWeight.w700,
                fontSize: 10.5,
                color: AppColors.tealDeep,
                letterSpacing: 0.3,
              ),
              dataTextStyle: const TextStyle(fontSize: 11.5, color: AppColors.readerBody),
              columns: [for (final h in headers) DataColumn(label: Text(h.toUpperCase()))],
              rows: [
                for (final row in rows)
                  DataRow(cells: [for (final cell in row) DataCell(Text(cell.toString()))]),
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
