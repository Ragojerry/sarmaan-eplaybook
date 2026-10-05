import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../models/api_models.dart';
import '../offline/content_sync_service.dart';
import '../services/auth_service.dart';
import '../theme/app_theme.dart';
import '../widgets/app_bottom_nav.dart';

final videosProvider = FutureProvider<List<TrainingVideo>>((ref) async {
  final api = ref.read(apiClientProvider);
  final resp = await api.dio.get('/videos');
  return (resp.data as List).map((j) => TrainingVideo.fromJson(j)).toList();
});

/// Real video list from GET /videos — replaces the prototype's 4 hardcoded
/// entries. Three real states now (Phase 9): no file uploaded server-side
/// (has_file=false — still true for every video right now, see
/// docs/content-migration.md §4), uploaded but not yet downloaded to this
/// device, and downloaded (checksum-verified) for real offline playback.
/// Styled to match the prototype's `.video-list-item`/`.video-list-thumb`
/// (dark teal gradient thumbnail, 64x42, rounded 8px).
class VideoLibraryScreen extends ConsumerWidget {
  const VideoLibraryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final videosAsync = ref.watch(videosProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Videos')),
      body: videosAsync.when(
        data: (videos) => videos.isEmpty
            ? const Center(child: Text('No videos yet.'))
            : ListView(
                padding: const EdgeInsets.symmetric(vertical: 8),
                children: [for (final v in videos) _VideoListItem(video: v)],
              ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Could not load videos: $e', style: const TextStyle(color: AppColors.danger))),
      ),
      bottomNavigationBar: const AppBottomNav(currentRoute: '/videos'),
    );
  }
}

class _VideoListItem extends ConsumerWidget {
  final TrainingVideo video;

  const _VideoListItem({required this.video});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final localAsync = video.hasFile ? ref.watch(_localVideoStateProvider(video.id)) : const AsyncValue.data(false);
    final downloaded = localAsync.maybeWhen(data: (d) => d, orElse: () => false);

    final IconData icon;
    if (!video.hasFile) {
      icon = Icons.hourglass_empty_rounded;
    } else if (downloaded) {
      icon = Icons.play_arrow_rounded;
    } else {
      icon = Icons.download_rounded;
    }

    return InkWell(
      onTap: () => context.go('/videos/${video.id}'),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 10),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Container(
              width: 64,
              height: 42,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [Color(0xFF1E3D37), AppColors.teal],
                ),
                borderRadius: BorderRadius.circular(8),
              ),
              alignment: Alignment.center,
              child: Icon(icon, color: Colors.white.withValues(alpha: video.hasFile ? 1 : 0.6), size: 18),
            ),
            const SizedBox(width: 11),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(video.title, style: const TextStyle(fontSize: 11.8, fontWeight: FontWeight.w700, color: AppColors.ink)),
                  const SizedBox(height: 2),
                  Text(
                    !video.hasFile
                        ? 'Not yet available'
                        : downloaded
                            ? 'Downloaded — tap to play'
                            : (video.description ?? 'Tap to download'),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 10, color: AppColors.textMuted),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

final _localVideoStateProvider = FutureProvider.family<bool, String>((ref, videoId) async {
  final db = ref.read(localDatabaseProvider);
  final row = await db.getVideo(videoId);
  return row?.localPath != null && row!.hasFile;
});
