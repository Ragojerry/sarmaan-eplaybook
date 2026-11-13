import 'package:flutter/material.dart';

import 'brand_tokens.g.dart';

/// What each colour is for. Every value comes from the one token file,
/// brand/tokens.json, via brand_tokens.g.dart. Widgets use these names, never a
/// hex value, so the palette changes in one place.
///
/// Palette of 2026-11-12: screens on the 15% teal background, cards on [surface]
/// with the thin teal [divider]; app bars and primary buttons logo teal with white
/// text; bottom navigation deep forest; the Home hero card forest to teal with pale teal
/// accents. Every text pair passes 4.5:1 (docs/brand/contrast_report.md).
class AppColors {
  AppColors._();

  static const primary = BrandColors.primary;
  static const onPrimary = BrandColors.onPrimary;

  /// Secondary text on teal, forest and deep forest.
  static const onPrimaryMuted = BrandColors.onPrimaryMuted;
  static const forest = BrandColors.forest;
  static const deepForest = BrandColors.deepForest;
  static const midBlend = BrandColors.midBlend;

  /// Accent on forest and teal (the pale teal tint): hero label, Continue button,
  /// hero progress, the Online dot.
  static const accent = BrandColors.accent;
  static const onAccent = BrandColors.onAccent;

  /// Teal text and links (the logo teal passes 4.5:1 on every light surface).
  static const primaryText = BrandColors.primaryText;
  static const sheenLight = BrandColors.sheenLight;
  static const sheenDark = BrandColors.sheenDark;
  static const highlightSurface = BrandColors.highlightSurface;
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

  static const navBar = BrandColors.navBar;
  static const navActive = BrandColors.navActive;
  static const navInactive = BrandColors.navInactive;

  /// Only behind partner logos (approved on white) and the certificate's paper preview.
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

/// The subtle sheen (decision 2026-11-12, kept in the new palette): forest-to-teal
/// gradients on headers, a soft glossy highlight on primary buttons, and softly
/// tinted shadows under cards.
class AppSheen {
  AppSheen._();

  /// Splash and Home header: Forest Green at the top to deep forest.
  static const header = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [AppColors.forest, AppColors.deepForest],
  );

  /// The Continue hero card and banners: Forest Green at the top to logo teal.
  static const hero = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [AppColors.forest, AppColors.primary],
  );

  /// For a photo at the top of the hero card (none yet): the photo fades into the
  /// card through this gradient, ending in the mid-blend.
  static final photoFade = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [AppColors.midBlend.withValues(alpha: 0), AppColors.midBlend],
  );

  /// Primary buttons and filled badges.
  static const button = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [AppColors.sheenLight, AppColors.primary, AppColors.sheenDark],
  );

  /// The glossy light along the top edge, laid over a gradient.
  static const gloss = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [Color(0x40FFFFFF), Color(0x00FFFFFF)],
    stops: [0, 0.55],
  );

  /// Soft, teal-tinted shadow under cards.
  static final card = [
    BoxShadow(color: AppColors.primary.withValues(alpha: 0.12), blurRadius: 18, offset: const Offset(0, 6)),
    BoxShadow(color: Colors.black.withValues(alpha: 0.04), blurRadius: 2, offset: const Offset(0, 1)),
  ];

  /// A stronger glow for the one element that matters most (the next module, primary buttons).
  static final glow = [
    BoxShadow(color: AppColors.primary.withValues(alpha: 0.32), blurRadius: 16, offset: const Offset(0, 6)),
  ];

  /// The hero gradient as a box decoration, for headers and banners.
  static BoxDecoration heroBox({BorderRadius? radius}) => BoxDecoration(gradient: hero, borderRadius: radius);
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
        headlineSmall: scale(BrandTypeScale.headline, AppColors.primaryText),
        // Reader section headings.
        titleMedium: scale(BrandTypeScale.titleSmall, AppColors.primaryText),
        bodyMedium: scale(BrandTypeScale.body, AppColors.text),
        bodySmall: scale(BrandTypeScale.bodySmall, AppColors.textMuted),
        // Uppercase, letter-spaced labels above screen titles.
        labelSmall: scale(BrandTypeScale.label, AppColors.textStrong),
      ),

      // Logo teal bars with white bold titles.
      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.primary,
        foregroundColor: AppColors.onPrimary,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: scale(BrandTypeScale.title, AppColors.onPrimary).copyWith(fontWeight: FontWeight.w700),
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
          textStyle: BrandTypeScale.button.copyWith(fontWeight: FontWeight.w700),
          elevation: 3,
          shadowColor: AppColors.primary.withValues(alpha: 0.5),
        ).copyWith(
          // The sheen: a gentle gradient with a glossy top edge (flat when disabled).
          backgroundBuilder: (context, states, child) => states.contains(WidgetState.disabled)
              ? child!
              : ClipRRect(
                  // Same corners as the button's shape, so the gradient never shows square edges.
                  borderRadius: BorderRadius.circular(AppRadius.standard),
                  child: DecoratedBox(
                    decoration: const BoxDecoration(gradient: AppSheen.button),
                    child: DecoratedBox(decoration: const BoxDecoration(gradient: AppSheen.gloss), child: child),
                  ),
                ),
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.primaryText,
          side: const BorderSide(color: AppColors.primary, width: 1.5),
          padding: const EdgeInsets.symmetric(vertical: 13, horizontal: 18),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppRadius.standard)),
          textStyle: BrandTypeScale.button.copyWith(fontSize: 13.5),
        ),
      ),

      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(foregroundColor: AppColors.primaryText),
      ),

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.surface,
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        labelStyle: const TextStyle(color: AppColors.textMuted),
        floatingLabelStyle: const TextStyle(color: AppColors.primaryText),
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

      // Card-coloured dialogs and sheets (Material 3 would tint them with the seed colour).
      dialogTheme: DialogThemeData(
        backgroundColor: AppColors.surface,
        surfaceTintColor: Colors.transparent,
        titleTextStyle: BrandTypeScale.title.copyWith(color: AppColors.textStrong),
        contentTextStyle: BrandTypeScale.body.copyWith(color: AppColors.text, fontSize: 14),
      ),
      bottomSheetTheme: const BottomSheetThemeData(backgroundColor: AppColors.surface, surfaceTintColor: Colors.transparent),

      snackBarTheme: SnackBarThemeData(
        backgroundColor: AppColors.deepForest,
        actionTextColor: AppColors.onPrimary,
        contentTextStyle: BrandTypeScale.body.copyWith(color: AppColors.onPrimary),
      ),

      // Deep forest bar: the active item white on a soft white pill, the others pale teal.
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: AppColors.navBar,
        surfaceTintColor: Colors.transparent,
        indicatorColor: AppColors.navActive.withValues(alpha: 0.18),
        labelTextStyle: WidgetStateProperty.resolveWith(
          (states) => TextStyle(
            fontWeight: FontWeight.w700,
            fontSize: 9.5,
            color: states.contains(WidgetState.selected) ? AppColors.navActive : AppColors.navInactive,
          ),
        ),
        iconTheme: WidgetStateProperty.resolveWith(
          (states) => IconThemeData(
            color: states.contains(WidgetState.selected) ? AppColors.navActive : AppColors.navInactive,
          ),
        ),
      ),

      dividerTheme: const DividerThemeData(color: AppColors.divider, thickness: 1),
    );
  }
}
