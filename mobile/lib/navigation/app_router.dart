import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

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

/// Splash, language, consent, login, home, modules, reader, videos, Ask (AI),
/// about, and (Phase 12) the sync & updates screen.
final appRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/splash',
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
      GoRoute(
        path: '/quiz/:moduleId',
        builder: (context, state) => QuizScreen(moduleId: state.pathParameters['moduleId']!),
      ),
      GoRoute(path: '/videos', builder: (context, state) => const VideoLibraryScreen()),
      GoRoute(
        path: '/videos/:videoId',
        builder: (context, state) => VideoScreen(videoId: state.pathParameters['videoId']!),
      ),
      GoRoute(path: '/ai', builder: (context, state) => const AiScreen()),
      GoRoute(path: '/about', builder: (context, state) => const AboutScreen()),
      GoRoute(path: '/updates', builder: (context, state) => const UpdatesScreen()),
    ],
  );
});
