import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../services/auth_service.dart';
import '../services/settings_service.dart';
import '../theme/app_theme.dart';
import '../widgets/partner_logo_row.dart';
import '../l10n/l10n.dart';

/// Real routing logic: first launch -> language picker; returning user with
/// a valid session (checked via /auth/me, including the client's built-in
/// refresh-on-401 retry) -> home; otherwise -> login. No network call is
/// made here directly — AuthNotifier's _restoreSession (constructed via
/// apiClientProvider/authProvider) does that, and this screen just waits on
/// its result.
class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _decideRoute());
  }

  Future<void> _decideRoute() async {
    try {
      final settings = ref.read(settingsServiceProvider);
      final firstLaunch = await settings.isFirstLaunch();
      if (firstLaunch) {
        if (mounted) context.go('/language');
        return;
      }

      // Wait for AuthNotifier's initial session-restore check to finish.
      while (ref.read(authProvider).loading) {
        await Future.delayed(const Duration(milliseconds: 100));
        if (!mounted) return;
      }

      final isLoggedIn = ref.read(authProvider).isLoggedIn;
      if (!mounted) return;
      context.go(isLoggedIn ? '/home' : '/login');
    } catch (_) {
      // A local-database failure (corrupted file, disk full, or — in a
      // test/CI environment — a missing platform channel for path_provider)
      // must never strand the user on a spinner forever. Falling back to
      // login is always safe: it doesn't depend on local storage at all,
      // and re-authenticating naturally re-establishes everything else.
      if (mounted) context.go('/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    // Brand splash: the app name on Forest Green, and the partner logos on a white
    // band below (the supplied logo files are only approved on white/light
    // backgrounds; order and size come from assets/brand/logos.json).
    return Scaffold(
      backgroundColor: AppColors.white,
      body: Column(
        children: [
          Expanded(
            child: Container(
              width: double.infinity,
              decoration: const BoxDecoration(gradient: AppSheen.hero),
              child: SafeArea(
                bottom: false,
                child: Center(child: _title()),
              ),
            ),
          ),
          const SafeArea(
              top: false, child: PartnerLogoRow(placement: 'splash')),
        ],
      ),
    );
  }

  Widget _title() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // The SARMAAN-II logo on its own white card, as on the login screen.
        const SarmaanLogoMark(),
        const SizedBox(height: 22),
        Text(
          context.t('app.name'),
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontFamily: AppFonts.serif,
            fontSize: 26,
            fontWeight: FontWeight.w600,
            color: AppColors.onPrimary,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          context.t('splash.subtitle'),
          textAlign: TextAlign.center,
          style: TextStyle(
            fontFamily: AppFonts.mono,
            fontSize: 11,
            letterSpacing: 1.5,
            color: AppColors.onPrimary.withValues(alpha: 0.75),
          ),
        ),
        const SizedBox(height: 34),
        SizedBox(
          width: 140,
          height: 3,
          child: ClipRRect(
            borderRadius: BorderRadius.circular(AppRadius.pill),
            child: LinearProgressIndicator(
              backgroundColor: AppColors.onPrimary.withValues(alpha: 0.2),
              valueColor: const AlwaysStoppedAnimation(AppColors.onPrimary),
            ),
          ),
        ),
      ],
    );
  }
}
