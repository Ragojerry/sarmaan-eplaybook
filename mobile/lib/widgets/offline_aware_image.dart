import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../offline/content_sync_service.dart';
import 'authenticated_image.dart';

/// Real offline-first image loading: checks the local Drift cache
/// (populated by ContentSyncService) for an already-downloaded file first,
/// and only falls back to a network fetch (AuthenticatedImage, Phase 7) if
/// no local copy exists yet. In normal operation after a successful sync,
/// this NEVER touches the network — satisfying master prompt §18's
/// requirement that image viewing work with zero connectivity.
class OfflineAwareImage extends ConsumerStatefulWidget {
  final String mediaAssetId;
  final String? alt;
  final double? width;
  final BoxFit fit;

  const OfflineAwareImage({
    super.key,
    required this.mediaAssetId,
    this.alt,
    this.width,
    this.fit = BoxFit.cover,
  });

  @override
  ConsumerState<OfflineAwareImage> createState() => _OfflineAwareImageState();
}

class _OfflineAwareImageState extends ConsumerState<OfflineAwareImage> {
  late final Future<String?> _localPathFuture;

  @override
  void initState() {
    super.initState();
    final db = ref.read(localDatabaseProvider);
    _localPathFuture = db.getMedia(widget.mediaAssetId).then((row) => row?.localPath);
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<String?>(
      future: _localPathFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return Container(width: widget.width, height: 160, color: Colors.grey.shade200);
        }
        final localPath = snapshot.data;
        if (localPath != null && File(localPath).existsSync()) {
          return Image.file(File(localPath), width: widget.width, fit: widget.fit, semanticLabel: widget.alt);
        }
        // No local copy — fall back to a network fetch (Phase 7's
        // AuthenticatedImage). This should be rare after a successful
        // sync, but a single missed download must not break the reader.
        return AuthenticatedImage(mediaAssetId: widget.mediaAssetId, alt: widget.alt, width: widget.width, fit: widget.fit);
      },
    );
  }
}
