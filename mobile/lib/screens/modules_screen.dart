import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'home_screen.dart' show cachedModulesProvider;
import '../db/local_database.dart';
import '../learning/learning_rules.dart';
import '../learning/learning_service.dart';
import '../theme/app_theme.dart';
import '../widgets/app_bottom_nav.dart';

/// Reads from the local cache (same provider Home uses) — real offline
/// module listing, per master prompt §18. Includes a simple local search
/// box, satisfying §19's "local search" requirement without any network
/// call at all. Styled to match the prototype's `.mod-row` list style
/// (mono index badge, bold title, meta line).
class ModulesScreen extends ConsumerStatefulWidget {
  const ModulesScreen({super.key});

  @override
  ConsumerState<ModulesScreen> createState() => _ModulesScreenState();
}

class _ModulesScreenState extends ConsumerState<ModulesScreen> {
  final _searchController = TextEditingController();
  String _query = '';

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final modulesAsync = ref.watch(cachedModulesProvider);
    final learning = ref.watch(learningProvider).valueOrNull;

    return Scaffold(
      appBar: AppBar(title: const Text('Modules')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(22, 12, 22, 6),
            child: TextField(
              controller: _searchController,
              decoration: const InputDecoration(
                hintText: 'Search modules…',
                prefixIcon: Icon(Icons.search, size: 18, color: AppColors.textMuted),
                isDense: true,
              ),
              style: const TextStyle(fontSize: 13),
              onChanged: (v) => setState(() => _query = v.trim().toLowerCase()),
            ),
          ),
          Expanded(
            child: modulesAsync.when(
              data: (modules) {
                final filtered = _query.isEmpty
                    ? modules
                    : modules.where((m) => m.title.toLowerCase().contains(_query)).toList();
                if (filtered.isEmpty) {
                  return Center(
                    child: Text(
                      _query.isEmpty ? 'No modules downloaded yet.' : 'No matches for "$_query".',
                      style: const TextStyle(color: AppColors.textSecondary),
                    ),
                  );
                }
                return ListView(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  children: [
                    if (learning != null && _query.isEmpty) GeneralTestCard(general: learning.general),
                    for (final m in filtered) _ModuleRow(module: m, state: learning?.of(m.id)),
                  ],
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('Could not load modules: $e', style: const TextStyle(color: AppColors.danger))),
            ),
          ),
        ],
      ),
      bottomNavigationBar: const AppBottomNav(currentRoute: '/modules'),
    );
  }
}

/// The General pre-/post-test at the top of the module list (when switched on):
/// the pre-test opens the modules; the post-test opens after all of them.
class GeneralTestCard extends StatelessWidget {
  final GeneralLearning general;

  const GeneralTestCard({super.key, required this.general});

  @override
  Widget build(BuildContext context) {
    if (!general.active || general.questions == 0) return const SizedBox.shrink();
    final pre = general.pre;
    final post = general.post;
    final String title;
    final String body;
    String? action;
    String? route;
    if (pre == null) {
      title = 'Start with the General pre-test';
      body = '${general.questions} questions about what you already know. Your modules open after you submit it. '
          'You take it once.';
      action = 'Start the pre-test';
      route = '/general-test/pre';
    } else if (post == null && general.canTakePost) {
      title = 'General post-test';
      body = 'You completed all your modules. Answer the same ${general.questions} questions again. You take it once.';
      action = 'Start the post-test';
      route = '/general-test/post';
    } else if (post == null) {
      title = 'General test';
      body = 'Pre-test: ${pre.correct} of ${pre.total} (${pre.percent}%). The post-test opens when you have '
          'completed all your modules (${general.modulesCompleted} of ${general.modulesTotal}).';
    } else {
      title = 'General test';
      body = 'Pre-test: ${pre.correct} of ${pre.total} (${pre.percent}%). '
          'Post-test: ${post.correct} of ${post.total} (${post.percent}%).';
    }
    return Container(
      margin: const EdgeInsets.fromLTRB(22, 0, 22, 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: route != null ? AppColors.tealSoft : AppColors.white,
        borderRadius: BorderRadius.circular(AppRadius.standard),
        border: Border.all(color: route != null ? AppColors.teal : AppColors.line),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(title, style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w800, color: AppColors.tealDeep)),
          const SizedBox(height: 4),
          Text(body, style: const TextStyle(fontSize: 12, height: 1.45, color: AppColors.textSecondary)),
          if (route != null) ...[
            const SizedBox(height: 10),
            FilledButton(
              onPressed: () => context.go(route!),
              style: FilledButton.styleFrom(backgroundColor: AppColors.tealDeep, foregroundColor: AppColors.sand),
              child: Text(action!),
            ),
          ],
        ],
      ),
    );
  }
}

class _ModuleRow extends StatelessWidget {
  final CachedModuleRow module;
  final ModuleLearning? state;

  const _ModuleRow({required this.module, this.state});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => context.go('/reader/${module.id}'),
      child: Container(
        margin: const EdgeInsets.fromLTRB(22, 0, 22, 10),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
        decoration: BoxDecoration(
          color: AppColors.white,
          borderRadius: BorderRadius.circular(AppRadius.standard),
          border: Border.all(color: AppColors.line),
        ),
        child: Row(
          children: [
            Container(
              width: 30,
              height: 30,
              decoration: BoxDecoration(color: AppColors.tealSoft, borderRadius: BorderRadius.circular(9)),
              alignment: Alignment.center,
              child: Text(
                module.moduleNumber.toString(),
                style: const TextStyle(fontFamily: AppFonts.mono, fontWeight: FontWeight.w700, fontSize: 12, color: AppColors.tealDeep),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(module.title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.ink)),
                  const SizedBox(height: 2),
                  Text(
                    state == null ? module.moduleCode : '${module.moduleCode} · ${stageLabel(state!.stage)}',
                    style: const TextStyle(fontSize: 10.5, color: AppColors.textMuted),
                  ),
                ],
              ),
            ),
            Icon(
              state?.stage == ModuleStage.locked
                  ? Icons.lock_outline
                  : state?.completed == true
                      ? Icons.check_circle
                      : Icons.chevron_right,
              color: state?.completed == true ? AppColors.teal : const Color(0xFFB7C0BA),
            ),
          ],
        ),
      ),
    );
  }
}
