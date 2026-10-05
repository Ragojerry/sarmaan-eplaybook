import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// Phase 2 stub with a REAL progress widget shape, but no real download yet.
/// Master prompt §93 is explicit: the prototype's fake `setInterval` progress
/// bar must NOT be carried into production. Phase 9/content-migration work
/// wires this to an actual release-package download with real byte counts
/// via lib/sync + lib/offline.
class DownloadingScreen extends StatelessWidget {
  const DownloadingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const CircularProgressIndicator(),
              const SizedBox(height: 16),
              const Text('Downloading training content…'),
              const SizedBox(height: 24),
              // TODO(Phase 9): replace with a real download-manager-driven
              // progress value once release-package download is implemented.
              OutlinedButton(
                onPressed: () => context.go('/home'),
                child: const Text('Continue (dev only — no real download yet)'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
