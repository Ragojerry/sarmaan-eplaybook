import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../models/consent_text.dart';
import '../services/auth_service.dart';
import '../services/settings_service.dart';
import '../theme/app_theme.dart';

/// Consent copy in the language chosen on the previous screen (edited and
/// translated in the admin portal; cached, with English and then the copy
/// built into the app as fallbacks). Records which text was agreed to, marks
/// first-launch done (in the local Drift app_settings table — Phase 8), then
/// routes to login (per master prompt Phase 7 screen order: splash, language,
/// consent, login). Styled to match the prototype's `.consent-box` (soft
/// bordered card) and `.btn-primary` treatment.
class ConsentScreen extends ConsumerStatefulWidget {
  const ConsentScreen({super.key});

  @override
  ConsumerState<ConsentScreen> createState() => _ConsentScreenState();
}

class _ConsentScreenState extends ConsumerState<ConsentScreen> {
  bool _shareUsage = false; // opt-in: off unless the person ticks it
  ConsentText _text = kBundledConsent;
  String? _language;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final settings = ref.read(settingsServiceProvider);
    _language = await settings.getSelectedLanguageCode();
    _show(await settings.getCachedConsent());
    try {
      // Pick up an edit made since the language screen fetched the texts.
      final resp = await ref.read(apiClientProvider).dio.get('/consent');
      final fresh = [for (final j in resp.data as List) ConsentText.fromJson(j as Map<String, dynamic>)];
      if (fresh.isEmpty) return;
      await settings.setCachedConsent(fresh);
      _show(fresh);
    } catch (_) {
      // Offline: the cached (or built-in) text is already on screen.
    }
  }

  void _show(List<ConsentText>? texts) {
    if (mounted) setState(() => _text = pickConsent(texts, _language));
  }

  Future<void> _continue() async {
    final settings = ref.read(settingsServiceProvider);
    await settings.recordAcceptedConsent(_text);
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
                  Container(width: 16, height: 2, color: AppColors.primary),
                  const SizedBox(width: 8),
                  Text('STEP 2 OF 2', style: Theme.of(context).textTheme.labelSmall),
                ],
              ),
              const SizedBox(height: 8),
              Text(_text.title, style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 20),
              // Admins edit this text, so a long version scrolls instead of
              // pushing the checkbox and button off small screens.
              Flexible(
                child: Container(
                  decoration: BoxDecoration(
                    color: AppColors.white,
                    border: Border.all(color: AppColors.divider),
                    borderRadius: BorderRadius.circular(AppRadius.standard),
                  ),
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(14),
                    child: Text(
                      _text.body,
                      style: const TextStyle(fontSize: 11.5, height: 1.6, color: AppColors.textMuted),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 10),
              CheckboxListTile(
                value: _shareUsage,
                onChanged: (v) => setState(() => _shareUsage = v ?? false),
                contentPadding: EdgeInsets.zero,
                controlAffinity: ListTileControlAffinity.leading,
                title: Text(
                  _text.usageLabel,
                  style: const TextStyle(fontSize: 11.5, color: AppColors.textMuted),
                ),
              ),
              const Spacer(),
              FilledButton(onPressed: _continue, child: Text(_text.buttonLabel)),
            ],
          ),
        ),
      ),
    );
  }
}
