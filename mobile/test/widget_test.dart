import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:sarmaan_eplaybook/main.dart';

void main() {
  testWidgets('App boots and shows the splash screen first', (WidgetTester tester) async {
    // SplashScreen's post-frame callback reads the local database (Phase 8)
    // via SettingsService, which needs path_provider/sqlite platform
    // channels this test environment doesn't have. That's fine — the
    // callback's try/catch (see splash_screen.dart's _decideRoute) is
    // specifically written to survive that failure and fall back to
    // /login rather than throwing, so no mock is required here.
    await tester.pumpWidget(const ProviderScope(child: SarmaanEPlaybookApp()));

    // Splash screen shows a pill-shaped loading bar (matching the
    // prototype's .splash .bar), not a circular spinner.
    expect(find.byType(LinearProgressIndicator), findsOneWidget);
  });
}
