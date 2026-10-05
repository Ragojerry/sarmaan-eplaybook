import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../screens/splash_screen.dart';
import '../screens/language_screen.dart';
import '../screens/consent_screen.dart';
import '../screens/login_screen.dart';
import '../screens/home_screen.dart';
import '../screens/modules_screen.dart';
import '../screens/reader_screen.dart';
import '../screens/video_library_screen.dart';
import '../screens/video_screen.dart';
import '../screens/about_screen.dart';

/// Phase 7 scope: splash, language, consent, login, home, modules, reader,
/// videos, about — exactly the screen list in master prompt Phase 7, no
/// more. `/downloading`, `/updates`, and `/ai` are deliberately NOT routed
/// here: offline content download is Phase 8/9 scope, update installation
/// is Phase 12, and the AI assistant is Phase 10/11 — routing to those
/// screens now would mean either fresh stubs (the exact prototype problem
/// this project exists to fix) or half-built features. Their screen files
/// still exist under lib/screens/ for when those phases build them out.
final appRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/splash',
    routes: [
      GoRoute(path: '/splash', builder: (context, state) => const SplashScreen()),
      GoRoute(path: '/language', builder: (context, state) => const LanguageScreen()),
      GoRoute(path: '/consent', builder: (context, state) => const ConsentScreen()),
      GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
      GoRoute(path: '/home', builder: (context, state) => const HomeScreen()),
      GoRoute(path: '/modules', builder: (context, state) => const ModulesScreen()),
      GoRoute(
        path: '/reader/:moduleId',
        builder: (context, state) => ReaderScreen(moduleId: state.pathParameters['moduleId']!),
      ),
      GoRoute(path: '/videos', builder: (context, state) => const VideoLibraryScreen()),
      GoRoute(
        path: '/videos/:videoId',
        builder: (context, state) => VideoScreen(videoId: state.pathParameters['videoId']!),
      ),
      GoRoute(path: '/about', builder: (context, state) => const AboutScreen()),
    ],
  );
});
