import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:video_player/video_player.dart';

import '../offline/content_sync_service.dart';
import '../sync/analytics_recorder.dart';
import '../theme/app_theme.dart';
import '../video/video_downloads.dart';
import '../video/video_manifest.dart';
import '../widgets/video_download_controls.dart';
import '../l10n/l10n.dart';

/// Whether the phone is online now (refreshed with every download change).
final videoOnlineProvider = FutureProvider.autoDispose<bool>((ref) {
  ref.watch(videoDownloadManagerProvider);
  return ref.read(videoNetworkProvider).isOnline();
});

/// One video. Works from the phone's copy of the video manifest, so it opens
/// offline. Tap to watch: a downloaded video plays from its verified local file;
/// otherwise it downloads (resumable, checked against its SHA-256) and plays as
/// soon as it is verified. Offline and not downloaded: "Connect to the internet
/// to watch this video." Nothing in training depends on watching.
class VideoScreen extends ConsumerStatefulWidget {
  final String videoId;

  const VideoScreen({super.key, required this.videoId});

  @override
  ConsumerState<VideoScreen> createState() => _VideoScreenState();
}

class _VideoScreenState extends ConsumerState<VideoScreen> {
  VideoPlayerController? _controller;
  bool _completionReported = false;
  String? _playError;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      recordAnalyticsEvent(ref.read(localDatabaseProvider), 'VIDEO_OPEN', videoId: widget.videoId);
    });
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  Future<void> _play(String localPath) async {
    final db = ref.read(localDatabaseProvider);
    VideoPlayerController? controller;
    try {
      controller = await ref.read(videoOpenerProvider)(localPath);
      await controller?.play();
    } catch (e) {
      await controller?.dispose();
      await recordAnalyticsEvent(db, 'VIDEO_PLAYBACK_FAILURE', videoId: widget.videoId, payload: {'reason': e.runtimeType.toString()});
      if (mounted) setState(() => _playError = L10n.t('video.playFailed'));
      return;
    }
    if (controller == null) return;
    // One VIDEO_COMPLETE ("watched") per viewing, when playback reaches the end. Analytics only.
    controller.addListener(() {
      final v = controller!.value;
      if (!_completionReported && v.isInitialized && v.duration > Duration.zero && v.position >= v.duration - const Duration(milliseconds: 500)) {
        _completionReported = true;
        recordAnalyticsEvent(db, 'VIDEO_COMPLETE', videoId: widget.videoId);
      }
    });
    if (!mounted) {
      await controller.dispose();
      return;
    }
    await _controller?.dispose();
    setState(() {
      _controller = controller;
      _playError = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    // A download started on this screen plays as soon as it is verified.
    ref.listen(videoStatusProvider(widget.videoId), (prev, next) {
      final before = prev?.valueOrNull;
      final now = next.valueOrNull;
      if (before != null && !before.playable && now != null && now.playable && _controller == null) {
        _play(now.localPath!);
      }
    });
    final entryAsync = ref.watch(videoEntryProvider(widget.videoId));
    return Scaffold(
      appBar: AppBar(
        title: Text(context.t('video.title')),
        leading: BackButton(onPressed: () => context.go('/videos')),
      ),
      body: entryAsync.when(
        data: (entry) => entry == null ? _notice(context.t('video.notInManifest')) : _body(entry),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _notice(context.t('common.somethingWrong')),
      ),
    );
  }

  Widget _body(VideoEntry entry) {
    final status = ref.watch(videoStatusProvider(widget.videoId)).valueOrNull;
    final online = ref.watch(videoOnlineProvider).valueOrNull ?? true;
    final playing = _controller != null && _controller!.value.isInitialized;
    final offlineAndMissing = !online && status != null && !status.playable && !status.busy;

    return ListView(
      padding: const EdgeInsets.fromLTRB(22, 16, 22, 22),
      children: [
        AspectRatio(
          aspectRatio: 16 / 9,
          child: playing
              ? GestureDetector(
                  onTap: () => setState(() => _controller!.value.isPlaying ? _controller!.pause() : _controller!.play()),
                  child: ClipRRect(borderRadius: BorderRadius.circular(AppRadius.medium), child: VideoPlayer(_controller!)),
                )
              : GestureDetector(
                  onTap: status?.playable == true
                      ? () => _play(status!.localPath!)
                      : (offlineAndMissing || status?.busy == true ? null : () => requestVideoDownloads(context, ref, [entry])),
                  child: Container(
                    decoration: BoxDecoration(gradient: AppSheen.hero, borderRadius: BorderRadius.circular(AppRadius.medium), boxShadow: AppSheen.card),
                    child: Center(
                      child: Container(
                        width: 56,
                        height: 56,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: AppColors.onPrimary.withValues(alpha: 0.15),
                          border: Border.all(color: AppColors.onPrimary.withValues(alpha: 0.5), width: 1.5),
                        ),
                        child: Icon(
                          status?.playable == true ? Icons.play_arrow_rounded : (offlineAndMissing ? Icons.cloud_off : Icons.download_rounded),
                          color: AppColors.onPrimary,
                          size: 28,
                        ),
                      ),
                    ),
                  ),
                ),
        ),
        const SizedBox(height: 14),
        Text(entry.title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
        const SizedBox(height: 4),
        Text(
          [if (entry.durationSeconds != null) _duration(entry.durationSeconds!), formatBytes(entry.sizeBytes)].join(' · '),
          style: const TextStyle(fontFamily: AppFonts.mono, fontSize: 10.5, color: AppColors.textMuted),
        ),
        const SizedBox(height: 16),
        if (offlineAndMissing)
          _notice(context.t('video.connectToWatch'))
        else
          VideoDownloadControls(entry: entry, onPlay: status?.playable == true ? () => _play(status!.localPath!) : null),
        if (_playError != null) ...[const SizedBox(height: 10), _notice(_playError!)],
        const SizedBox(height: 18),
        Text(context.t('video.optionalNote'), style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
      ],
    );
  }

  static String _duration(int s) => '${s ~/ 60}:${(s % 60).toString().padLeft(2, '0')}';

  Widget _notice(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(color: AppColors.warningSurface, borderRadius: BorderRadius.circular(12)),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.info_outline, size: 16, color: AppColors.info),
          const SizedBox(width: 9),
          Expanded(child: Text(text, style: const TextStyle(fontSize: 11.5, color: AppColors.warningText, height: 1.5))),
        ],
      ),
    );
  }
}
