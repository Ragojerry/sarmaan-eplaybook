import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'home_screen.dart' show cachedModulesProvider;
import '../db/local_database.dart';
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
                  children: [for (final m in filtered) _ModuleRow(module: m)],
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

class _ModuleRow extends StatelessWidget {
  final CachedModuleRow module;

  const _ModuleRow({required this.module});

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
                  Text(module.moduleCode, style: const TextStyle(fontSize: 10.5, color: AppColors.textMuted)),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: Color(0xFFB7C0BA)),
          ],
        ),
      ),
    );
  }
}
