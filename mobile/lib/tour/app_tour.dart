import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../db/local_database.dart';
import '../l10n/l10n.dart';
import '../learning/learning_rules.dart';
import '../offline/content_sync_service.dart' show localDatabaseProvider;
import '../services/auth_service.dart';
import '../support/support_contacts.dart';
import '../theme/app_theme.dart';
import '../tools/tools_service.dart';

/// One screen of the first-run tour: the icon of the area (as in the bottom
/// navigation), a title and a short text, all in the learner's language.
class TourStep {
  final IconData icon;
  final String title;
  final String body;

  const TourStep(this.icon, this.title, this.body);
}

/// The tour for this learner: only areas the app really has and this account can
/// see (the Tools step only when Tools are assigned; the support line in the Ask
/// step only when support contacts exist).
List<TourStep> tourSteps({required bool hasTools, required bool hasSupport}) => [
      TourStep(Icons.home_outlined, L10n.t('tour.homeTitle'), L10n.t('tour.homeBody')),
      TourStep(Icons.menu_book_outlined, L10n.t('tour.modulesTitle'), L10n.t('tour.modulesBody')),
      TourStep(Icons.play_circle_outline, L10n.t('tour.videosTitle'), L10n.t('tour.videosBody')),
      TourStep(Icons.chat_bubble_outline, L10n.t('tour.askTitle'),
          hasSupport ? '${L10n.t('tour.askBody')} ${L10n.t('tour.askSupport')}' : L10n.t('tour.askBody')),
      if (hasTools) TourStep(Icons.home_repair_service_outlined, L10n.t('tour.toolsTitle'), L10n.t('tour.toolsBody')),
      TourStep(Icons.info_outline, L10n.t('tour.aboutTitle'), L10n.t('tour.aboutBody')),
    ];

/// app_settings key: this account has seen (finished or skipped) the tour on this phone.
String tourSeenKey(String userId) => 'tour_seen_$userId';

Future<bool> tourSeen(LocalDatabase db, String userId) async => (await db.getSetting(tourSeenKey(userId))) == 'true';

Future<void> markTourSeen(LocalDatabase db, String userId) => db.setSetting(tourSeenKey(userId), 'true');

/// Shows the tour after the first sign-in on this phone, once: never before the
/// General pre-test is done (while it gates the modules), never over another
/// screen or dialog (so never in the middle of a quiz). Works offline.
Future<void> maybeShowFirstRunTour(BuildContext context, WidgetRef ref, GeneralLearning? general) async {
  final user = ref.read(authProvider).user;
  if (user == null || general == null || !general.gateOpen) return;
  final db = ref.read(localDatabaseProvider);
  if (await tourSeen(db, user.id)) return;
  if (!context.mounted || !(ModalRoute.of(context)?.isCurrent ?? false)) return;
  await showAppTour(context, ref);
}

/// The tour itself (also "Replay tour" in About). Skipping or finishing records it as seen.
Future<void> showAppTour(BuildContext context, WidgetRef ref) async {
  final tools = await ref.read(toolsProvider.future).catchError((_) => ToolsData.empty);
  final support = await ref.read(supportDeckProvider.future).catchError((_) => SupportDeckData.empty);
  if (!context.mounted) return;
  final steps = tourSteps(hasTools: !tools.isEmpty, hasSupport: support.contacts.isNotEmpty);
  await showDialog<void>(
    context: context,
    barrierDismissible: false,
    builder: (_) => AppTourDialog(steps: steps),
  );
  final user = ref.read(authProvider).user;
  if (user != null) await markTourSeen(ref.read(localDatabaseProvider), user.id);
}

class AppTourDialog extends StatefulWidget {
  final List<TourStep> steps;

  const AppTourDialog({super.key, required this.steps});

  @override
  State<AppTourDialog> createState() => _AppTourDialogState();
}

class _AppTourDialogState extends State<AppTourDialog> {
  int _i = 0;

  @override
  Widget build(BuildContext context) {
    final step = widget.steps[_i];
    final last = _i == widget.steps.length - 1;
    const tap = Size(64, 48);
    return AlertDialog(
      backgroundColor: AppColors.surface,
      titlePadding: const EdgeInsets.fromLTRB(20, 12, 8, 0),
      title: Row(
        children: [
          Expanded(
            child: Semantics(
              liveRegion: true,
              child: Text(context.t('tour.progress', {'step': _i + 1, 'count': widget.steps.length}),
                  style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700, color: AppColors.textMuted)),
            ),
          ),
          TextButton(
            style: TextButton.styleFrom(minimumSize: tap, foregroundColor: AppColors.primaryText),
            onPressed: () => Navigator.of(context).pop(),
            child: Text(context.t('tour.skip')),
          ),
        ],
      ),
      content: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 420),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(color: AppColors.surfaceSelected, borderRadius: BorderRadius.circular(AppRadius.medium)),
              child: Icon(step.icon, size: 30, color: AppColors.primaryText),
            ),
            const SizedBox(height: 14),
            Semantics(
              header: true,
              child: Text(step.title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: AppColors.textStrong)),
            ),
            const SizedBox(height: 8),
            Text(step.body, style: const TextStyle(fontSize: 14, height: 1.5, color: AppColors.text)),
            const SizedBox(height: 16),
            // The dots repeat the "2 of 6" above for sighted users.
            ExcludeSemantics(
              child: Row(
                children: [
                  for (var k = 0; k < widget.steps.length; k++)
                    Container(
                      margin: const EdgeInsets.only(right: 6),
                      width: k == _i ? 18 : 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: k == _i ? AppColors.primary : AppColors.divider,
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
      actions: [
        if (_i > 0)
          TextButton(
            style: TextButton.styleFrom(minimumSize: tap, foregroundColor: AppColors.primaryText),
            onPressed: () => setState(() => _i--),
            child: Text(context.t('tour.back')),
          ),
        FilledButton(
          style: FilledButton.styleFrom(minimumSize: tap, backgroundColor: AppColors.primary, foregroundColor: AppColors.onPrimary),
          onPressed: () => last ? Navigator.of(context).pop() : setState(() => _i++),
          child: Text(last ? context.t('tour.done') : context.t('tour.next')),
        ),
      ],
    );
  }
}
