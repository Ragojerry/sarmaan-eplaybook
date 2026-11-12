import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../services/settings_service.dart';
import '../sync/release_installer.dart';
import '../sync/sync_engine.dart';
import '../theme/app_theme.dart';
import '../l10n/l10n.dart';

/// Sync & updates (master prompt §55-56): real status from the sync engine,
/// real pending counts, and a real install progress bar driven by the actual
/// download/validate/apply stages — nothing here is simulated.
class UpdatesScreen extends ConsumerStatefulWidget {
  const UpdatesScreen({super.key});

  @override
  ConsumerState<UpdatesScreen> createState() => _UpdatesScreenState();
}

class _UpdatesScreenState extends ConsumerState<UpdatesScreen> {
  bool? _consent;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await ref.read(syncEngineProvider.notifier).refreshLocalInfo();
      final c = await ref.read(settingsServiceProvider).getAnalyticsConsent();
      if (mounted) setState(() => _consent = c);
    });
  }

  static String _label(SyncStatus s) => switch (s) {
        SyncStatus.offline => L10n.t('common.offline'),
        SyncStatus.online => L10n.t('updates.connected'),
        SyncStatus.syncing => L10n.t('sync.syncing'),
        SyncStatus.syncError => L10n.t('updates.problem'),
        SyncStatus.updateAvailable => L10n.t('updates.updateAvailable'),
        SyncStatus.upToDate => L10n.t('updates.upToDate'),
      };

  static String _detail(SyncSnapshot s) {
    if (s.message != null) return s.message!;
    return switch (s.status) {
      SyncStatus.offline => L10n.t('updates.offlineDetail'),
      SyncStatus.online => L10n.t('updates.connectedDetail'),
      SyncStatus.syncing => L10n.t('updates.working'),
      SyncStatus.syncError => L10n.t('updates.problemDetail'),
      SyncStatus.updateAvailable => L10n.t('updates.readyToInstall'),
      SyncStatus.upToDate => L10n.t('updates.latest'),
    };
  }

  static Color _color(SyncStatus s) => switch (s) {
        SyncStatus.offline => AppColors.textMuted,
        SyncStatus.online || SyncStatus.upToDate => AppColors.primary,
        SyncStatus.syncing => AppColors.info,
        SyncStatus.syncError => AppColors.error,
        SyncStatus.updateAvailable => AppColors.warning,
      };

  static String _ago(DateTime? t) {
    if (t == null) return L10n.t('updates.notYet');
    final d = DateTime.now().difference(t);
    if (d.inMinutes < 1) return L10n.t('updates.justNow');
    if (d.inHours < 1) return L10n.n('updates.minutesAgo', d.inMinutes);
    if (d.inDays < 1) return L10n.n('updates.hoursAgo', d.inHours);
    return L10n.n('updates.daysAgo', d.inDays);
  }

  static String _mb(int? bytes) => bytes == null ? '' : '${(bytes / 1024).toStringAsFixed(0)} KB';

  static String _stage(InstallStage? s) => switch (s) {
        InstallStage.download => L10n.t('install.downloading'),
        InstallStage.validate => L10n.t('install.checking'),
        InstallStage.media => L10n.t('install.images'),
        InstallStage.apply => L10n.t('install.installing'),
        InstallStage.verify => L10n.t('install.verifying'),
        InstallStage.done => L10n.t('install.done'),
        null => L10n.t('install.starting'),
      };

  @override
  Widget build(BuildContext context) {
    final snap = ref.watch(syncEngineProvider);
    final busy = snap.status == SyncStatus.syncing || snap.installing;
    final color = _color(snap.status);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Text(context.t('about.syncUpdates')),
        leading: BackButton(onPressed: () => context.go('/home')),
      ),
      body: ListView(
        padding: const EdgeInsets.all(22),
        children: [
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.white,
              border: Border.all(color: AppColors.divider),
              boxShadow: AppSheen.card,
              borderRadius: BorderRadius.circular(AppRadius.standard),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.only(top: 3),
                  child: Icon(Icons.circle, size: 11, color: color),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(_label(snap.status), style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: color)),
                      const SizedBox(height: 4),
                      Text(_detail(snap), style: const TextStyle(fontSize: 11.5, height: 1.5, color: AppColors.textMuted)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          _row(context.t('updates.waitingToUpload'),
              snap.pendingCount == 0 ? context.t('updates.nothing') : context.tn('updates.items', snap.pendingCount)),
          _row(context.t('updates.lastSynced'), _ago(snap.lastSyncedAt)),
          _row(
            context.t('updates.installedContent'),
            snap.installedReleaseCode == null
                ? context.t('updates.noneYet')
                : '${snap.installedReleaseCode} · v${snap.installedVersion ?? '?'}',
          ),
          if (snap.availableRelease != null) ...[
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppColors.warningSurface,
                borderRadius: BorderRadius.circular(AppRadius.standard),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    [
                      context.t('updates.version', {'version': snap.availableRelease!.version}),
                      if (snap.availableRelease!.packageSize != null) _mb(snap.availableRelease!.packageSize),
                    ].join(' · '),
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.textStrong),
                  ),
                  if (snap.availableRelease!.description != null) ...[
                    const SizedBox(height: 4),
                    Text(snap.availableRelease!.description!, style: const TextStyle(fontSize: 11.5, height: 1.5, color: AppColors.textMuted)),
                  ],
                  const SizedBox(height: 10),
                  FilledButton(
                    onPressed: busy ? null : () => ref.read(syncEngineProvider.notifier).installAvailableUpdate(),
                    child: Text(context.t('updates.install')),
                  ),
                ],
              ),
            ),
          ],
          if (snap.installing) ...[
            const SizedBox(height: 14),
            Text(_stage(snap.installStage), style: const TextStyle(fontSize: 11.5, color: AppColors.textMuted)),
            const SizedBox(height: 6),
            LinearProgressIndicator(value: snap.installFraction <= 0 ? null : snap.installFraction),
            const SizedBox(height: 4),
            Text(
              context.t('updates.staysAvailable'),
              style: const TextStyle(fontSize: 10.5, color: AppColors.textMuted),
            ),
          ],
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: busy ? null : () => ref.read(syncEngineProvider.notifier).syncNow(manual: true),
            icon: const Icon(Icons.sync, size: 16),
            label: Text(context.t('updates.syncNow')),
          ),
          const SizedBox(height: 22),
          Container(
            padding: const EdgeInsets.fromLTRB(14, 6, 6, 6),
            decoration: BoxDecoration(
              color: AppColors.white,
              border: Border.all(color: AppColors.divider),
              boxShadow: AppSheen.card,
              borderRadius: BorderRadius.circular(AppRadius.standard),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    '${context.t('updates.shareUsage')}\n${context.t('updates.shareUsageDetail')}',
                    style: const TextStyle(fontSize: 11.5, height: 1.5, color: AppColors.textMuted),
                  ),
                ),
                Switch(
                  value: _consent ?? false,
                  onChanged: _consent == null
                      ? null
                      : (v) async {
                          await ref.read(settingsServiceProvider).setAnalyticsConsent(v);
                          if (mounted) setState(() => _consent = v);
                          await ref.read(syncEngineProvider.notifier).refreshLocalInfo();
                        },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _row(String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
            Flexible(
              child: Text(
                value,
                textAlign: TextAlign.right,
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.textStrong),
              ),
            ),
          ],
        ),
      );
}
