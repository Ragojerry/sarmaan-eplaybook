import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../learning/curriculum_notice.dart';
import '../offline/content_sync_service.dart';
import '../sync/sync_engine.dart';
import '../theme/app_theme.dart';
import '../l10n/l10n.dart';

/// Shown instead of the training when the server needs a newer app
/// (min_app_version), so an old app never shows stale or broken content.
class UpdateRequiredScreen extends ConsumerStatefulWidget {
  const UpdateRequiredScreen({super.key});

  @override
  ConsumerState<UpdateRequiredScreen> createState() => _UpdateRequiredScreenState();
}

class _UpdateRequiredScreenState extends ConsumerState<UpdateRequiredScreen> {
  bool _checking = false;

  Future<void> _checkAgain() async {
    setState(() => _checking = true);
    try {
      await ref.read(syncEngineProvider.notifier).syncNow(manual: true);
    } catch (_) {}
    final still = await updateRequired(ref.read(localDatabaseProvider));
    if (!mounted) return;
    setState(() => _checking = false);
    if (!still) context.go('/home');
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        backgroundColor: AppColors.background,
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Icon(Icons.system_update, size: 56, color: AppColors.primary),
                const SizedBox(height: 18),
                Text(context.t('update.required'),
                    textAlign: TextAlign.center, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
                const SizedBox(height: 12),
                Text(
                  context.t('update.askSupervisor'),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: _checking ? null : _checkAgain,
                  child: Text(_checking ? context.t('update.checking') : context.t('update.checkAgain')),
                ),
              ],
            ),
          ),
        ),
      );
}
