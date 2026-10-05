import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// Phase 2 stub. Real release/update management (Phase 9 / atomic update
/// logic, master prompt §56) checks the local release manifest against the
/// server's current release, downloads real bytes, verifies content hashes
/// (master prompt §72), and only then atomically swaps in the new content —
/// no fabricated progress bar like the prototype.
class UpdatesScreen extends StatelessWidget {
  const UpdatesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Updates'),
        leading: BackButton(onPressed: () => context.go('/home')),
      ),
      body: const Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text(
            'Real content/app release status implemented in Phase 9 against '
            'the release manifest — not hardcoded release notes.',
            textAlign: TextAlign.center,
          ),
        ),
      ),
    );
  }
}
