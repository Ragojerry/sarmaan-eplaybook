import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:video_player/video_player.dart';

import '../db/local_database.dart';
import '../models/api_models.dart';
import '../offline/content_sync_service.dart';
import '../services/auth_service.dart';
import '../theme/app_theme.dart';
import '../video/video_manager.dart';

final videoDetailProvider =
    FutureProvider.family<TrainingVideo, String>((ref, videoId) async {
  final api = ref.read(apiClientProvider);
  final resp = await api.dio.get('/videos/$videoId');
  return TrainingVideo.fromJson(resp.data);
});

final localVideoProvider =
    FutureProvider.family<CachedVideoRow?, String>((ref, videoId) async {
  final db = ref.read(localDatabaseProvider);
  return db.getVideo(videoId);
});

/// Real video download + local playback (Phase 9). Three real states, not
/// one fake one:
///   1. No file uploaded server-side yet (video.hasFile == false) — honest
///      "not available" notice, same as Phase 7.
///   2. File exists server-side but not downloaded to this device yet —
///      a real download button using VideoManager (checksum-verified,
///      resumable).
///   3. Downloaded and checksum-verified — plays from the REAL local file
///      via video_player. Never a remote URL relabeled as offline (master
///      prompt §95) — this is the exact guarantee the prototype's video
///      screen never had (docs/prototype-analysis.md §1).
class VideoScreen extends ConsumerStatefulWidget {
  final String videoId;

  const VideoScreen({super.key, required this.videoId});

  @override
  ConsumerState<VideoScreen> createState() => _VideoScreenState();
}

class _VideoScreenState extends ConsumerState<VideoScreen> {
  VideoPlayerController? _controller;
  bool _downloading = false;
  double _progress = 0;
  String? _downloadError;

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  Future<void> _startDownload() async {
    setState(() {
      _downloading = true;
      _progress = 0;
      _downloadError = null;
    });
    try {
      await ref.read(videoManagerProvider).downloadVideo(
        widget.videoId,
        onProgress: (p) {
          if (mounted) setState(() => _progress = p);
        },
      );
      ref.invalidate(localVideoProvider(widget.videoId));
    } catch (e) {
      setState(() => _downloadError = e.toString());
    } finally {
      if (mounted) setState(() => _downloading = false);
    }
  }

  Future<void> _play(String localPath) async {
    final controller = VideoPlayerController.file(File(localPath));
    await controller.initialize();
    await controller.play();
    setState(() => _controller = controller);
  }

  @override
  Widget build(BuildContext context) {
    final videoAsync = ref.watch(videoDetailProvider(widget.videoId));
    final localAsync = ref.watch(localVideoProvider(widget.videoId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Video'),
        leading: BackButton(onPressed: () => context.go('/videos')),
      ),
      body: videoAsync.when(
        data: (video) => localAsync.when(
          data: (local) => _buildBody(video, local),
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => _buildBody(video, null),
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
            child: Text('Could not load video: $e',
                style: const TextStyle(color: AppColors.danger))),
      ),
    );
  }

  Widget _buildBody(TrainingVideo video, CachedVideoRow? local) {
    final downloaded = local?.localPath != null && local!.hasFile;

    return Padding(
      padding: const EdgeInsets.fromLTRB(22, 16, 22, 22),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AspectRatio(
            aspectRatio: 16 / 9,
            child: downloaded &&
                    _controller != null &&
                    _controller!.value.isInitialized
                ? ClipRRect(
                    borderRadius: BorderRadius.circular(AppRadius.medium),
                    child: VideoPlayer(_controller!),
                  )
                : GestureDetector(
                    onTap: downloaded ? () => _play(local.localPath!) : null,
                    child: Container(
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [Color(0xFF1E3D37), AppColors.teal],
                        ),
                        borderRadius: BorderRadius.circular(AppRadius.medium),
                      ),
                      child: Center(
                        child: Container(
                          width: 56,
                          height: 56,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: Colors.white.withValues(alpha: 0.15),
                            border: Border.all(
                                color: Colors.white.withValues(alpha: 0.5),
                                width: 1.5),
                          ),
                          child: Icon(
                            downloaded
                                ? Icons.play_arrow_rounded
                                : Icons.download_rounded,
                            color: Colors.white,
                            size: 28,
                          ),
                        ),
                      ),
                    ),
                  ),
          ),
          const SizedBox(height: 14),
          Text(video.title,
              style:
                  const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
          const SizedBox(height: 6),
          if (video.description != null)
            Text(video.description!,
                style: const TextStyle(
                    fontSize: 11.5,
                    color: AppColors.textSecondary,
                    height: 1.5)),
          const SizedBox(height: 16),
          if (!video.hasFile)
            _notice(
              'This video is not yet available. Real footage and offline download support are planned for a later phase.',
            )
          else if (downloaded) ...[
            const Row(
              children: [
                Icon(Icons.check_circle, size: 16, color: AppColors.teal),
                SizedBox(width: 6),
                Text('Downloaded for offline playback',
                    style: TextStyle(
                        fontSize: 11.5,
                        color: AppColors.teal,
                        fontWeight: FontWeight.w700)),
              ],
            ),
          ] else ...[
            if (_downloading) ...[
              ClipRRect(
                borderRadius: BorderRadius.circular(99),
                child: LinearProgressIndicator(
                  value: _progress,
                  minHeight: 7,
                  backgroundColor: AppColors.sandDeep,
                  valueColor: const AlwaysStoppedAnimation(AppColors.teal),
                ),
              ),
              const SizedBox(height: 6),
              Text('${(_progress * 100).toStringAsFixed(0)}%',
                  style: const TextStyle(
                      fontFamily: AppFonts.mono,
                      fontSize: 10.5,
                      color: AppColors.textMuted)),
            ] else
              FilledButton.icon(
                onPressed: _startDownload,
                icon: const Icon(Icons.download_rounded, size: 18),
                label: Text(
                    'Download${video.fileSize != null ? ' (${_formatBytes(video.fileSize!)})' : ''}'),
              ),
            if (_downloadError != null) ...[
              const SizedBox(height: 10),
              _notice(_downloadError!),
            ],
          ],
        ],
      ),
    );
  }

  Widget _notice(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
          color: AppColors.claySoft, borderRadius: BorderRadius.circular(12)),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.info_outline, size: 16, color: AppColors.clay),
          const SizedBox(width: 9),
          Expanded(
              child: Text(text,
                  style: const TextStyle(
                      fontSize: 11.5,
                      color: AppColors.calloutWarningText,
                      height: 1.5))),
        ],
      ),
    );
  }

  String _formatBytes(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(0)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}
