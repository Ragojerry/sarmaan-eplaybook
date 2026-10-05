import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../models/api_models.dart';
import '../services/auth_service.dart';
import '../services/settings_service.dart';
import '../theme/app_theme.dart';

/// Used only when nothing has ever been cached yet (a genuinely fresh
/// install with zero prior network contact). "bundled-*" ids are
/// deliberately not real server UUIDs — they're never sent back to the
/// API, only used to display this screen and to persist the user's
/// choice by language `code`.
const _bundledLanguages = [
  AppLanguage(id: 'bundled-en', code: 'en', name: 'English', nativeName: 'English', status: 'ACTIVE', isDefault: true),
  AppLanguage(id: 'bundled-ha', code: 'ha', name: 'Hausa', nativeName: 'Hausa', status: 'BETA', isDefault: false),
  AppLanguage(id: 'bundled-ff', code: 'ff', name: 'Fulfulde', nativeName: 'Fulfulde', status: 'BETA', isDefault: false),
  AppLanguage(id: 'bundled-kr', code: 'kr', name: 'Kanuri', nativeName: 'Kanuri', status: 'BETA', isDefault: false),
];

/// Cache-first language picker:
///
///   read cached languages -> found? show immediately : show bundled list
///                                        |
///                              API sync in background
///                                        |
///                        success -> save + refresh screen
///                        failure -> keep whatever's already shown
///
/// The picker is never blocked on the network and never shows a loading
/// spinner or an error banner for a failed sync — there's always something
/// correct to display (cache or bundled), and a network hiccup here would
/// otherwise stall the very first thing a new user sees.
class LanguageScreen extends ConsumerStatefulWidget {
  const LanguageScreen({super.key});

  @override
  ConsumerState<LanguageScreen> createState() => _LanguageScreenState();
}

class _LanguageScreenState extends ConsumerState<LanguageScreen> {
  List<AppLanguage> _languages = _bundledLanguages;
  String? _selectedCode;

  @override
  void initState() {
    super.initState();
    _loadInitial();
  }

  Future<void> _loadInitial() async {
    final cached = await ref.read(settingsServiceProvider).getCachedLanguages();
    if (cached != null && cached.isNotEmpty) {
      _applyLanguageList(cached);
    } else {
      _applyLanguageList(_bundledLanguages);
    }
    _syncInBackground();
  }

  void _applyLanguageList(List<AppLanguage> languages) {
    if (!mounted) return;
    setState(() {
      _languages = languages;
      // Keep the user's existing selection if it still exists in the new
      // list (e.g. cache -> fresh-sync swap mid-screen); otherwise fall
      // back to whichever entry the list marks as default.
      final stillPresent = _selectedCode != null && languages.any((l) => l.code == _selectedCode);
      _selectedCode = stillPresent
          ? _selectedCode
          : languages.firstWhere((l) => l.isDefault, orElse: () => languages.first).code;
    });
  }

  Future<void> _syncInBackground() async {
    try {
      final api = ref.read(apiClientProvider);
      final resp = await api.dio.get('/languages');
      final fresh = (resp.data as List).map((j) => AppLanguage.fromJson(j)).toList();
      if (fresh.isEmpty) return; // never replace a working list with an empty one

      await ref.read(settingsServiceProvider).setCachedLanguages(fresh);
      _applyLanguageList(fresh); // refresh screen with the up-to-date list
    } catch (_) {
      // Offline, or the request failed for any other reason — keep
      // showing whatever was already on screen (cache or bundled).
      // Silent by design: this is a background refresh, not a user action.
    }
  }

  Future<void> _continue() async {
    if (_selectedCode == null) return;
    await ref.read(settingsServiceProvider).setSelectedLanguageCode(_selectedCode!);
    if (mounted) context.go('/consent');
  }

  @override
  Widget build(BuildContext context) {
    // Matches the prototype's onboarding screens exactly: mono "eyebrow"
    // label with a gold tick mark, serif screen title, then custom
    // `.lang-option` cards (not default RadioListTiles) with a name/native
    // name pair, a gold "Beta" badge, and a circular check indicator that
    // fills teal when selected.
    return Scaffold(
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(22, 22, 22, 6),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(width: 16, height: 2, color: AppColors.gold),
                      const SizedBox(width: 8),
                      Text('STEP 1 OF 2', style: Theme.of(context).textTheme.labelSmall),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text('Choose your language', style: Theme.of(context).textTheme.headlineSmall),
                  const SizedBox(height: 4),
                  Text(
                    'Training content will be shown in this language where available.',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.fromLTRB(22, 12, 22, 12),
                children: [
                  for (final lang in _languages) _buildLanguageOption(lang),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(22, 0, 22, 22),
              child: FilledButton(onPressed: _continue, child: const Text('Continue')),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLanguageOption(AppLanguage lang) {
    final selected = _selectedCode == lang.code;
    return GestureDetector(
      onTap: () => setState(() => _selectedCode = lang.code),
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 15),
        decoration: BoxDecoration(
          color: selected ? AppColors.tealSoft : AppColors.white,
          borderRadius: BorderRadius.circular(AppRadius.standard),
          border: Border.all(color: selected ? AppColors.teal : AppColors.line, width: 1.5),
        ),
        child: Row(
          children: [
            Expanded(
              child: Row(
                children: [
                  Text(
                    lang.name,
                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14.5, color: AppColors.ink),
                  ),
                  if (lang.status == 'BETA')
                    Container(
                      margin: const EdgeInsets.only(left: 8),
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(color: AppColors.gold, borderRadius: BorderRadius.circular(5)),
                      child: const Text(
                        'BETA',
                        style: TextStyle(
                          fontFamily: AppFonts.mono,
                          fontSize: 9.5,
                          fontWeight: FontWeight.w700,
                          color: AppColors.tealDeep,
                        ),
                      ),
                    ),
                ],
              ),
            ),
            Container(
              width: 20,
              height: 20,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: selected ? AppColors.teal : Colors.transparent,
                border: Border.all(color: selected ? AppColors.teal : AppColors.line, width: 2),
              ),
              alignment: Alignment.center,
              child: selected
                  ? const Icon(Icons.check, size: 12, color: Colors.white)
                  : null,
            ),
          ],
        ),
      ),
    );
  }
}
