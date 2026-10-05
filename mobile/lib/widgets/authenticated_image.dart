import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../services/auth_service.dart';

/// `Image.network` can't attach the Authorization header GET /media/{id}/file
/// requires (media is deliberately not public). Fetches the bytes through
/// the authenticated Dio client instead. Mirrors
/// admin/src/components/AuthenticatedImage.tsx exactly, same reasoning.
///
/// Stateful (not a plain ConsumerWidget) specifically so the fetch Future is
/// created once in initState, not recreated on every rebuild — a bare
/// `FutureBuilder(future: someCallThatRunsInBuild())` restarts the request
/// (and briefly re-shows the loading spinner) on every parent rebuild, which
/// is a real, easy-to-miss bug, not just a style preference.
class AuthenticatedImage extends ConsumerStatefulWidget {
  final String mediaAssetId;
  final String? alt;
  final double? width;
  final BoxFit fit;

  const AuthenticatedImage({
    super.key,
    required this.mediaAssetId,
    this.alt,
    this.width,
    this.fit = BoxFit.cover,
  });

  @override
  ConsumerState<AuthenticatedImage> createState() => _AuthenticatedImageState();
}

class _AuthenticatedImageState extends ConsumerState<AuthenticatedImage> {
  late final Future<Response<List<int>>> _future;

  @override
  void initState() {
    super.initState();
    final api = ref.read(apiClientProvider);
    _future = api.dio.get<List<int>>(
      '/media/${widget.mediaAssetId}/file',
      options: Options(responseType: ResponseType.bytes),
    );
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Response<List<int>>>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return Container(
            width: widget.width,
            height: 160,
            color: Colors.grey.shade200,
            child: const Center(child: CircularProgressIndicator()),
          );
        }
        if (snapshot.hasError || snapshot.data == null) {
          return Container(
            width: widget.width,
            height: 80,
            color: Colors.grey.shade100,
            child: const Center(child: Text('Image failed to load', style: TextStyle(fontSize: 12))),
          );
        }
        return Image.memory(
          Uint8List.fromList(snapshot.data!.data!),
          width: widget.width,
          fit: widget.fit,
          semanticLabel: widget.alt,
        );
      },
    );
  }
}
