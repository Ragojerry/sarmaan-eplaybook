import 'package:flutter/material.dart';

import 'brand_tokens.g.dart';

/// What each colour is for. Every value comes from the one token file,
/// brand/tokens.json (IHS Towers Brand Manual 2021), via brand_tokens.g.dart.
/// Widgets use these names, never a hex value.
///
/// Red, Orange, Blue and Teal are below 4.5:1 as text on white, so they are only
/// fills, icons and borders; the text beside them uses the matching *Text colour
/// (docs/brand/contrast_report.md).
class AppColors {
  AppColors._();

  static const primary = BrandColors.primary;
  static const onPrimary = BrandColors.onPrimary;
  static const background = BrandColors.background;
  static const surface = BrandColors.surface;
  static const surfaceMuted = BrandColors.surfaceMuted;
  static const surfaceSelected = BrandColors.surfaceSelected;
  static const divider = BrandColors.divider;
  static const controlBorder = BrandColors.controlBorder;

  static const text = BrandColors.text;
  static const textStrong = BrandColors.textStrong;
  static const textMuted = BrandColors.textMuted;
  static const textDisabled = BrandColors.textDisabled;

  static const success = BrandColors.success;
  static const successText = BrandColors.successText;
  static const successSurface = BrandColors.successSurface;
  static const warning = BrandColors.warning;
  static const warningText = BrandColors.warningText;
  static const warningSurface = BrandColors.warningSurface;
  static const error = BrandColors.error;
  static const errorText = BrandColors.errorText;
  static const errorSurface = BrandColors.errorSurface;
  static const info = BrandColors.info;
  static const infoText = BrandColors.infoText;
  static const infoSurface = BrandColors.infoSurface;

  static const progressTrack = BrandColors.progressTrack;
  static const progressFill = BrandColors.progressFill;
  static const white = BrandPalette.white;
}

/// Radii from brand/tokens.json.
class AppRadius {
  AppRadius._();

  static const large = BrandRadius.large;
  static const medium = BrandRadius.medium;
  static const standard = BrandRadius.standard;
  static const small = BrandRadius.small;
  static const pill = BrandRadius.pill;
}

/// The app's own bundled fonts (assets/fonts, SIL OFL 1.1), kept by decision on
/// 2026-11-11 instead of the guide's Helvetica Neue: Fraunces for headings, Manrope
/// for body and UI, JetBrains Mono for labels. They lack the Hausa letters
/// (ɓ ɗ ƙ ƴ); Flutter draws those from [fallback] (Roboto / Noto Sans on Android).
class AppFonts {
  AppFonts._();

  static const serif = BrandFont.heading;
  static const sans = BrandFont.body;
  static const mono = BrandFont.mono;
  static const fallback = BrandFont.fallback;
}

class AppTheme {
  AppTheme._();

  static ThemeData light() {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: AppColors.primary,
      brightness: Brightness.light,
      primary: AppColors.primary,
      onPrimary: AppColors.onPrimary,
      secondary: AppColors.primary,
      onSecondary: AppColors.onPrimary,
      surface: AppColors.surface,
      onSurface: AppColors.text,
      error: AppColors.error,
      onError: AppColors.textStrong,
      outline: AppColors.controlBorder,
      outlineVariant: AppColors.divider,
    );

    TextStyle scale(TextStyle s, Color color) => s.copyWith(color: color);

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: AppColors.background,
      fontFamily: AppFonts.sans,
      fontFamilyFallback: AppFonts.fallback,

      textTheme: TextTheme(
        // Screen titles ("Choose your language", "Sign in", ...).
        headlineSmall: scale(BrandTypeScale.headline, AppColors.textStrong),
        // Reader section headings.
        titleMedium: scale(BrandTypeScale.titleSmall, AppColors.textStrong),
        bodyMedium: scale(BrandTypeScale.body, AppColors.text),
        bodySmall: scale(BrandTypeScale.bodySmall, AppColors.textMuted),
        // Uppercase, letter-spaced labels above screen titles.
        labelSmall: scale(BrandTypeScale.label, AppColors.textStrong),
      ),

      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.background,
        foregroundColor: AppColors.textStrong,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: scale(BrandTypeScale.title, AppColors.textStrong),
      ),

      cardTheme: CardThemeData(
        color: AppColors.surface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.standard),
          side: const BorderSide(color: AppColors.divider, width: 1),
        ),
        margin: EdgeInsets.zero,
      ),

      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.primary,
          foregroundColor: AppColors.onPrimary,
          disabledBackgroundColor: AppColors.surfaceMuted,
          disabledForegroundColor: AppColors.textMuted,
          padding: const EdgeInsets.symmetric(vertical: 15, horizontal: 20),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppRadius.standard)),
          textStyle: BrandTypeScale.button,
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.primary,
          side: const BorderSide(color: AppColors.controlBorder, width: 1.5),
          padding: const EdgeInsets.symmetric(vertical: 13, horizontal: 18),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppRadius.standard)),
          textStyle: BrandTypeScale.button.copyWith(fontSize: 13.5),
        ),
      ),

      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(foregroundColor: AppColors.primary),
      ),

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.surface,
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        labelStyle: const TextStyle(color: AppColors.textMuted),
        floatingLabelStyle: const TextStyle(color: AppColors.textStrong),
        hintStyle: const TextStyle(color: AppColors.textMuted),
        // Red borders mark the field; the message itself is Forest Green (Red fails as text).
        errorStyle: const TextStyle(color: AppColors.errorText, fontWeight: FontWeight.w600),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.standard),
          borderSide: const BorderSide(color: AppColors.controlBorder, width: 1),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.standard),
          borderSide: const BorderSide(color: AppColors.controlBorder, width: 1),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.standard),
          borderSide: const BorderSide(color: AppColors.primary, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.standard),
          borderSide: const BorderSide(color: AppColors.error, width: 1.5),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.standard),
          borderSide: const BorderSide(color: AppColors.error, width: 2),
        ),
      ),

      radioTheme: RadioThemeData(
        fillColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected) ? AppColors.primary : AppColors.controlBorder,
        ),
      ),

      checkboxTheme: CheckboxThemeData(
        fillColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected) ? AppColors.primary : Colors.transparent,
        ),
        checkColor: const WidgetStatePropertyAll(AppColors.onPrimary),
        side: const BorderSide(color: AppColors.controlBorder, width: 1.5),
      ),

      progressIndicatorTheme: const ProgressIndicatorThemeData(
        color: AppColors.progressFill,
        linearTrackColor: AppColors.progressTrack,
      ),

      // White dialogs and sheets (Material 3 would tint them with the seed colour).
      dialogTheme: DialogThemeData(
        backgroundColor: AppColors.surface,
        surfaceTintColor: Colors.transparent,
        titleTextStyle: BrandTypeScale.title.copyWith(color: AppColors.textStrong),
        contentTextStyle: BrandTypeScale.body.copyWith(color: AppColors.text, fontSize: 14),
      ),
      bottomSheetTheme: const BottomSheetThemeData(backgroundColor: AppColors.surface, surfaceTintColor: Colors.transparent),

      snackBarTheme: SnackBarThemeData(
        backgroundColor: AppColors.primary,
        contentTextStyle: BrandTypeScale.body.copyWith(color: AppColors.onPrimary),
      ),

      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: AppColors.surface,
        surfaceTintColor: Colors.transparent,
        indicatorColor: AppColors.surfaceSelected,
        labelTextStyle: WidgetStateProperty.resolveWith(
          (states) => TextStyle(
            fontWeight: FontWeight.w700,
            fontSize: 9.5,
            color: states.contains(WidgetState.selected) ? AppColors.textStrong : AppColors.textMuted,
          ),
        ),
        iconTheme: WidgetStateProperty.resolveWith(
          (states) => IconThemeData(
            color: states.contains(WidgetState.selected) ? AppColors.primary : AppColors.textMuted,
          ),
        ),
      ),

      dividerTheme: const DividerThemeData(color: AppColors.divider, thickness: 1),
    );
  }
}
