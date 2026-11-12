import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'home_screen.dart' show cachedModulesProvider;
import '../db/local_database.dart';
import '../learning/learning_rules.dart';
import '../learning/learning_service.dart';
import '../theme/app_theme.dart';
import '../widgets/partner_logo_row.dart';
import '../widgets/app_bottom_nav.dart';
import '../l10n/l10n.dart';

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
      appBar: BrandTopBar(appBar: AppBar(title: Text(context.t('modules.title')))),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(22, 12, 22, 6),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: context.t('modules.searchHint'),
                prefixIcon: const Icon(Icons.search, size: 18, color: AppColors.textMuted),
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
                      _query.isEmpty ? context.t('modules.none') : context.t('modules.noMatches', {'query': _query}),
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: AppColors.textMuted),
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
              error: (e, _) => Center(child: Text(context.t('home.loadFailed', {'error': e}), style: const TextStyle(color: AppColors.errorText))),
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
      title = context.t('general.preTitle');
      body = context.tn('general.preBody', general.questions);
      action = context.t('general.preAction');
      route = '/general-test/pre';
    } else if (post == null && general.canTakePost) {
      title = context.t('general.postTitle');
      body = context.tn('general.postBody', general.questions);
      action = context.t('general.postAction');
      route = '/general-test/post';
    } else if (post == null) {
      title = context.t('general.title');
      body = context.t('general.preScoreWaiting', {
        'correct': pre.correct,
        'total': pre.total,
        'percent': pre.percent,
        'done': general.modulesCompleted,
        'modules': general.modulesTotal,
      });
    } else {
      title = context.t('general.title');
      body = context.t('general.bothScores', {
        'preCorrect': pre.correct,
        'preTotal': pre.total,
        'prePercent': pre.percent,
        'postCorrect': post.correct,
        'postTotal': post.total,
        'postPercent': post.percent,
      });
    }
    return Container(
      margin: const EdgeInsets.fromLTRB(22, 0, 22, 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: route != null ? AppColors.surfaceSelected : AppColors.white,
        borderRadius: BorderRadius.circular(AppRadius.standard),
        border: Border.all(color: route != null ? AppColors.primary : AppColors.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(title, style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w800, color: AppColors.primary)),
          const SizedBox(height: 4),
          Text(body, style: const TextStyle(fontSize: 12, height: 1.45, color: AppColors.textMuted)),
          if (route != null) ...[
            const SizedBox(height: 10),
            FilledButton(
              onPressed: () => context.go(route!),
              style: FilledButton.styleFrom(backgroundColor: AppColors.primary, foregroundColor: AppColors.onPrimary),
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
          border: Border.all(color: AppColors.divider),
        ),
        child: Row(
          children: [
            Container(
              width: 30,
              height: 30,
              decoration: BoxDecoration(color: AppColors.surfaceSelected, borderRadius: BorderRadius.circular(9)),
              alignment: Alignment.center,
              child: Text(
                module.moduleNumber.toString(),
                style: const TextStyle(fontFamily: AppFonts.mono, fontWeight: FontWeight.w700, fontSize: 12, color: AppColors.primary),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(module.title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.textStrong)),
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
              color: state?.completed == true ? AppColors.success : AppColors.textDisabled,
            ),
          ],
        ),
      ),
    );
  }
}
