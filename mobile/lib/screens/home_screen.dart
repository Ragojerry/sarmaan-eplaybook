import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../db/local_database.dart';
import '../models/api_models.dart' show UserProfile;
import '../offline/content_sync_service.dart';
import '../services/auth_service.dart';
import '../sync/release_installer.dart' show ReleaseInfo;
import '../sync/sync_engine.dart';
import '../theme/app_theme.dart';
import '../widgets/app_bottom_nav.dart';

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
  const HomeExtras(this.progress, this.sectionCounts);
}

final homeExtrasProvider = FutureProvider.autoDispose<HomeExtras>((ref) async {
  final db = ref.read(localDatabaseProvider);
  final modules = await db.getAllModules();
  final progress = {for (final p in await db.getAllProgress()) p.moduleId: p};
  final counts = <String, int>{};
  for (final m in modules) {
    counts[m.id] = (await db.getSectionsForModule(m.id)).length;
  }
  return HomeExtras(progress, counts);
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
  final terms = query
      .toLowerCase()
      .split(RegExp(r'[^a-z0-9]+'))
      .where((t) => t.length >= 2)
      .toList();
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
  return h < 12 ? 'GOOD MORNING' : (h < 17 ? 'GOOD AFTERNOON' : 'GOOD EVENING');
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
      await ref.read(syncEngineProvider.notifier).syncNow(manual: true);
      ref.invalidate(cachedModulesProvider);
      final hasContent = await ref.read(localDatabaseProvider).hasCachedContent();
      if (!hasContent && mounted) {
        final offline = ref.read(syncEngineProvider).status == SyncStatus.offline;
        setState(() => _syncError = offline
            ? 'You are offline. Connect once to download your training content.'
            : 'Could not download content. Check your connection and try again.');
      }
    } catch (e) {
      if (mounted) setState(() => _syncError = 'Could not download content. Check your connection and try again.');
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
    });
    final modules = modulesAsync.valueOrNull ?? const <CachedModuleRow>[];
    final searching = _query.trim().isNotEmpty;

    return Scaffold(
      backgroundColor: AppColors.sand,
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.go('/ai'),
        backgroundColor: AppColors.gold,
        foregroundColor: AppColors.tealDeep,
        tooltip: 'Ask a question',
        child: const Icon(Icons.auto_awesome),
      ),
      body: RefreshIndicator(
        onRefresh: _runSync,
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            _buildHeader(_who(user), snap.status != SyncStatus.offline, snap.availableRelease != null),
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
            if (searching)
              _buildSearchResults(modules)
            else ...[
              if (snap.availableRelease != null) _UpdateBanner(release: snap.availableRelease!),
              ..._buildContinueReading(modules, extras),
              const _SectionLabel('SARMAAN-II · AZM MDA MODULES'),
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
                          childAspectRatio: 1.05,
                          children: [
                            for (final m in modules)
                              _ModuleCard(
                                module: m,
                                completed: extras?.progress[m.id]?.completed ?? false,
                                percent: extras?.progress[m.id]?.progressPercent ?? 0,
                                sectionCount: extras?.sectionCounts[m.id],
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
                  child: Text('Could not load modules: $e', style: const TextStyle(color: AppColors.danger)),
                ),
              ),
            ],
            const SizedBox(height: 90),
          ],
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentRoute: '/home'),
    );
  }

  /// One card per module the learner has started but not finished, most
  /// recently opened first, each showing that module's own progress.
  List<Widget> _buildContinueReading(List<CachedModuleRow> modules, HomeExtras? extras) {
    if (extras == null) return const [];
    final byId = {for (final m in modules) m.id: m};
    final started = [
      for (final p in extras.progress.values)
        if (!p.completed && p.progressPercent > 0 && byId.containsKey(p.moduleId)) p,
    ]..sort((a, b) => (b.lastOpenedAt ?? DateTime(0)).compareTo(a.lastOpenedAt ?? DateTime(0)));
    if (started.isEmpty) return const [];
    return [
      const _SectionLabel('CONTINUE READING'),
      for (var i = 0; i < started.length; i++)
        Padding(
          padding: EdgeInsets.fromLTRB(22, i == 0 ? 0 : 10, 22, 0),
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
            hits.isEmpty ? 'NO MATCHES' : 'RESULTS',
            style: const TextStyle(
              fontFamily: AppFonts.sans, fontSize: 11, fontWeight: FontWeight.w800, letterSpacing: 0.9, color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 10),
          if (hits.isEmpty)
            const Text(
              'Nothing in your downloaded modules matches that. Try one word, or use the Ask button.',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
            ),
          for (final h in hits)
            GestureDetector(
              onTap: () => context.go('/reader/${h.moduleId}'),
              child: Container(
                width: double.infinity,
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(13),
                decoration: BoxDecoration(
                  color: AppColors.white,
                  borderRadius: BorderRadius.circular(AppRadius.medium),
                  border: Border.all(color: AppColors.line),
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
                            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.ink),
                          ),
                        ),
                      ],
                    ),
                    if (h.snippet.isNotEmpty) ...[
                      const SizedBox(height: 6),
                      Text(h.snippet, style: const TextStyle(fontSize: 12, height: 1.45, color: AppColors.textSecondary)),
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
  /// "CDD TEAM 0041" when the account has a team code, otherwise the first name.
  String? _who(UserProfile? user) {
    if (user == null) return null;
    final team = user.teamCode?.trim();
    if (team != null && team.isNotEmpty) return '${user.role == 'CDD' ? 'CDD ' : ''}TEAM $team';
    return user.firstName;
  }

  /// Header pill in the same style as the Online pill, shown only while a
  /// newer content release is waiting; it opens the Updates screen.
  Widget _updatePill() {
    return GestureDetector(
      onTap: () => context.go('/updates'),
      child: Container(
        margin: const EdgeInsets.only(right: 6),
        padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
        decoration: BoxDecoration(color: AppColors.gold, borderRadius: BorderRadius.circular(20)),
        child: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.download_rounded, size: 11, color: AppColors.tealDeep),
            SizedBox(width: 4),
            Text(
              'New content',
              style: TextStyle(fontFamily: AppFonts.mono, fontSize: 10.5, fontWeight: FontWeight.w700, color: AppColors.tealDeep),
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
                      color: AppColors.sand.withValues(alpha: 0.75),
                    ),
                  ),
                ),
                if (updateAvailable) _updatePill(),
                GestureDetector(
                  onTap: () => context.go('/updates'),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.sand.withValues(alpha: 0.16),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.circle, size: 7, color: online ? const Color(0xFF7FE0B0) : AppColors.textMuted),
                        const SizedBox(width: 5),
                        Text(
                          online ? 'Online' : 'Offline',
                          style: const TextStyle(fontFamily: AppFonts.mono, fontSize: 10.5, color: AppColors.sand),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            const Text(
              "Ready for today's round",
              style: TextStyle(fontFamily: AppFonts.serif, fontSize: 24, fontWeight: FontWeight.w600, color: AppColors.sand),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _searchController,
              onChanged: (v) => setState(() => _query = v),
              textInputAction: TextInputAction.search,
              style: const TextStyle(color: AppColors.sand, fontSize: 13.5),
              cursorColor: AppColors.gold,
              decoration: InputDecoration(
                hintText: 'Search modules, e.g. "MUAC", "referral"…',
                hintStyle: TextStyle(color: AppColors.sand.withValues(alpha: 0.6), fontSize: 13.5),
                prefixIcon: Icon(Icons.search, color: AppColors.sand.withValues(alpha: 0.8)),
                suffixIcon: _query.isEmpty
                    ? null
                    : IconButton(
                        icon: const Icon(Icons.close, size: 18, color: AppColors.sand),
                        onPressed: () {
                          _searchController.clear();
                          setState(() => _query = '');
                        },
                      ),
                filled: true,
                fillColor: AppColors.sand.withValues(alpha: 0.14),
                contentPadding: const EdgeInsets.symmetric(vertical: 12),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide(color: AppColors.sand.withValues(alpha: 0.25)),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide(color: AppColors.sand.withValues(alpha: 0.25)),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: const BorderSide(color: AppColors.gold),
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
            color: AppColors.textSecondary,
          ),
        ),
      );
}

class _CodeBadge extends StatelessWidget {
  final String code;
  const _CodeBadge(this.code);

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
        decoration: BoxDecoration(color: AppColors.claySoft, borderRadius: BorderRadius.circular(5)),
        child: Text(
          code,
          style: const TextStyle(fontFamily: AppFonts.mono, fontSize: 9.5, fontWeight: FontWeight.w700, color: AppColors.goldDeep),
        ),
      );
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
          decoration: BoxDecoration(color: AppColors.gold, borderRadius: BorderRadius.circular(AppRadius.medium)),
          child: Row(
            children: [
              const Icon(Icons.circle, size: 9, color: AppColors.clay),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Content update available',
                      style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w700, color: AppColors.ink),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      '${release.releaseCode}$mb',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontFamily: AppFonts.mono, fontSize: 10.5, color: AppColors.tealDeep),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: AppColors.ink),
            ],
          ),
        ),
      ),
    );
  }
}

/// A "Continue reading" card: code tile, title, "N% complete · section" and a bar.
class _ContinueCard extends StatelessWidget {
  final CachedModuleRow module;
  final LocalProgressRow progress;
  const _ContinueCard({required this.module, required this.progress});

  @override
  Widget build(BuildContext context) {
    final where = progress.lastSection;
    return GestureDetector(
      onTap: () => context.go('/reader/${module.id}'),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.white,
          borderRadius: BorderRadius.circular(AppRadius.medium),
          border: Border.all(color: AppColors.line),
        ),
        child: Row(
          children: [
            Container(
              width: 52,
              height: 52,
              alignment: Alignment.center,
              decoration: BoxDecoration(color: AppColors.tealSoft, borderRadius: BorderRadius.circular(12)),
              child: Text(
                module.moduleCode,
                style: const TextStyle(fontFamily: AppFonts.mono, fontWeight: FontWeight.w700, color: AppColors.tealDeep),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    module.title,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, height: 1.3, color: AppColors.ink),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    '${progress.progressPercent}% complete${where != null && where.isNotEmpty ? ' · $where' : ''}',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 11.5, color: AppColors.textSecondary),
                  ),
                  const SizedBox(height: 8),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: progress.progressPercent / 100,
                      minHeight: 6,
                      backgroundColor: AppColors.sandDeep,
                      valueColor: const AlwaysStoppedAnimation(AppColors.teal),
                    ),
                  ),
                ],
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

  const _ModuleCard({required this.module, this.completed = false, this.percent = 0, this.sectionCount});

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
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _CodeBadge(module.moduleCode),
                if (completed) const Icon(Icons.check, size: 16, color: AppColors.teal),
              ],
            ),
            const SizedBox(height: 8),
            Expanded(
              child: Text(
                module.title,
                maxLines: 4,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700, height: 1.35, color: AppColors.ink),
              ),
            ),
            const SizedBox(height: 6),
            Row(
              children: [
                const Icon(Icons.menu_book_outlined, size: 12, color: AppColors.textMuted),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    '${sectionCount != null ? '$sectionCount sections · ' : ''}'
                    '${!completed && percent > 0 ? '$percent% read' : 'offline'}',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 10.5, color: AppColors.textSecondary),
                  ),
                ),
              ],
            ),
            if (!completed && percent > 0) ...[
              const SizedBox(height: 6),
              ClipRRect(
                borderRadius: BorderRadius.circular(3),
                child: LinearProgressIndicator(
                  value: percent / 100,
                  minHeight: 4,
                  backgroundColor: AppColors.sandDeep,
                  valueColor: const AlwaysStoppedAnimation(AppColors.teal),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
