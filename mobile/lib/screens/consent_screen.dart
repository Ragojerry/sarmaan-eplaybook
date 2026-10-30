import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../services/settings_service.dart';
import '../theme/app_theme.dart';

/// Real consent copy, marks first-launch done (in the local Drift
/// app_settings table — Phase 8), then routes to login (per master prompt
/// Phase 7 screen order: splash, language, consent, login). Styled to
/// match the prototype's `.consent-box` (soft bordered card) and
/// `.btn-primary` treatment.
class ConsentScreen extends ConsumerStatefulWidget {
  const ConsentScreen({super.key});

  @override
  ConsumerState<ConsentScreen> createState() => _ConsentScreenState();
}

class _ConsentScreenState extends ConsumerState<ConsentScreen> {
  bool _shareUsage = false; // opt-in: off unless the person ticks it

  Future<void> _continue() async {
    final settings = ref.read(settingsServiceProvider);
    await settings.setAnalyticsConsent(_shareUsage);
    await settings.markFirstLaunchDone();
    if (mounted) context.go('/login');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(22, 22, 22, 22),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Container(width: 16, height: 2, color: AppColors.gold),
                  const SizedBox(width: 8),
                  Text('STEP 2 OF 2', style: Theme.of(context).textTheme.labelSmall),
                ],
              ),
              const SizedBox(height: 8),
              Text('Before you start', style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 20),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppColors.white,
                  border: Border.all(color: AppColors.line),
                  borderRadius: BorderRadius.circular(AppRadius.standard),
                ),
                child: const Text(
                  'This app is used to deliver AZM training content to Community Drug Distributors. '
                  'Your training progress and the questions you ask in the app are linked to your account and '
                  'uploaded when you are online, so your supervisor and the programme team can support you. '
                  'Module content is downloaded to this device so you can keep working without an internet connection.',
                  style: TextStyle(fontSize: 11.5, height: 1.6, color: AppColors.textSecondary),
                ),
              ),
              const SizedBox(height: 10),
              CheckboxListTile(
                value: _shareUsage,
                onChanged: (v) => setState(() => _shareUsage = v ?? false),
                contentPadding: EdgeInsets.zero,
                controlAffinity: ListTileControlAffinity.leading,
                title: const Text(
                  'Also share anonymous usage statistics (optional)',
                  style: TextStyle(fontSize: 11.5, color: AppColors.textSecondary),
                ),
              ),
              const Spacer(),
              FilledButton(onPressed: _continue, child: const Text('Agree and continue')),
            ],
          ),
        ),
      ),
    );
  }
}
