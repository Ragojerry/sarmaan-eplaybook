import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../l10n/l10n.dart';
import '../theme/app_theme.dart';
import '../tools/tools_service.dart';

/// The "Tools" section under the training modules (Home and Modules): one card
/// that opens the Tools repository. Deliberately unlike a module card: no
/// progress, tick, lock or time, and always open. Hidden when no Tools links are
/// assigned to this account.
class ToolsEntry extends ConsumerWidget {
  const ToolsEntry({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final data = ref.watch(toolsProvider).valueOrNull ?? ToolsData.empty;
    if (data.isEmpty) return const SizedBox.shrink();
    final subtitle = context.tn('tools.linkCount', data.linkCount);
    return Padding(
      padding: const EdgeInsets.fromLTRB(22, 22, 22, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Text(
              context.t('tools.sectionLabel'),
              style: const TextStyle(fontFamily: AppFonts.sans, fontSize: 11, fontWeight: FontWeight.w800, letterSpacing: 0.9, color: AppColors.textMuted),
            ),
          ),
          Semantics(
            button: true,
            label: '${context.t('tools.entryTitle')}, $subtitle',
            excludeSemantics: true,
            child: Material(
              color: AppColors.surface,
              shape: RoundedRectangleBorder(
                side: const BorderSide(color: AppColors.divider),
                borderRadius: BorderRadius.circular(AppRadius.medium),
              ),
              child: InkWell(
                borderRadius: BorderRadius.circular(AppRadius.medium),
                onTap: () => context.push('/tools'),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(minHeight: 64),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    child: Row(
                      children: [
                        Container(
                          width: 42,
                          height: 42,
                          decoration: BoxDecoration(color: AppColors.surfaceSelected, borderRadius: BorderRadius.circular(AppRadius.small)),
                          child: const Icon(Icons.home_repair_service_outlined, color: AppColors.primaryText),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(context.t('tools.entryTitle'),
                                  style: const TextStyle(fontSize: 14.5, fontWeight: FontWeight.w700, color: AppColors.textStrong)),
                              const SizedBox(height: 2),
                              Text(subtitle, style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
                            ],
                          ),
                        ),
                        const Icon(Icons.chevron_right_rounded, color: AppColors.textMuted),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
