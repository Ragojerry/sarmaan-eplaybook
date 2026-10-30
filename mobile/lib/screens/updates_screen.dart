import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../services/settings_service.dart';
import '../sync/release_installer.dart';
import '../sync/sync_engine.dart';
import '../theme/app_theme.dart';

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
        SyncStatus.offline => 'Offline',
        SyncStatus.online => 'Connected',
        SyncStatus.syncing => 'Syncing…',
        SyncStatus.syncError => 'Sync problem',
        SyncStatus.updateAvailable => 'Update available',
        SyncStatus.upToDate => 'Up to date',
      };

  static String _detail(SyncSnapshot s) {
    if (s.message != null) return s.message!;
    return switch (s.status) {
      SyncStatus.offline => 'No connection to the server. Everything you have already downloaded still works, and your progress will upload when you are back online.',
      SyncStatus.online => 'Connected to the server.',
      SyncStatus.syncing => 'Working…',
      SyncStatus.syncError => 'Something went wrong. It will retry automatically.',
      SyncStatus.updateAvailable => 'New training content is ready to install.',
      SyncStatus.upToDate => 'You have the latest training content.',
    };
  }

  static Color _color(SyncStatus s) => switch (s) {
        SyncStatus.offline => AppColors.textMuted,
        SyncStatus.online || SyncStatus.upToDate => AppColors.teal,
        SyncStatus.syncing => AppColors.goldDeep,
        SyncStatus.syncError => AppColors.danger,
        SyncStatus.updateAvailable => AppColors.clay,
      };

  static String _ago(DateTime? t) {
    if (t == null) return 'Not yet';
    final d = DateTime.now().difference(t);
    if (d.inMinutes < 1) return 'Just now';
    if (d.inHours < 1) return '${d.inMinutes} min ago';
    if (d.inDays < 1) return '${d.inHours} h ago';
    return '${d.inDays} d ago';
  }

  static String _mb(int? bytes) => bytes == null ? '' : '${(bytes / 1024).toStringAsFixed(0)} KB';

  static String _stage(InstallStage? s) => switch (s) {
        InstallStage.download => 'Downloading…',
        InstallStage.validate => 'Checking the download…',
        InstallStage.media => 'Downloading images…',
        InstallStage.apply => 'Installing…',
        InstallStage.verify => 'Verifying…',
        InstallStage.done => 'Done',
        null => 'Starting…',
      };

  @override
  Widget build(BuildContext context) {
    final snap = ref.watch(syncEngineProvider);
    final busy = snap.status == SyncStatus.syncing || snap.installing;
    final color = _color(snap.status);

    return Scaffold(
      backgroundColor: AppColors.sand,
      appBar: AppBar(
        title: const Text('Sync & updates'),
        leading: BackButton(onPressed: () => context.go('/home')),
      ),
      body: ListView(
        padding: const EdgeInsets.all(22),
        children: [
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.white,
              border: Border.all(color: AppColors.line),
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
                      Text(_detail(snap), style: const TextStyle(fontSize: 11.5, height: 1.5, color: AppColors.textSecondary)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          _row('Waiting to upload', snap.pendingCount == 0 ? 'Nothing' : '${snap.pendingCount} item${snap.pendingCount == 1 ? '' : 's'}'),
          _row('Last synced', _ago(snap.lastSyncedAt)),
          _row(
            'Installed content',
            snap.installedReleaseCode == null ? 'None yet' : '${snap.installedReleaseCode} · v${snap.installedVersion ?? '?'}',
          ),
          if (snap.availableRelease != null) ...[
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppColors.claySoft,
                borderRadius: BorderRadius.circular(AppRadius.standard),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Version ${snap.availableRelease!.version}'
                    '${snap.availableRelease!.packageSize != null ? ' · ${_mb(snap.availableRelease!.packageSize)}' : ''}',
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.ink),
                  ),
                  if (snap.availableRelease!.description != null) ...[
                    const SizedBox(height: 4),
                    Text(snap.availableRelease!.description!, style: const TextStyle(fontSize: 11.5, height: 1.5, color: AppColors.textSecondary)),
                  ],
                  const SizedBox(height: 10),
                  FilledButton(
                    onPressed: busy ? null : () => ref.read(syncEngineProvider.notifier).installAvailableUpdate(),
                    child: const Text('Install update'),
                  ),
                ],
              ),
            ),
          ],
          if (snap.installing) ...[
            const SizedBox(height: 14),
            Text(_stage(snap.installStage), style: const TextStyle(fontSize: 11.5, color: AppColors.textSecondary)),
            const SizedBox(height: 6),
            LinearProgressIndicator(value: snap.installFraction <= 0 ? null : snap.installFraction),
            const SizedBox(height: 4),
            const Text(
              'Your current content stays available until the update is fully installed.',
              style: TextStyle(fontSize: 10.5, color: AppColors.textMuted),
            ),
          ],
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: busy ? null : () => ref.read(syncEngineProvider.notifier).syncNow(manual: true),
            icon: const Icon(Icons.sync, size: 16),
            label: const Text('Sync now'),
          ),
          const SizedBox(height: 22),
          Container(
            padding: const EdgeInsets.fromLTRB(14, 6, 6, 6),
            decoration: BoxDecoration(
              color: AppColors.white,
              border: Border.all(color: AppColors.line),
              borderRadius: BorderRadius.circular(AppRadius.standard),
            ),
            child: Row(
              children: [
                const Expanded(
                  child: Text(
                    'Share anonymous usage statistics\nWhich modules and videos are used, and app errors. Never your answers or questions.',
                    style: TextStyle(fontSize: 11.5, height: 1.5, color: AppColors.textSecondary),
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
            Text(label, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
            Flexible(
              child: Text(
                value,
                textAlign: TextAlign.right,
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.ink),
              ),
            ),
          ],
        ),
      );
}
