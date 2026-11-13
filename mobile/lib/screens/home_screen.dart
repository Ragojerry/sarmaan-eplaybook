import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../db/local_database.dart';
import '../learning/curriculum_notice.dart';
import '../learning/learning_rules.dart';
import '../learning/learning_service.dart';
import '../models/api_models.dart' show UserProfile;
import '../offline/content_sync_service.dart';
import '../services/auth_service.dart';
import '../sync/release_installer.dart' show ReleaseInfo;
import '../sync/sync_engine.dart';
import '../theme/app_theme.dart';
import '../widgets/partner_logo_row.dart';
import '../widgets/app_bottom_nav.dart';
import '../widgets/module_state_marks.dart';
import '../widgets/tools_entry.dart';
import '../l10n/l10n.dart';
import '../tour/app_tour.dart';
import 'modules_screen.dart' show GeneralTestCard;

/// Reads from the LOCAL cache (Phase 8), never directly from the network —
/// this is what makes master prompt §18's offline-first guarantee real
/// rather than aspirational. Network only gets touched by ContentSyncService,
/// triggered here on first load if the cache is empty, or on manual
/// pull-to-refresh. Watching contentRevision reloads the list whenever a sync
/// installs content, even if that happened while Home wasn't on screen.
final cachedModulesProvider = FutureProvider<List<CachedModuleRow>>((ref) async {
  ref.watch(syncEngineProvider.select((v) => v.contentRevision));
  final db = ref.read(localDatabaseProvider);
  return db.getAllModules();
});

/// Everything the Home cards need beyond the module list, read locally:
/// per-module progress and section counts. autoDispose so it reloads each
/// time Home is shown (e.g. after reading a module).
class HomeExtras {
  final Map<String, LocalProgressRow> progress;
  final Map<String, int> sectionCounts;
  final LearningSnapshot learning;
  const HomeExtras(this.progress, this.sectionCounts, this.learning);
}

final homeExtrasProvider = FutureProvider.autoDispose<HomeExtras>((ref) async {
  final db = ref.read(localDatabaseProvider);
  final modules = await db.getAllModules();
  final progress = {for (final p in await db.getAllProgress()) p.moduleId: p};
  final counts = <String, int>{};
  for (final m in modules) {
    counts[m.id] = (await db.getSectionsForModule(m.id)).length;
  }
  return HomeExtras(progress, counts, await loadLearning(db));
});

/// Local search index: the Q&A passages already stored on the phone.
final homeChunksProvider = FutureProvider.autoDispose<List<ContentChunkRow>>((ref) async {
  return ref.read(localDatabaseProvider).getChunks('en');
});

class _SearchHit {
  final String moduleId;
  final String moduleCode;
  final String title;
  final String snippet;
  const _SearchHit(this.moduleId, this.moduleCode, this.title, this.snippet);
}

/// Offline search: every typed word must appear in a passage (or in a module
/// title). Titles rank first, then passages with the most occurrences.
List<_SearchHit> _search(String query, List<CachedModuleRow> modules, List<ContentChunkRow> chunks) {
  final terms = query.toLowerCase().split(RegExp(r'[^a-z0-9]+')).where((t) => t.length >= 2).toList();
  if (terms.isEmpty) return const [];
  final hits = <(int, _SearchHit)>[];
  for (final m in modules) {
    final t = m.title.toLowerCase();
    if (terms.every(t.contains)) hits.add((1000, _SearchHit(m.id, m.moduleCode, m.title, m.description ?? '')));
  }
  for (final c in chunks) {
    final text = c.chunkText.toLowerCase();
    final head = (c.sectionTitle ?? '').toLowerCase();
    if (!terms.every((t) => text.contains(t) || head.contains(t))) continue;
    var score = 0;
    for (final t in terms) {
      score += RegExp(RegExp.escape(t)).allMatches(text).length + (head.contains(t) ? 3 : 0);
    }
    final first = text.indexOf(terms.first);
    final start = first < 0 ? 0 : (first - 40).clamp(0, text.length);
    final end = (start + 140).clamp(0, c.chunkText.length);
    final snippet = '${start > 0 ? '…' : ''}${c.chunkText.substring(start, end).trim()}${end < c.chunkText.length ? '…' : ''}';
    hits.add((score, _SearchHit(c.moduleId, c.moduleCode, c.sectionTitle ?? c.sourceTitle, snippet)));
  }
  hits.sort((a, b) => b.$1.compareTo(a.$1));
  return [for (final h in hits.take(10)) h.$2];
}

String _greeting() {
  final h = DateTime.now().hour;
  return h < 12 ? L10n.t('home.goodMorning') : (h < 17 ? L10n.t('home.goodAfternoon') : L10n.t('home.goodEvening'));
}

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  bool _syncing = false;
  String? _syncError;
  final TextEditingController _searchController = TextEditingController();
  String _query = '';

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await _syncIfCacheEmpty();
      await _showTrainingNotice();
      await _maybeShowTour();
    });
  }

  /// The first-run tour, once per account on this phone, after the General pre-test.
  Future<void> _maybeShowTour() async {
    if (!mounted) return;
    try {
      final extras = await ref.read(homeExtrasProvider.future);
      if (mounted) await maybeShowFirstRunTour(context, ref, extras.learning.general);
    } catch (_) {}
  }

  /// One-time notice after the curriculum changeover (set by the release installer).
  Future<void> _showTrainingNotice() async {
    if (!mounted) return;
    await showTrainingNoticeIfPending(context, ref.read(localDatabaseProvider));
  }

  Future<void> _syncIfCacheEmpty() async {
    final db = ref.read(localDatabaseProvider);
    final hasContent = await db.hasCachedContent();
    if (!hasContent) {
      await _runSync();
    }
  }

  /// The Home "Sync" button: upload what is waiting, check for new content,
  /// and install an optional update straight away (tapping it asks for that).
  Future<void> _syncAndUpdate() async {
    final engine = ref.read(syncEngineProvider.notifier);
    var installed = false;
    try {
      await engine.syncNow(manual: true);
      if (!mounted) return;
      if (ref.read(syncEngineProvider).availableRelease != null) {
        await engine.installAvailableUpdate();
        installed = ref.read(syncEngineProvider).availableRelease == null;
      }
    } catch (_) {
      // The engine records the problem in its status; reported below.
    }
    if (!mounted) return;
    final snap = ref.read(syncEngineProvider);
    final text = switch (snap.status) {
      SyncStatus.offline => L10n.t('sync.offlineWillUpload'),
      SyncStatus.syncError => snap.message ?? L10n.t('sync.failed'),
      _ => installed ? L10n.t('sync.updateInstalled') : L10n.t('sync.done'),
    };
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(text)));
  }

  Future<void> _runSync() async {
    setState(() {
      _syncing = true;
      _syncError = null;
    });
    try {
      await ref.read(syncEngineProvider.notifier).syncNow(manual: true);
      ref.invalidate(cachedModulesProvider);
      final hasContent = await ref.read(localDatabaseProvider).hasCachedContent();
      if (!hasContent && mounted) {
        final offline = ref.read(syncEngineProvider).status == SyncStatus.offline;
        setState(() => _syncError = offline ? L10n.t('home.offlineFirstDownload') : L10n.t('home.downloadFailed'));
      }
    } catch (e) {
      if (mounted) setState(() => _syncError = L10n.t('home.downloadFailed'));
    } finally {
      if (mounted) setState(() => _syncing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(authProvider).user;
    final modulesAsync = ref.watch(cachedModulesProvider);
    final extras = ref.watch(homeExtrasProvider).valueOrNull;
    final snap = ref.watch(syncEngineProvider);
    ref.listen<int>(syncEngineProvider.select((v) => v.contentRevision), (_, __) {
      ref.invalidate(cachedModulesProvider);
      ref.invalidate(homeExtrasProvider);
      ref.invalidate(homeChunksProvider);
      _showTrainingNotice();
    });
    final modules = modulesAsync.valueOrNull ?? const <CachedModuleRow>[];
    final searching = _query.trim().isNotEmpty;

    return Scaffold(
      appBar: const BrandTopBar(),
      backgroundColor: AppColors.background,
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.go('/ai'),
        backgroundColor: AppColors.primary,
        foregroundColor: AppColors.onPrimary,
        tooltip: context.t('home.askTooltip'),
        child: const Icon(Icons.auto_awesome),
      ),
      body: RefreshIndicator(
        onRefresh: _runSync,
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            _buildHeader(_who(user), snap.status != SyncStatus.offline, snap.availableRelease != null),
            if (_syncing)
              Padding(
                padding: const EdgeInsets.fromLTRB(22, 16, 22, 0),
                child: Row(
                  children: [
                    const SizedBox(height: 14, width: 14, child: CircularProgressIndicator(strokeWidth: 2)),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(context.t('home.downloading'), style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
                    ),
                  ],
                ),
              ),
            if (_syncError != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(22, 16, 22, 0),
                child: Text(_syncError!, style: const TextStyle(color: AppColors.errorText, fontSize: 12)),
              ),
            if (searching)
              _buildSearchResults(modules)
            else ...[
              _SyncCard(snap: snap, onSync: _syncAndUpdate),
              if (snap.availableRelease != null) _UpdateBanner(release: snap.availableRelease!),
              ..._buildContinueReading(modules, extras),
              // The General pre-test opens the modules; the post-test follows them.
              if (extras != null) GeneralTestCard(general: extras.learning.general),
              _SectionLabel(context.t('home.modulesHeading')),
              modulesAsync.when(
                data: (modules) => modules.isEmpty
                    ? Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 22),
                        child: Text(context.t('home.noModules'), style: const TextStyle(color: AppColors.textMuted)),
                      )
                    : Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 22),
                        child: GridView.count(
                          crossAxisCount: 2,
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          mainAxisSpacing: 11,
                          crossAxisSpacing: 11,
                          childAspectRatio: 1.05,
                          children: [
                            for (final m in modules)
                              _ModuleCard(
                                module: m,
                                completed: extras?.progress[m.id]?.completed ?? false,
                                percent: extras?.progress[m.id]?.progressPercent ?? 0,
                                sectionCount: extras?.sectionCounts[m.id],
                                stage: extras?.learning.of(m.id)?.stage,
                                active: m.id == _activeModuleId(modules, extras),
                              ),
                          ],
                        ),
                      ),
                loading: () => const Padding(
                  padding: EdgeInsets.all(32),
                  child: Center(child: CircularProgressIndicator()),
                ),
                error: (e, _) => Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 22),
                  child: Text(context.t('home.loadFailed', {'error': e}), style: const TextStyle(color: AppColors.errorText)),
                ),
              ),
              // Separate from the training modules above: links only, no progress or locks.
              const ToolsEntry(),
            ],
            const SizedBox(height: 90),
          ],
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentRoute: '/home'),
    );
  }

  /// The module to work on next: the first open one not yet completed (modules
  /// open one after another, so there is at most one). None before the General
  /// pre-test, and none once every module is completed.
  String? _activeModuleId(List<CachedModuleRow> modules, HomeExtras? extras) {
    if (extras == null) return null;
    for (final m in modules) {
      if (extras.learning.of(m.id)?.stage == ModuleStage.reading) return m.id;
    }
    return null;
  }

  /// One card per module the learner has started but not finished, most
  /// recently opened first, each showing that module's own progress. Locked
  /// modules (General pre-test not taken, or an earlier module unfinished) are
  /// left out: their reading progress is kept and they come back once unlocked.
  List<Widget> _buildContinueReading(List<CachedModuleRow> modules, HomeExtras? extras) {
    if (extras == null) return const [];
    final byId = {for (final m in modules) m.id: m};
    final started = [
      for (final p in extras.progress.values)
        if (!p.completed &&
            p.progressPercent > 0 &&
            byId.containsKey(p.moduleId) &&
            extras.learning.of(p.moduleId)?.stage != ModuleStage.locked)
          p,
    ]..sort((a, b) => (b.lastOpenedAt ?? DateTime(0)).compareTo(a.lastOpenedAt ?? DateTime(0)));
    if (started.isEmpty) return const [];
    return [
      for (var i = 0; i < started.length; i++)
        Padding(
          padding: EdgeInsets.fromLTRB(22, i == 0 ? 18 : 10, 22, 0),
          child: _ContinueCard(module: byId[started[i].moduleId]!, progress: started[i]),
        ),
    ];
  }

  Widget _buildSearchResults(List<CachedModuleRow> modules) {
    final chunks = ref.watch(homeChunksProvider).valueOrNull ?? const <ContentChunkRow>[];
    final hits = _search(_query, modules, chunks);
    return Padding(
      padding: const EdgeInsets.fromLTRB(22, 18, 22, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            hits.isEmpty ? context.t('search.noMatches') : context.t('search.results'),
            style: const TextStyle(
              fontFamily: AppFonts.sans,
              fontSize: 11,
              fontWeight: FontWeight.w800,
              letterSpacing: 0.9,
              color: AppColors.textMuted,
            ),
          ),
          const SizedBox(height: 10),
          if (hits.isEmpty)
            Text(
              context.t('search.nothingFound'),
              style: const TextStyle(color: AppColors.textMuted, fontSize: 13),
            ),
          for (final h in hits)
            GestureDetector(
              onTap: () => context.go('/reader/${h.moduleId}'),
              child: Container(
                width: double.infinity,
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(13),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(AppRadius.medium),
                  border: Border.all(color: AppColors.divider),
                  boxShadow: AppSheen.card,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        _CodeBadge(h.moduleCode),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            h.title,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.textStrong),
                          ),
                        ),
                      ],
                    ),
                    if (h.snippet.isNotEmpty) ...[
                      const SizedBox(height: 6),
                      Text(h.snippet, style: const TextStyle(fontSize: 12, height: 1.45, color: AppColors.textMuted)),
                    ],
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  /// Matches the prototype's `.home-top`: teal gradient, mono greeting,
  /// serif title, online pill and a search field.
  /// The signed-in user's first and last name.
  String? _who(UserProfile? user) {
    if (user == null) return null;
    final name = '${user.firstName} ${user.lastName}'.trim();
    return name.isEmpty ? null : name;
  }

  /// Header pill in the same style as the Online pill, shown only while a
  /// newer content release is waiting; it opens the Updates screen.
  Widget _updatePill() {
    return GestureDetector(
      onTap: () => context.go('/updates'),
      child: Container(
        margin: const EdgeInsets.only(right: 6),
        padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
        decoration: BoxDecoration(color: AppColors.infoSurface, borderRadius: BorderRadius.circular(20)),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.download_rounded, size: 11, color: AppColors.infoText),
            const SizedBox(width: 4),
            Text(
              context.t('home.newContent'),
              style: const TextStyle(fontFamily: AppFonts.mono, fontSize: 10.5, fontWeight: FontWeight.w700, color: AppColors.primaryText),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(String? who, bool online, bool updateAvailable) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(22, 20, 22, 22),
      // The sheen: deep teal behind the small greeting, IHS Teal under the title, a soft glow below.
      decoration: BoxDecoration(
        gradient: AppSheen.header,
        borderRadius: const BorderRadius.only(bottomLeft: Radius.circular(26), bottomRight: Radius.circular(26)),
        boxShadow: AppSheen.glow,
      ),
      child: SafeArea(
        bottom: false,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    '${_greeting()}${who != null ? ' · ${who.toUpperCase()}' : ''}',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontFamily: AppFonts.mono,
                      fontSize: 11.5,
                      letterSpacing: 0.5,
                      color: AppColors.onPrimary.withValues(alpha: 0.75),
                    ),
                  ),
                ),
                if (updateAvailable) _updatePill(),
                // Connection status only; syncing lives in the Sync & update card.
                Semantics(
                  label: online ? context.t('common.online') : context.t('common.offline'),
                  excludeSemantics: true,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.onPrimary.withValues(alpha: 0.16),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        // The accent: the success green would vanish on the Forest Green header.
                        Icon(Icons.circle, size: 7, color: online ? AppColors.accent : AppColors.onPrimaryMuted.withValues(alpha: 0.5)),
                        const SizedBox(width: 5),
                        Text(
                          online ? context.t('common.online') : context.t('common.offline'),
                          style: const TextStyle(fontFamily: AppFonts.mono, fontSize: 10.5, color: AppColors.onPrimary),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              context.t('home.title'),
              style: const TextStyle(fontFamily: AppFonts.serif, fontSize: 24, fontWeight: FontWeight.w600, color: AppColors.onPrimary),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _searchController,
              onChanged: (v) => setState(() => _query = v),
              textInputAction: TextInputAction.search,
              style: const TextStyle(color: AppColors.onPrimary, fontSize: 13.5),
              cursorColor: AppColors.onPrimary,
              decoration: InputDecoration(
                hintText: context.t('search.hint'),
                hintStyle: TextStyle(color: AppColors.onPrimary.withValues(alpha: 0.6), fontSize: 13.5),
                prefixIcon: Icon(Icons.search, color: AppColors.onPrimary.withValues(alpha: 0.8)),
                suffixIcon: _query.isEmpty
                    ? null
                    : IconButton(
                        icon: const Icon(Icons.close, size: 18, color: AppColors.onPrimary),
                        onPressed: () {
                          _searchController.clear();
                          setState(() => _query = '');
                        },
                      ),
                filled: true,
                fillColor: AppColors.onPrimary.withValues(alpha: 0.14),
                contentPadding: const EdgeInsets.symmetric(vertical: 12),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide(color: AppColors.onPrimary.withValues(alpha: 0.25)),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide(color: AppColors.onPrimary.withValues(alpha: 0.25)),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: const BorderSide(color: AppColors.onPrimary),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  final String text;
  const _SectionLabel(this.text);

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.fromLTRB(22, 22, 22, 10),
        child: Text(
          text,
          style: const TextStyle(
            fontFamily: AppFonts.sans,
            fontSize: 11,
            fontWeight: FontWeight.w800,
            letterSpacing: 0.9,
            color: AppColors.textMuted,
          ),
        ),
      );
}

class _CodeBadge extends StatelessWidget {
  final String code;

  /// Logo teal for the module to work on next.
  final bool next;
  const _CodeBadge(this.code, {this.next = false});

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
        decoration: BoxDecoration(color: next ? AppColors.primary : AppColors.surfaceSelected, borderRadius: BorderRadius.circular(5)),
        child: Text(
          code,
          style: TextStyle(
              fontFamily: AppFonts.mono,
              fontSize: 9.5,
              fontWeight: FontWeight.w700,
              color: next ? AppColors.onPrimary : AppColors.textStrong),
        ),
      );
}

String _syncedAgo(DateTime? t) {
  if (t == null) return L10n.t('sync.notYet');
  final d = DateTime.now().difference(t);
  if (d.inMinutes < 1) return L10n.t('sync.justNow');
  if (d.inHours < 1) return L10n.n('sync.minutesAgo', d.inMinutes);
  if (d.inDays < 1) return L10n.n('sync.hoursAgo', d.inHours);
  return L10n.n('sync.daysAgo', d.inDays);
}

/// "Sync & update" card: last sync time, changes waiting to upload, and a
/// button that syncs and installs any waiting content update.
class _SyncCard extends StatelessWidget {
  final SyncSnapshot snap;
  final VoidCallback onSync;
  const _SyncCard({required this.snap, required this.onSync});

  @override
  Widget build(BuildContext context) {
    final busy = snap.status == SyncStatus.syncing || snap.installing;
    final waiting = snap.pendingCount;
    final String detail;
    if (snap.installing) {
      final pct = (snap.installFraction * 100).round();
      detail = pct > 0 ? context.t('sync.installingPercent', {'percent': pct}) : context.t('sync.installing');
    } else if (busy) {
      detail = context.t('sync.syncing');
    } else {
      detail = [
        _syncedAgo(snap.lastSyncedAt),
        if (waiting > 0) context.tn('sync.waitingToUpload', waiting),
      ].join(' · ');
    }
    return Padding(
      padding: const EdgeInsets.fromLTRB(22, 16, 22, 0),
      child: Container(
        padding: const EdgeInsets.fromLTRB(14, 10, 10, 10),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.medium),
          border: Border.all(color: AppColors.divider),
          boxShadow: AppSheen.card,
        ),
        child: Row(
          children: [
            SizedBox(
              width: 22,
              height: 22,
              child: busy
                  ? const Padding(padding: EdgeInsets.all(3), child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.sync, size: 22, color: AppColors.primary),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    context.t('sync.cardTitle'),
                    style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w700, color: AppColors.textStrong),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    detail,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            FilledButton(
              onPressed: busy ? null : onSync,
              style: FilledButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: AppColors.onPrimary,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                visualDensity: VisualDensity.compact,
              ),
              child: Text(context.t('sync.button')),
            ),
          ],
        ),
      ),
    );
  }
}

/// Amber banner shown when a newer content release is waiting to download.
class _UpdateBanner extends StatelessWidget {
  final ReleaseInfo release;
  const _UpdateBanner({required this.release});

  @override
  Widget build(BuildContext context) {
    final size = release.packageSize;
    final mb = size == null ? '' : ' · ${(size / 1024 / 1024).toStringAsFixed(1)} MB';
    return Padding(
      padding: const EdgeInsets.fromLTRB(22, 16, 22, 0),
      child: GestureDetector(
        onTap: () => context.go('/updates'),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
              color: AppColors.infoSurface,
              border: Border.all(color: AppColors.info),
              borderRadius: BorderRadius.circular(AppRadius.medium)),
          child: Row(
            children: [
              const Icon(Icons.info_outline, size: 16, color: AppColors.info),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      context.t('updates.available'),
                      style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w700, color: AppColors.textStrong),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      '${release.releaseCode}$mb',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontFamily: AppFonts.mono, fontSize: 10.5, color: AppColors.primaryText),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: AppColors.textStrong),
            ],
          ),
        ),
      ),
    );
  }
}

/// The "Continue" hero card: Forest Green to logo teal, a pale teal label and Continue
/// button, and the module's progress in pale teal on a 28% white track. A photo, when
/// one is added, goes at the top and fades into the card through [AppSheen.photoFade].
class _ContinueCard extends StatelessWidget {
  final CachedModuleRow module;
  final LocalProgressRow progress;
  const _ContinueCard({required this.module, required this.progress});

  @override
  Widget build(BuildContext context) {
    final where = progress.lastSection;
    void open() => context.go('/reader/${module.id}');
    return GestureDetector(
      onTap: open,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: AppSheen.hero,
          borderRadius: BorderRadius.circular(AppRadius.large),
          boxShadow: AppSheen.glow,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 3),
                  decoration: BoxDecoration(color: AppColors.accent, borderRadius: BorderRadius.circular(AppRadius.pill)),
                  child: Text(
                    context.t('home.continueReading'),
                    style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w800, letterSpacing: 0.8, color: AppColors.onAccent),
                  ),
                ),
                const Spacer(),
                Text(
                  module.moduleCode,
                  style: const TextStyle(fontFamily: AppFonts.mono, fontWeight: FontWeight.w700, color: AppColors.onPrimaryMuted),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              module.title,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, height: 1.3, color: AppColors.onPrimary),
            ),
            const SizedBox(height: 4),
            Text(
              [
                context.t('home.percentComplete', {'percent': progress.progressPercent}),
                if (where != null && where.isNotEmpty) where,
              ].join(' · '),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 11.5, color: AppColors.onPrimaryMuted),
            ),
            const SizedBox(height: 10),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: progress.progressPercent / 100,
                minHeight: 6,
                backgroundColor: AppColors.onPrimary.withValues(alpha: 0.28),
                valueColor: const AlwaysStoppedAnimation(AppColors.accent),
              ),
            ),
            const SizedBox(height: 14),
            Align(
              alignment: Alignment.centerRight,
              child: FilledButton(
                onPressed: open,
                style: FilledButton.styleFrom(
                  backgroundColor: AppColors.accent,
                  foregroundColor: AppColors.onAccent,
                  padding: const EdgeInsets.symmetric(horizontal: 22),
                  visualDensity: VisualDensity.compact,
                ).copyWith(
                  // Pale teal with the glossy top edge, instead of the theme's teal gradient.
                  backgroundBuilder: (context, states, child) => ClipRRect(
                    borderRadius: BorderRadius.circular(AppRadius.standard),
                    child: DecoratedBox(decoration: const BoxDecoration(gradient: AppSheen.gloss), child: child),
                  ),
                ),
                child: Text(context.t('common.continue')),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Matches the prototype's `.module-card`: code badge, completion tick,
/// bold title, and a "N sections · offline" meta line.
class _ModuleCard extends StatelessWidget {
  final CachedModuleRow module;
  final bool completed;
  final int percent;
  final int? sectionCount;
  final ModuleStage? stage;

  /// The module to work on next: teal outline, teal number badge and a glow.
  final bool active;

  const _ModuleCard({required this.module, this.completed = false, this.percent = 0, this.sectionCount, this.stage, this.active = false});

  @override
  Widget build(BuildContext context) {
    final locked = stage == ModuleStage.locked;
    return GestureDetector(
      onTap: () => context.go('/reader/${module.id}'),
      child: CustomPaint(
        foregroundPainter: locked ? const DashedOutline(color: AppColors.primary, radius: AppRadius.medium) : null,
        child: Container(
          padding: const EdgeInsets.all(13),
          decoration: BoxDecoration(
            color: locked ? AppColors.surfaceMuted : AppColors.surface,
            borderRadius: BorderRadius.circular(AppRadius.medium),
            border: active
                ? Border.all(color: AppColors.primary, width: 2)
                : locked
                    ? null
                    : Border.all(color: AppColors.divider),
            boxShadow: active ? AppSheen.glow : (locked ? null : AppSheen.card),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _CodeBadge(module.moduleCode, next: active),
                  if (completed) const DoneMark(),
                  if (locked) const Icon(Icons.lock_outline, size: 16, color: AppColors.textMuted),
                ],
              ),
              const SizedBox(height: 8),
              Expanded(
                child: Text(
                  module.title,
                  maxLines: 4,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                      fontSize: 12.5,
                      fontWeight: FontWeight.w700,
                      height: 1.35,
                      color: locked ? AppColors.textMuted : AppColors.textStrong),
                ),
              ),
              const SizedBox(height: 6),
              Row(
                children: [
                  const Icon(Icons.menu_book_outlined, size: 12, color: AppColors.textMuted),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      [
                        if (sectionCount != null) context.tn('home.sectionCount', sectionCount!),
                        stage != null && stage != ModuleStage.reading && !completed
                            ? stageLabel(stage!)
                            : !completed && percent > 0
                                ? context.t('home.percentRead', {'percent': percent})
                                : context.t('home.availableOffline'),
                      ].join(' · '),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 10.5, color: AppColors.textMuted),
                    ),
                  ),
                ],
              ),
              if (!completed && !locked && percent > 0) ...[
                const SizedBox(height: 6),
                ClipRRect(
                  borderRadius: BorderRadius.circular(3),
                  child: LinearProgressIndicator(
                    value: percent / 100,
                    minHeight: 4,
                    backgroundColor: AppColors.surfaceMuted,
                    valueColor: const AlwaysStoppedAnimation(AppColors.primary),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
