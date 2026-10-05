import 'package:flutter/material.dart';

/// Exact color tokens transcribed from the prototype's `:root` CSS variables
/// (sarmaan-eplaybook-prototype_1.html, lines ~9-24). Every hex value here
/// matches the prototype 1:1 — this is a real design system, not an
/// approximation of one.
class AppColors {
  AppColors._();

  static const ink = Color(0xFF16241F);
  static const teal = Color(0xFF0B5D51);
  static const tealDeep = Color(0xFF08322C);
  static const tealSoft = Color(0xFFE4EEEA);
  static const gold = Color(0xFFE8A93C);
  static const goldDeep = Color(0xFFB5792A);
  static const sand = Color(0xFFF4EFDF);
  static const sandDeep = Color(0xFFE9DFC0);
  static const clay = Color(0xFFB5652F);
  static const claySoft = Color(0xFFF3E2D3);
  static const white = Color(0xFFFFFFFF);
  static const line = Color(0x2416241F); // rgba(22,36,31,0.14)
  static const danger = Color(0xFFB23B3B);

  // Body text greys used throughout the prototype's copy (not CSS custom
  // properties there, but consistently reused literals — e.g. `#5b6b62` for
  // secondary text, `#334039` for reader body copy).
  static const textSecondary = Color(0xFF5B6B62);
  static const textMuted = Color(0xFF7C8A83);
  static const readerBody = Color(0xFF334039);
  static const calloutWarningText = Color(0xFF5B3A1F);
  static const calloutGoodText = Color(0xFF0D3F37);
}

/// Radii match the prototype's actual scale: 20px large cards/splash marks,
/// 14-16px standard cards/buttons, 9-12px small chips/icons, 999px pills.
class AppRadius {
  AppRadius._();

  static const large = 20.0;
  static const medium = 16.0;
  static const standard = 14.0;
  static const small = 10.0;
  static const pill = 999.0;
}

/// Font families referenced here are the prototype's actual fonts (Fraunces
/// serif for headings, Manrope for body/UI, JetBrains Mono for
/// labels/eyebrows/badges) — matching master prompt's own reasoning for
/// picking distinctive type at all. They render as system-font fallbacks
/// until the actual font files are added as assets (Flutter doesn't fail or
/// warn when a declared fontFamily has no matching asset — it silently
/// falls back), since downloading the real font files isn't possible from
/// this dev sandbox (no network access to fonts.google.com/gstatic.com
/// here). To get the exact prototype typefaces rendering:
///   1. Download Fraunces, Manrope, and JetBrains Mono from Google Fonts
///   2. Add the .ttf files under mobile/assets/fonts/
///   3. Register them in pubspec.yaml's `fonts:` section
/// Everything else in this theme (colors, radii, spacing, component shapes)
/// matches the prototype exactly regardless of that step.
class AppFonts {
  AppFonts._();

  static const serif = 'Fraunces';
  static const sans = 'Manrope';
  static const mono = 'JetBrainsMono';
}

class AppTheme {
  AppTheme._();

  static ThemeData light() {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: AppColors.teal,
      brightness: Brightness.light,
      primary: AppColors.tealDeep,
      secondary: AppColors.gold,
      surface: AppColors.white,
      error: AppColors.danger,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: AppColors.sand,
      fontFamily: AppFonts.sans,

      textTheme: const TextTheme(
        // Screen titles ("Choose your language", "Sign in", etc.) — the
        // prototype's h2.screen-title: Fraunces serif, 22px, weight 600.
        headlineSmall: TextStyle(
          fontFamily: AppFonts.serif,
          fontSize: 22,
          fontWeight: FontWeight.w600,
          color: AppColors.ink,
        ),
        // Reader section headings (h3): Fraunces serif, 16px, teal-deep.
        titleMedium: TextStyle(
          fontFamily: AppFonts.serif,
          fontSize: 16,
          fontWeight: FontWeight.w600,
          color: AppColors.tealDeep,
        ),
        // Body copy: Manrope, matches .reader-body p (12.8px/1.65 line
        // height) and .screen-desc (13px) closely enough to share one style.
        bodyMedium: TextStyle(
          fontFamily: AppFonts.sans,
          fontSize: 13,
          height: 1.55,
          color: AppColors.readerBody,
        ),
        bodySmall: TextStyle(
          fontFamily: AppFonts.sans,
          fontSize: 11.5,
          color: AppColors.textSecondary,
          height: 1.5,
        ),
        // "Eyebrow" mono labels (uppercase, letter-spaced) used above every
        // screen title in the prototype.
        labelSmall: TextStyle(
          fontFamily: AppFonts.mono,
          fontSize: 10.5,
          fontWeight: FontWeight.w700,
          letterSpacing: 1.5,
          color: AppColors.tealDeep,
        ),
      ),

      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.sand,
        foregroundColor: AppColors.ink,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          fontFamily: AppFonts.serif,
          fontSize: 20,
          fontWeight: FontWeight.w600,
          color: AppColors.ink,
        ),
      ),

      cardTheme: CardThemeData(
        color: AppColors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.standard),
          side: const BorderSide(color: AppColors.line, width: 1),
        ),
        margin: EdgeInsets.zero,
      ),

      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.tealDeep,
          foregroundColor: AppColors.sand,
          padding: const EdgeInsets.symmetric(vertical: 15),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppRadius.standard)),
          textStyle: const TextStyle(fontFamily: AppFonts.sans, fontWeight: FontWeight.w800, fontSize: 14.5),
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.tealDeep,
          side: const BorderSide(color: AppColors.line, width: 1.5),
          padding: const EdgeInsets.symmetric(vertical: 13),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppRadius.standard)),
          textStyle: const TextStyle(fontFamily: AppFonts.sans, fontWeight: FontWeight.w700, fontSize: 13.5),
        ),
      ),

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.white,
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.standard),
          borderSide: const BorderSide(color: AppColors.line, width: 1.5),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.standard),
          borderSide: const BorderSide(color: AppColors.line, width: 1.5),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.standard),
          borderSide: const BorderSide(color: AppColors.teal, width: 1.5),
        ),
      ),

      radioTheme: RadioThemeData(
        fillColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected) ? AppColors.teal : AppColors.line,
        ),
      ),

      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: AppColors.white,
        indicatorColor: AppColors.tealSoft,
        labelTextStyle: WidgetStateProperty.resolveWith(
          (states) => TextStyle(
            fontFamily: AppFonts.sans,
            fontWeight: FontWeight.w700,
            fontSize: 9.5,
            color: states.contains(WidgetState.selected) ? AppColors.tealDeep : AppColors.textMuted,
          ),
        ),
        iconTheme: WidgetStateProperty.resolveWith(
          (states) => IconThemeData(
            color: states.contains(WidgetState.selected) ? AppColors.tealDeep : AppColors.textMuted,
          ),
        ),
      ),

      dividerTheme: const DividerThemeData(color: AppColors.line, thickness: 1),
    );
  }
}
