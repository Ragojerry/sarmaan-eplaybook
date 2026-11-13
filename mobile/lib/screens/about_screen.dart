import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:package_info_plus/package_info_plus.dart';

import '../offline/content_sync_service.dart';
import '../services/auth_service.dart';
import '../services/settings_service.dart';
import '../sync/sync_engine.dart';
import '../theme/app_theme.dart';
import '../widgets/partner_logo_row.dart';
import '../video/video_manager.dart';
import '../widgets/app_bottom_nav.dart';
import '../l10n/l10n.dart';
import '../tour/app_tour.dart';

final packageInfoProvider = FutureProvider<PackageInfo>((ref) => PackageInfo.fromPlatform());

/// Master prompt §24's storage-usage display ("Videos: 1.2 GB / Training:
/// 200 MB / AI: 350 MB / Total / Available"), with real numbers for what's
/// actually computable right now. "AI" and "Available" are honestly
/// reported as not-yet-tracked rather than filled with fabricated numbers —
/// AI/RAG storage doesn't exist until Phase 10/11, and free-disk-space
/// reporting needs a platform-specific plugin this build doesn't include
/// yet. A real Videos/Training total with an honest gap beats fake
/// precision everywhere.
final storageUsageProvider = FutureProvider<({int videoBytes, int trainingBytes})>((ref) async {
  final videoManager = ref.read(videoManagerProvider);
  final db = ref.read(localDatabaseProvider);
  final videoBytes = await videoManager.totalVideoBytesUsed();
  final trainingBytes = await db.totalCachedMediaBytes();
  return (videoBytes: videoBytes, trainingBytes: trainingBytes);
});

/// Real app version (package_info_plus, reads pubspec.yaml's version at
/// build time) — replaces the prototype's hardcoded "1.2.0" string
/// (docs/prototype-analysis.md §8). Real logged-in user + role. The
/// safeguarding contact below is still a HARDCODED literal, same limitation
/// as the prototype had (docs/prototype-analysis.md §8 flagged this exact
/// string as something that "should become a configurable org setting" —
/// that hasn't happened yet). It matches the AZM Flipbook's Module 6 text
/// migrated in Phase 6, but isn't fetched from that content at runtime.
/// Styled to match the prototype's `.about-item` (white bordered rows) and
/// `.safeguard-box` (filled teal-deep card) exactly.
class AboutScreen extends ConsumerWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).user;
    final packageInfoAsync = ref.watch(packageInfoProvider);

    return Scaffold(
      appBar: BrandTopBar(appBar: AppBar(title: Text(context.t('about.title')))),
      body: ListView(
        padding: const EdgeInsets.symmetric(vertical: 16),
        children: [
          packageInfoAsync.when(
            data: (info) => _AboutItem(label: context.t('about.appVersion'), value: '${info.version} (${info.buildNumber})'),
            loading: () => _AboutItem(label: context.t('about.appVersion'), value: '…'),
            error: (_, __) => _AboutItem(label: context.t('about.appVersion'), value: context.t('common.unknown')),
          ),
          if (user != null)
            _AboutItem(label: context.t('about.signedInAs'), value: '${user.firstName} ${user.lastName}'),
          if (user != null) _AboutItem(label: context.t('about.role'), value: user.role),
          _AboutItem(label: context.t('about.contentSource'), value: 'AZM Training Flipbook'),
          ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 22),
            title: Text(context.t('about.language'), style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
            subtitle: Text(ref.watch(selectedLanguageLabelProvider).valueOrNull ?? 'English', style: const TextStyle(fontSize: 11)),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.go('/language?change=1'),
          ),
          ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 22),
            title: Text(context.t('about.syncUpdates'), style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
            subtitle: Text(context.t('about.syncUpdatesHint'), style: const TextStyle(fontSize: 11)),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.go('/updates'),
          ),
          ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 22),
            minTileHeight: 48,
            title: Text(context.t('tour.replay'), style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
            subtitle: Text(context.t('tour.replayHint'), style: const TextStyle(fontSize: 11)),
            trailing: const Icon(Icons.slideshow_outlined),
            onTap: () => showAppTour(context, ref),
          ),
          const SizedBox(height: 6),
          _buildStorageCard(ref),
          const SizedBox(height: 6),
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 22),
            padding: const EdgeInsets.all(15),
            decoration: BoxDecoration(color: AppColors.primaryText, borderRadius: BorderRadius.circular(AppRadius.standard), boxShadow: AppSheen.card),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  context.t('about.safeguardingTitle'),
                  style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700, color: AppColors.onPrimary),
                ),
                const SizedBox(height: 6),
                Text(
                  context.t('about.safeguardingBody'),
                  style: TextStyle(fontSize: 11, height: 1.6, color: AppColors.onPrimary.withValues(alpha: 0.9)),
                ),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(color: AppColors.onPrimary.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(6)),
                  child: const Text(
                    'concerns@malariaconsortium.org',
                    style: TextStyle(fontFamily: AppFonts.mono, fontSize: 10.5, color: AppColors.onPrimary),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 22),
            child: OutlinedButton.icon(
              onPressed: () => _confirmRestart(context, ref),
              icon: const Icon(Icons.restart_alt, size: 16),
              label: Text(context.t('about.restart')),
            ),
          ),
          const SizedBox(height: 10),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 22),
            child: OutlinedButton.icon(
              onPressed: () async {
                // Best effort: push anything still waiting before the session ends,
                // so nobody's progress is stranded on a shared phone.
                try {
                  await ref.read(syncEngineProvider.notifier).syncNow(manual: true).timeout(const Duration(seconds: 8));
                } catch (_) {}
                await ref.read(authProvider.notifier).logout();
                if (context.mounted) context.go('/login');
              },
              icon: const Icon(Icons.logout, size: 16),
              label: Text(context.t('about.signOut')),
              style: OutlinedButton.styleFrom(foregroundColor: AppColors.errorText, side: const BorderSide(color: AppColors.error, width: 1.5)),
            ),
          ),
          const SizedBox(height: 20),
          // Partner logos, full width on white (order and wording: assets/brand/logos.json).
          const PartnerLogoRow(placement: 'about'),
        ],
      ),
      bottomNavigationBar: const AppBottomNav(currentRoute: '/about'),
    );
  }

  /// Starting over replaces the old attempt: progress and quiz results are
  /// cleared here and on the server. Downloaded content and videos are kept.
  Future<void> _confirmRestart(BuildContext context, WidgetRef ref) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(ctx.t('about.restartConfirmTitle')),
        content: Text(ctx.t('about.restartConfirmBody')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(ctx.t('common.cancel'))),
          FilledButton(
            // Red fails 4.5:1 behind white or Forest text, so the confirm button keeps the primary
            // fill and is marked by a red border (contrast report).
            style: FilledButton.styleFrom(side: const BorderSide(color: AppColors.error, width: 2)),
            onPressed: () => Navigator.pop(ctx, true),
            child: Text(ctx.t('about.startOver')),
          ),
        ],
      ),
    );
    if (ok != true) return;
    await ref.read(localDatabaseProvider).restartTraining();
    // Tell the open screens, then upload the restart as soon as we can.
    ref.read(syncEngineProvider.notifier).notifyContentChanged();
    ref.read(syncEngineProvider.notifier).syncNow(manual: true).catchError((_) {});
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(L10n.t('about.restarted'))));
      context.go('/home');
    }
  }

  Widget _buildStorageCard(WidgetRef ref) {
    final usageAsync = ref.watch(storageUsageProvider);
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 22),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border.all(color: AppColors.divider),
        boxShadow: AppSheen.card,
        borderRadius: BorderRadius.circular(AppRadius.standard),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(L10n.t('about.offlineStorage'),
              style: const TextStyle(fontFamily: AppFonts.mono, fontSize: 10, fontWeight: FontWeight.w700, color: AppColors.textMuted, letterSpacing: 0.5)),
          const SizedBox(height: 10),
          usageAsync.when(
            data: (usage) {
              final total = usage.videoBytes + usage.trainingBytes;
              return Column(
                children: [
                  _storageRow(L10n.t('about.storageVideos'), usage.videoBytes),
                  _storageRow(L10n.t('about.storageTraining'), usage.trainingBytes),
                  const Divider(height: 18),
                  _storageRow(L10n.t('about.storageTotal'), total, bold: true),
                ],
              );
            },
            loading: () => const Padding(
              padding: EdgeInsets.symmetric(vertical: 8),
              child: Center(child: SizedBox(height: 16, width: 16, child: CircularProgressIndicator(strokeWidth: 2))),
            ),
            error: (_, __) => Text(L10n.t('about.storageFailed'), style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
          ),
        ],
      ),
    );
  }

  Widget _storageRow(String label, int bytes, {bool bold = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(fontSize: 12, fontWeight: bold ? FontWeight.w800 : FontWeight.w500, color: AppColors.textStrong)),
          Text(
            _formatBytes(bytes),
            style: TextStyle(fontFamily: AppFonts.mono, fontSize: 11.5, fontWeight: bold ? FontWeight.w800 : FontWeight.w500, color: AppColors.textMuted),
          ),
        ],
      ),
    );
  }

  String _formatBytes(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(0)} KB';
    if (bytes < 1024 * 1024 * 1024) return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
    return '${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(2)} GB';
  }
}

class _AboutItem extends StatelessWidget {
  final String label;
  final String value;

  const _AboutItem({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(22, 0, 22, 9),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border.all(color: AppColors.divider),
        boxShadow: AppSheen.card,
        borderRadius: BorderRadius.circular(AppRadius.standard),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 12.8, fontWeight: FontWeight.w600, color: AppColors.textStrong)),
          Text(
            value,
            style: const TextStyle(fontFamily: AppFonts.mono, fontSize: 11, color: AppColors.textMuted),
          ),
        ],
      ),
    );
  }
}

/// Name of the language the person chose, for the About screen.
final selectedLanguageLabelProvider = FutureProvider.autoDispose<String>((ref) async {
  final settings = ref.read(settingsServiceProvider);
  final code = await settings.getSelectedLanguageCode() ?? 'en';
  final languages = await settings.getCachedLanguages() ?? const [];
  for (final l in languages) {
    if (l.code == code) return l.nativeName == l.name ? l.name : '${l.name} · ${l.nativeName}';
  }
  return code == 'en' ? 'English' : code;
});
