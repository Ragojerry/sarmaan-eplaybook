import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../screens/tools_screen.dart';
import '../screens/certificate_screen.dart';
import '../screens/splash_screen.dart';
import '../screens/language_screen.dart';
import '../screens/consent_screen.dart';
import '../screens/login_screen.dart';
import '../screens/home_screen.dart';
import '../screens/modules_screen.dart';
import '../screens/quiz_screen.dart';
import '../screens/reader_screen.dart';
import '../screens/video_library_screen.dart';
import '../screens/video_screen.dart';
import '../screens/about_screen.dart';
import '../screens/ai_screen.dart';
import '../screens/updates_screen.dart';
import '../screens/update_required_screen.dart';
import '../learning/curriculum_notice.dart';
import '../offline/content_sync_service.dart';

/// Splash, language, consent, login, home, modules, reader, videos, Ask (AI),
/// about, and (Phase 12) the sync & updates screen.
final appRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/splash',
    // The training screens are closed when the server needs a newer app (min_app_version).
    // Other screens (splash, login, ...) are never delayed: they return synchronously.
    redirect: (context, state) {
      const gated = ['/home', '/modules', '/reader', '/general-test', '/certificate'];
      if (!gated.any((p) => state.matchedLocation.startsWith(p))) return null;
      return updateRequired(ref.read(localDatabaseProvider)).then((needed) => needed ? '/update-required' : null);
    },
    routes: [
      GoRoute(path: '/splash', builder: (context, state) => const SplashScreen()),
      GoRoute(path: '/language', builder: (context, state) => LanguageScreen(changing: state.uri.queryParameters['change'] == '1')),
      GoRoute(path: '/consent', builder: (context, state) => const ConsentScreen()),
      GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
      GoRoute(path: '/home', builder: (context, state) => const HomeScreen()),
      GoRoute(path: '/modules', builder: (context, state) => const ModulesScreen()),
      GoRoute(
        path: '/reader/:moduleId',
        builder: (context, state) => ReaderScreen(moduleId: state.pathParameters['moduleId']!),
      ),
      // The General pre-/post-test (the per-module tests were retired in 2026-11).
      GoRoute(
        path: '/general-test/:type',
        builder: (context, state) => GeneralTestScreen(testType: state.pathParameters['type'] == 'post' ? 'POST' : 'PRE'),
      ),
      GoRoute(path: '/videos', builder: (context, state) => const VideoLibraryScreen()),
      GoRoute(
        path: '/videos/:videoId',
        builder: (context, state) => VideoScreen(videoId: state.pathParameters['videoId']!),
      ),
      GoRoute(path: '/ai', builder: (context, state) => const AiScreen()),
      // Tools repository: not gated (open before the General pre-test; not training).
      GoRoute(path: '/tools', builder: (context, state) => const ToolsScreen()),
      GoRoute(path: '/about', builder: (context, state) => const AboutScreen()),
      GoRoute(path: '/updates', builder: (context, state) => const UpdatesScreen()),
      GoRoute(path: '/certificate', builder: (context, state) => const CertificateScreen()),
      GoRoute(path: '/update-required', builder: (context, state) => const UpdateRequiredScreen()),
    ],
  );
});
