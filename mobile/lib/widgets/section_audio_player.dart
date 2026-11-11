import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:video_player/video_player.dart';

import '../offline/content_sync_service.dart';
import '../theme/app_theme.dart';

/// Plays an AUDIO section's file from the copy the release installer
/// downloaded (offline, never streamed). video_player also plays audio-only
/// files (mp3, m4a, wav), so no extra package is needed.
class SectionAudioPlayer extends ConsumerStatefulWidget {
  final String mediaAssetId;
  final String title;

  const SectionAudioPlayer({super.key, required this.mediaAssetId, required this.title});

  @override
  ConsumerState<SectionAudioPlayer> createState() => _SectionAudioPlayerState();
}

class _SectionAudioPlayerState extends ConsumerState<SectionAudioPlayer> {
  VideoPlayerController? _controller;
  bool _loading = true;
  bool _failed = false;

  @override
  void initState() {
    super.initState();
    _open();
  }

  Future<void> _open() async {
    final row = await ref.read(localDatabaseProvider).getMedia(widget.mediaAssetId);
    final path = row?.localPath;
    if (path == null || !File(path).existsSync()) {
      if (mounted) setState(() => _loading = false);
      return;
    }
    final controller = VideoPlayerController.file(File(path));
    try {
      await controller.initialize();
      controller.addListener(() {
        if (mounted) setState(() {});
      });
      if (!mounted) return controller.dispose();
      setState(() {
        _controller = controller;
        _loading = false;
      });
    } catch (_) {
      await controller.dispose();
      if (mounted) {
        setState(() {
          _loading = false;
          _failed = true;
        });
      }
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  String _time(Duration d) => '${d.inMinutes}:${(d.inSeconds % 60).toString().padLeft(2, '0')}';

  @override
  Widget build(BuildContext context) {
    final c = _controller;
    final value = c?.value;
    final playing = value?.isPlaying ?? false;
    final total = value?.duration ?? Duration.zero;
    final pos = value?.position ?? Duration.zero;
    final String status;
    if (_loading) {
      status = 'Loading…';
    } else if (_failed) {
      status = 'This audio could not be played on this phone.';
    } else if (c == null) {
      status = 'Audio will be available after the next sync.';
    } else {
      status = '${_time(pos)} / ${_time(total)}';
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.fromLTRB(12, 9, 12, 4),
      decoration: BoxDecoration(
        color: AppColors.white,
        border: Border.all(color: AppColors.divider, width: 1.5),
        borderRadius: BorderRadius.circular(AppRadius.standard),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Semantics(
                button: true,
                label: playing ? 'Pause audio' : 'Play audio',
                child: GestureDetector(
                  onTap: c == null
                      ? null
                      : () {
                          if (playing) {
                            c.pause();
                          } else {
                            if (pos >= total && total > Duration.zero) c.seekTo(Duration.zero);
                            c.play();
                          }
                        },
                  child: Container(
                    width: 34,
                    height: 34,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: c == null ? AppColors.divider : AppColors.primary,
                    ),
                    alignment: Alignment.center,
                    child: Icon(playing ? Icons.pause_rounded : Icons.play_arrow_rounded, size: 18, color: AppColors.onPrimary),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(widget.title,
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.textStrong)),
                    Text(status,
                        style: const TextStyle(fontSize: 9.5, color: AppColors.textMuted)),
                  ],
                ),
              ),
            ],
          ),
          if (c != null)
            Slider(
              value: pos.inMilliseconds.clamp(0, total.inMilliseconds).toDouble(),
              max: total.inMilliseconds > 0 ? total.inMilliseconds.toDouble() : 1,
              activeColor: AppColors.primary,
              onChanged: (v) => c.seekTo(Duration(milliseconds: v.round())),
            ),
        ],
      ),
    );
  }
}
