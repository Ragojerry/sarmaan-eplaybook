import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../db/local_database.dart';
import '../offline/content_sync_service.dart';
import '../services/auth_service.dart';
import '../theme/app_theme.dart';
import '../widgets/app_bottom_nav.dart';

/// Reads from the LOCAL cache (Phase 8), never directly from the network —
/// this is what makes master prompt §18's offline-first guarantee real
/// rather than aspirational. Network only gets touched by ContentSyncService,
/// triggered here on first load if the cache is empty, or on manual
/// pull-to-refresh.
final cachedModulesProvider = FutureProvider<List<CachedModuleRow>>((ref) async {
  final db = ref.read(localDatabaseProvider);
  return db.getAllModules();
});

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  bool _syncing = false;
  String? _syncError;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _syncIfCacheEmpty());
  }

  Future<void> _syncIfCacheEmpty() async {
    final db = ref.read(localDatabaseProvider);
    final hasContent = await db.hasCachedContent();
    if (!hasContent) {
      await _runSync();
    }
  }

  Future<void> _runSync() async {
    setState(() {
      _syncing = true;
      _syncError = null;
    });
    try {
      await ref.read(contentSyncServiceProvider).syncAll();
      ref.invalidate(cachedModulesProvider);
    } catch (e) {
      setState(() => _syncError = 'Could not download content. Check your connection and try again.');
    } finally {
      if (mounted) setState(() => _syncing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(authProvider).user;
    final modulesAsync = ref.watch(cachedModulesProvider);

    return Scaffold(
      backgroundColor: AppColors.sand,
      body: RefreshIndicator(
        onRefresh: _runSync,
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            _buildHeader(user?.firstName),
            if (_syncing)
              const Padding(
                padding: EdgeInsets.fromLTRB(22, 16, 22, 0),
                child: Row(
                  children: [
                    SizedBox(height: 14, width: 14, child: CircularProgressIndicator(strokeWidth: 2)),
                    SizedBox(width: 10),
                    Text('Downloading content for offline use…', style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                  ],
                ),
              ),
            if (_syncError != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(22, 16, 22, 0),
                child: Text(_syncError!, style: const TextStyle(color: AppColors.danger, fontSize: 12)),
              ),
            const Padding(
              padding: EdgeInsets.fromLTRB(22, 22, 22, 10),
              child: Text(
                'MODULES',
                style: TextStyle(
                  fontFamily: AppFonts.sans,
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0.9,
                  color: AppColors.textSecondary,
                ),
              ),
            ),
            modulesAsync.when(
              data: (modules) => modules.isEmpty
                  ? const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 22),
                      child: Text('No modules downloaded yet. Pull down to sync.', style: TextStyle(color: AppColors.textSecondary)),
                    )
                  : Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 22),
                      child: GridView.count(
                        crossAxisCount: 2,
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        mainAxisSpacing: 11,
                        crossAxisSpacing: 11,
                        childAspectRatio: 1.35,
                        children: [for (final m in modules) _ModuleCard(module: m)],
                      ),
                    ),
              loading: () => const Padding(
                padding: EdgeInsets.all(32),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (e, _) => Padding(
                padding: const EdgeInsets.symmetric(horizontal: 22),
                child: Text('Could not load modules: $e', style: const TextStyle(color: AppColors.danger)),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentRoute: '/home'),
    );
  }

  /// Matches the prototype's `.home-top`: teal-deep -> teal gradient,
  /// rounded bottom corners, mono greeting line + serif title.
  Widget _buildHeader(String? firstName) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(22, 20, 22, 24),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [AppColors.tealDeep, AppColors.teal],
        ),
        borderRadius: BorderRadius.only(bottomLeft: Radius.circular(26), bottomRight: Radius.circular(26)),
      ),
      child: SafeArea(
        bottom: false,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'WELCOME BACK',
              style: TextStyle(
                fontFamily: AppFonts.mono,
                fontSize: 11.5,
                letterSpacing: 0.5,
                color: AppColors.sand.withValues(alpha: 0.75),
              ),
            ),
            const SizedBox(height: 2),
            Text(
              firstName ?? 'CDD',
              style: const TextStyle(
                fontFamily: AppFonts.serif,
                fontSize: 21,
                fontWeight: FontWeight.w600,
                color: AppColors.sand,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Matches the prototype's `.module-card`: white card, clay-soft mono
/// "module number" badge, bold title, small meta line.
class _ModuleCard extends StatelessWidget {
  final CachedModuleRow module;

  const _ModuleCard({required this.module});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => context.go('/reader/${module.id}'),
      child: Container(
        padding: const EdgeInsets.all(13),
        decoration: BoxDecoration(
          color: AppColors.white,
          borderRadius: BorderRadius.circular(AppRadius.medium),
          border: Border.all(color: AppColors.line),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(color: AppColors.claySoft, borderRadius: BorderRadius.circular(5)),
              child: Text(
                module.moduleCode,
                style: const TextStyle(
                  fontFamily: AppFonts.mono,
                  fontSize: 9.5,
                  fontWeight: FontWeight.w700,
                  color: AppColors.goldDeep,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Expanded(
              child: Text(
                module.title,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700, height: 1.35, color: AppColors.ink),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
