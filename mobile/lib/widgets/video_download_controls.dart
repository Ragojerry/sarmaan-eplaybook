import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../l10n/l10n.dart';
import '../offline/content_sync_service.dart' show localDatabaseProvider;
import '../theme/app_theme.dart';
import '../video/video_downloads.dart';
import '../video/video_manifest.dart';

/// Asks the download manager for [entries] the way every screen does: a one-time
/// question before a large download on mobile data, and a clear message when the
/// phone is offline or short of space. Returns true when downloading started (or
/// the videos were already there).
Future<bool> requestVideoDownloads(BuildContext context, WidgetRef ref, List<VideoEntry> entries) async {
  final manager = ref.read(videoDownloadManagerProvider);
  final messenger = ScaffoldMessenger.maybeOf(context);
  void say(String text) => messenger?.showSnackBar(SnackBar(content: Text(text)));

  final results = await manager.startAll(entries.map((e) => e.videoId));
  final ask = [for (final e in entries) if (results[e.videoId] == StartResult.needsMobileDataConfirm) e];
  if (ask.isNotEmpty) {
    if (!context.mounted) return false;
    final size = ask.fold<int>(0, (s, e) => s + e.sizeBytes);
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(context.t('video.mobileDataTitle')),
        content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(context.t('video.mobileDataBody', {'size': formatBytes(size)})),
          const SizedBox(height: 10),
          Text(context.t('video.mobileDataHint'), style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: Text(context.t('common.cancel'))),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: Text(context.t('common.continue'))),
        ],
      ),
    );
    if (ok != true) return false;
    results.addAll(await manager.startAll(ask.map((e) => e.videoId), confirmedMobileData: true));
  }
  final values = results.values.toList();
  if (values.contains(StartResult.offline)) {
    say(L10n.t('video.connectToWatch'));
  } else if (values.contains(StartResult.notEnoughSpace)) {
    final needed = entries.where((e) => results[e.videoId] == StartResult.notEnoughSpace).fold<int>(0, (s, e) => s + e.sizeBytes);
    say(L10n.t('video.notEnoughSpace', {'size': formatBytes(needed)}));
  } else if (values.contains(StartResult.unknownVideo)) {
    say(L10n.t('video.notInManifest'));
  }
  final started = values.where((r) => r == StartResult.started).length;
  if (started > 1) say(L10n.t('video.downloadsQueued', {'count': started}));
  return values.any((r) => r == StartResult.started || r == StartResult.alreadyQueued || r == StartResult.alreadyDownloaded);
}

String failureText(VideoDownloadError? e) => switch (e) {
      VideoDownloadError.corrupt => L10n.t('video.failedCorrupt'),
      VideoDownloadError.notFound => L10n.t('video.failedNotFound'),
      VideoDownloadError.storage => L10n.t('video.failedStorage'),
      _ => L10n.t('video.failedNetwork'),
    };

/// A video's download state and its one or two actions, used on the video
/// screen, the Videos tab and module pages.
///   not downloaded: "Download to watch" + size
///   downloading:    progress bar, Pause, Cancel
///   paused:         Resume, Cancel
///   failed:         reason + Retry
///   downloaded:     Play + "Offline ready" (+ "Update available" when newer)
class VideoDownloadControls extends ConsumerWidget {
  final VideoEntry entry;
  final VoidCallback? onPlay;
  final bool compact;

  const VideoDownloadControls({super.key, required this.entry, this.onPlay, this.compact = false});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final status = ref.watch(videoStatusProvider(entry.videoId)).valueOrNull;
    if (status == null) return const SizedBox(height: 36);
    final manager = ref.read(videoDownloadManagerProvider);
    final percent = (status.progress * 100).floor();
    final size = Text(formatBytes(entry.sizeBytes), style: const TextStyle(fontFamily: AppFonts.mono, fontSize: 11, color: AppColors.textMuted));

    final downloading = status.busy || (status.state == VideoDownloadState.downloading);
    if (downloading) {
      final label = status.queued
          ? context.t('video.queued')
          : status.active
              ? context.t('video.downloadingPercent', {'percent': percent})
              : context.t('video.waitingForConnection');
      return Column(crossAxisAlignment: CrossAxisAlignment.stretch, mainAxisSize: MainAxisSize.min, children: [
        Row(children: [
          Expanded(child: Text(label, style: const TextStyle(fontSize: 12, color: AppColors.textMuted))),
          IconButton(
            tooltip: context.t('video.pause'),
            icon: const Icon(Icons.pause_circle_outline),
            color: AppColors.primary,
            onPressed: () => manager.pause(entry.videoId),
          ),
          IconButton(
            tooltip: context.t('video.cancelDownload'),
            icon: const Icon(Icons.close),
            color: AppColors.textMuted,
            onPressed: () => manager.cancel(entry.videoId),
          ),
        ]),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(value: status.active ? status.progress : null, minHeight: 6, color: AppColors.primary, backgroundColor: AppColors.divider),
        ),
      ]);
    }

    if (status.state == VideoDownloadState.paused) {
      return Row(children: [
        Expanded(child: Text(context.t('video.pausedAt', {'percent': percent}), style: const TextStyle(fontSize: 12, color: AppColors.textMuted))),
        TextButton.icon(
          icon: const Icon(Icons.play_circle_outline, size: 18),
          label: Text(context.t('video.resume')),
          onPressed: () => requestVideoDownloads(context, ref, [entry]),
        ),
        IconButton(
          tooltip: context.t('video.cancelDownload'),
          icon: const Icon(Icons.close),
          color: AppColors.textMuted,
          onPressed: () => manager.cancel(entry.videoId),
        ),
      ]);
    }

    if (status.playable) {
      return Wrap(spacing: 8, runSpacing: 6, crossAxisAlignment: WrapCrossAlignment.center, children: [
        FilledButton.icon(
          icon: const Icon(Icons.play_arrow_rounded, size: 18),
          label: Text(context.t('video.play')),
          onPressed: onPlay,
        ),
        _Badge(icon: Icons.offline_pin, text: context.t('video.offlineReady')),
        if (status.updateAvailable)
          OutlinedButton.icon(
            icon: const Icon(Icons.system_update_alt, size: 16),
            label: Text(context.t('video.updateAvailable')),
            onPressed: () => requestVideoDownloads(context, ref, [entry]),
          ),
        if (!compact)
          TextButton.icon(
            icon: const Icon(Icons.delete_outline, size: 18),
            label: Text(context.t('video.deleteDownload')),
            style: TextButton.styleFrom(foregroundColor: AppColors.textMuted),
            onPressed: () => manager.delete(entry.videoId),
          ),
      ]);
    }

    if (status.state == VideoDownloadState.failed) {
      return Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
        Text(failureText(status.error), style: const TextStyle(fontSize: 12, color: AppColors.errorText)),
        const SizedBox(height: 4),
        OutlinedButton.icon(
          icon: const Icon(Icons.refresh, size: 18),
          label: Text(context.t('video.retry')),
          onPressed: () => requestVideoDownloads(context, ref, [entry]),
        ),
      ]);
    }

    return Wrap(spacing: 10, crossAxisAlignment: WrapCrossAlignment.center, children: [
      OutlinedButton.icon(
        icon: const Icon(Icons.download_rounded, size: 18),
        label: Text(context.t('video.downloadToWatch')),
        onPressed: () => requestVideoDownloads(context, ref, [entry]),
      ),
      size,
    ]);
  }
}

class _Badge extends StatelessWidget {
  final IconData icon;
  final String text;
  const _Badge({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: AppColors.primary.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(AppRadius.standard),
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(icon, size: 14, color: AppColors.primary),
          const SizedBox(width: 4),
          Text(text, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppColors.primary)),
        ]),
      );
}

/// A module's videos: what is left to download, for "Download videos for this module".
final moduleVideosProvider = FutureProvider.autoDispose.family<({List<VideoEntry> missing, int bytes, int total}), String>((ref, moduleId) async {
  final manager = ref.watch(videoDownloadManagerProvider);
  final entries = await videosOfModule(ref.read(localDatabaseProvider), moduleId);
  final missing = <VideoEntry>[];
  for (final e in entries) {
    final s = await manager.statusOf(e.videoId);
    if (!s.playable && !s.busy) missing.add(e);
  }
  return (missing: missing, bytes: missing.fold<int>(0, (n, e) => n + e.sizeBytes), total: entries.length);
});

/// Under a module's time indicator: download all its videos (optional), or a note
/// that they are all on the phone. Nothing shows for a module without videos.
class ModuleVideosBar extends ConsumerWidget {
  final String moduleId;
  const ModuleVideosBar({super.key, required this.moduleId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final info = ref.watch(moduleVideosProvider(moduleId)).valueOrNull;
    if (info == null || info.total == 0) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: info.missing.isEmpty
          ? Row(children: [
              const Icon(Icons.offline_pin, size: 16, color: AppColors.primary),
              const SizedBox(width: 6),
              Expanded(child: Text(context.t('video.moduleAllOffline'), style: const TextStyle(fontSize: 11.5, color: AppColors.primary))),
            ])
          : Align(
              alignment: Alignment.centerLeft,
              child: OutlinedButton.icon(
                icon: const Icon(Icons.download_for_offline_outlined, size: 18),
                label: Text(context.t('video.moduleDownloadAll', {'size': formatBytes(info.bytes)})),
                onPressed: () => requestVideoDownloads(context, ref, info.missing),
              ),
            ),
    );
  }
}

/// One line on a module's video card: its size, its progress, or "Offline ready".
class VideoCardStatus extends ConsumerWidget {
  final String videoId;
  const VideoCardStatus({super.key, required this.videoId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final entry = ref.watch(videoEntryProvider(videoId)).valueOrNull;
    final status = ref.watch(videoStatusProvider(videoId)).valueOrNull;
    if (entry == null || status == null) return const SizedBox.shrink();
    final text = status.playable
        ? context.t('video.offlineReady')
        : status.busy
            ? context.t('video.downloadingPercent', {'percent': (status.progress * 100).floor()})
            : '${context.t('video.downloadToWatch')} · ${formatBytes(entry.sizeBytes)}';
    return Padding(
      padding: const EdgeInsets.only(top: 2),
      child: Text(text, style: TextStyle(fontSize: 10, color: AppColors.onPrimary.withValues(alpha: 0.85))),
    );
  }
}
