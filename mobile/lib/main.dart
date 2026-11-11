import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'navigation/app_router.dart';
import 'sync/error_reporter.dart';
import 'sync/sync_lifecycle.dart';
import 'theme/app_theme.dart';

/// Phase 7 scope: real screens (splash, language, consent, login, home,
/// modules, reader, videos, about), all talking to the live backend built
/// in Phases 3-6. Offline storage (Phase 8), offline video (Phase 9), and
/// AI (Phase 10/11) are not yet wired — see app_router.dart and
/// app_bottom_nav.dart for exactly what's in scope and why.
void main() {
  WidgetsFlutterBinding.ensureInitialized();
  final container = ProviderContainer();
  ErrorReporter.install(container); // opt-in APPLICATION_ERROR events (type only)
  runApp(UncontrolledProviderScope(container: container, child: const SarmaanEPlaybookApp()));
}

class SarmaanEPlaybookApp extends ConsumerWidget {
  const SarmaanEPlaybookApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);
    return MaterialApp.router(
      title: 'SARMAAN II e-Playbook',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      routerConfig: router,
      builder: (context, child) => SyncLifecycle(child: child ?? const SizedBox.shrink()),
    );
  }
}
