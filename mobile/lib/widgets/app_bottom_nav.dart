import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// Phase 7 scope: Home/Modules/Videos/About. The prototype's 5th tab
/// ("Ask", the AI assistant) is deliberately omitted here — that screen
/// isn't wired until the RAG/offline-AI phases (Phase 10/11) actually give
/// it something real to call. Showing an "Ask" tab now would mean either a
/// broken destination or a fresh fake stub — the exact prototype problem
/// this project exists to fix (docs/prototype-analysis.md §1, §6).
class AppBottomNav extends StatelessWidget {
  final String currentRoute;

  const AppBottomNav({super.key, required this.currentRoute});

  static const _items = [
    ('/home', Icons.home_outlined, 'Home'),
    ('/modules', Icons.menu_book_outlined, 'Modules'),
    ('/videos', Icons.play_circle_outline, 'Videos'),
    ('/about', Icons.info_outline, 'About'),
  ];

  @override
  Widget build(BuildContext context) {
    final index = _items.indexWhere((i) => i.$1 == currentRoute).clamp(0, _items.length - 1);
    return NavigationBar(
      selectedIndex: index,
      onDestinationSelected: (i) => context.go(_items[i].$1),
      destinations: [
        for (final item in _items) NavigationDestination(icon: Icon(item.$2), label: item.$3),
      ],
    );
  }
}
