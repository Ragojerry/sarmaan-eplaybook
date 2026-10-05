import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../services/auth_service.dart';
import '../services/settings_service.dart';
import '../theme/app_theme.dart';

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
    // Matches the prototype's .splash: teal-deep -> teal gradient, gold
    // "splash-mark" square with the app's initial, serif title, and a
    // pill-shaped loading bar in place of the CircularProgressIndicator.
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [AppColors.tealDeep, AppColors.teal],
          ),
        ),
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 84,
                height: 84,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(AppRadius.large),
                  border: Border.all(color: Colors.white.withValues(alpha: 0.25)),
                ),
                alignment: Alignment.center,
                child: const Text(
                  'S',
                  style: TextStyle(
                    fontFamily: AppFonts.serif,
                    fontWeight: FontWeight.w700,
                    fontSize: 34,
                    color: AppColors.gold,
                  ),
                ),
              ),
              const SizedBox(height: 22),
              const Text(
                'SARMAAN e-Playbook',
                style: TextStyle(
                  fontFamily: AppFonts.serif,
                  fontSize: 26,
                  fontWeight: FontWeight.w600,
                  color: AppColors.sand,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                'AZM TRAINING',
                style: TextStyle(
                  fontFamily: AppFonts.mono,
                  fontSize: 11,
                  letterSpacing: 1.5,
                  color: AppColors.sand.withValues(alpha: 0.75),
                ),
              ),
              const SizedBox(height: 34),
              SizedBox(
                width: 140,
                height: 3,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(AppRadius.pill),
                  child: LinearProgressIndicator(
                    backgroundColor: Colors.white.withValues(alpha: 0.2),
                    valueColor: const AlwaysStoppedAnimation(AppColors.gold),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
