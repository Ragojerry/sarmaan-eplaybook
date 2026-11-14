import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../offline/content_sync_service.dart';
import '../services/auth_service.dart';
import '../theme/app_theme.dart';
import '../video/video_downloads.dart';
import '../video/video_manifest.dart';
import '../widgets/partner_logo_row.dart';
import '../widgets/app_bottom_nav.dart';
import '../widgets/video_download_controls.dart';
import '../l10n/l10n.dart';

/// The Videos tab, from the phone's copy of the video manifest, so it lists
/// offline. Each video shows its own download state and actions; nothing
/// downloads until the learner asks. Pull down to refresh the list when online.
/// Styled to match the prototype's `.video-list-item`/`.video-list-thumb`.
class VideoLibraryScreen extends ConsumerWidget {
  const VideoLibraryScreen({super.key});

  Future<void> _refresh(WidgetRef ref) async {
    try {
      await refreshVideoManifest(ref.read(apiClientProvider), ref.read(localDatabaseProvider));
    } catch (_) {
      // Offline: the stored list stays.
    }
    ref.invalidate(videoEntriesProvider);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final videosAsync = ref.watch(videoEntriesProvider);

    return Scaffold(
      appBar: BrandTopBar(appBar: AppBar(title: Text(context.t('videos.title')))),
      body: RefreshIndicator(
        onRefresh: () => _refresh(ref),
        child: videosAsync.when(
          data: (videos) => ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.symmetric(vertical: 8),
            children: videos.isEmpty
                ? [Padding(padding: const EdgeInsets.all(40), child: Center(child: Text(context.t('videos.none'))))]
                : [
                    Padding(
                      padding: const EdgeInsets.fromLTRB(22, 4, 22, 8),
                      child: Text(context.t('video.optionalNote'), style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
                    ),
                    for (final v in videos) _VideoListItem(video: v),
                  ],
          ),
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => Center(child: Text(context.t('common.somethingWrong'), style: const TextStyle(color: AppColors.errorText))),
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentRoute: '/videos'),
    );
  }
}

class _VideoListItem extends ConsumerWidget {
  final VideoEntry video;

  const _VideoListItem({required this.video});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final playable = ref.watch(videoStatusProvider(video.videoId)).valueOrNull?.playable ?? false;
    return InkWell(
      onTap: () => context.go('/videos/${video.videoId}'),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 10),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 64,
              height: 42,
              decoration: BoxDecoration(gradient: AppSheen.button, borderRadius: BorderRadius.circular(8)),
              alignment: Alignment.center,
              child: Icon(playable ? Icons.play_arrow_rounded : Icons.download_rounded, color: AppColors.onPrimary, size: 18),
            ),
            const SizedBox(width: 11),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(video.title, style: const TextStyle(fontSize: 11.8, fontWeight: FontWeight.w700, color: AppColors.textStrong)),
                  const SizedBox(height: 6),
                  VideoDownloadControls(entry: video, compact: true, onPlay: () => context.go('/videos/${video.videoId}')),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
