import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'services/auth_service.dart';
import 'theme/brand_identity.g.dart';
import 'l10n/app_strings_service.dart';
import 'l10n/l10n.dart';
import 'navigation/app_router.dart';
import 'offline/content_sync_service.dart' show localDatabaseProvider;
import 'sync/error_reporter.dart';
import 'sync/sync_lifecycle.dart';
import 'theme/app_theme.dart';

/// Phase 7 scope: real screens (splash, language, consent, login, home,
/// modules, reader, videos, about), all talking to the live backend built
/// in Phases 3-6. Offline storage (Phase 8), offline video (Phase 9), and
/// AI (Phase 10/11) are not yet wired — see app_router.dart and
/// app_bottom_nav.dart for exactly what's in scope and why.
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final container = ProviderContainer();
  ErrorReporter.install(container); // opt-in APPLICATION_ERROR events (type only)
  // Interface text in the learner's language from the first frame (cached on the
  // phone; English until downloaded), then refreshed in the background.
  var code = 'en';
  try {
    code = await container.read(localDatabaseProvider).getSetting('selected_language_code') ?? 'en';
    await container.read(appStringsServiceProvider).show(code);
  } catch (_) {}
  runApp(UncontrolledProviderScope(container: container, child: const SarmaanEPlaybookApp()));
  container.read(appStringsServiceProvider).sync(code);
}

class SarmaanEPlaybookApp extends ConsumerWidget {
  const SarmaanEPlaybookApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);
    // A deactivated account is signed out from wherever it was (a sync, any screen):
    // back to sign-in, which explains why.
    ref.listen<AuthState>(authProvider, (previous, next) {
      if (next.deactivated && !(previous?.deactivated ?? false)) router.go('/login');
    });
    return MaterialApp.router(
      title: BrandIdentity.title,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      routerConfig: router,
      builder: (context, child) => L10nScope(child: SyncLifecycle(child: child ?? const SizedBox.shrink())),
    );
  }
}
