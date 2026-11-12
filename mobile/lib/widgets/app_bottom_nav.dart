import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../l10n/l10n.dart';

/// Phase 7 scope: Home/Modules/Videos/About. The prototype's 5th tab
/// ("Ask", the AI assistant) is deliberately omitted here — that screen
/// isn't wired until the RAG/offline-AI phases (Phase 10/11) actually give
/// it something real to call. Showing an "Ask" tab now would mean either a
/// broken destination or a fresh fake stub — the exact prototype problem
/// this project exists to fix (docs/prototype-analysis.md §1, §6).
class AppBottomNav extends StatelessWidget {
  final String currentRoute;

  const AppBottomNav({super.key, required this.currentRoute});

  @override
  Widget build(BuildContext context) {
    final items = [
      ('/home', Icons.home_outlined, context.t('nav.home')),
      ('/modules', Icons.menu_book_outlined, context.t('nav.modules')),
      ('/videos', Icons.play_circle_outline, context.t('nav.videos')),
      ('/ai', Icons.chat_bubble_outline, context.t('nav.ask')),
      ('/about', Icons.info_outline, context.t('nav.about')),
    ];
    final index = items.indexWhere((i) => i.$1 == currentRoute).clamp(0, items.length - 1);
    return NavigationBar(
      selectedIndex: index,
      onDestinationSelected: (i) => context.go(items[i].$1),
      destinations: [
        // Long translations shrink to fit the tab instead of being cut off.
        for (final item in items) NavigationDestination(icon: Icon(item.$2), label: item.$3),
      ],
    );
  }
}
