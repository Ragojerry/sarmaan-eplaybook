import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import '../theme/brand_identity.g.dart';

/// The app logo (brand/brand.json -> theme/brand_identity.g.dart): the supplied file,
/// unmodified, on its own white card, never larger than the file's own pixels (the
/// current file is only 118 x 50 px; a larger file grows up to [height]).
/// [onCard] false drops the white card where the logo already sits on white.
class BrandLogo extends StatelessWidget {
  const BrandLogo({super.key, this.height = 56, this.onCard = true});

  final double height;
  final bool onCard;

  @override
  Widget build(BuildContext context) {
    const wPx = BrandIdentity.logoWidthPx * 1.0;
    const hPx = BrandIdentity.logoHeightPx * 1.0;
    final h = math.min(height, hPx / MediaQuery.devicePixelRatioOf(context));
    final image = Image.asset(
      BrandIdentity.logoAsset,
      width: h * wPx / hPx,
      height: h,
      fit: BoxFit.contain,
      filterQuality: FilterQuality.medium,
      semanticLabel: BrandIdentity.logoLabel,
    );
    if (!onCard) return image;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(color: AppColors.white, borderRadius: BorderRadius.circular(AppRadius.small)),
      child: image,
    );
  }
}

/// The app title, as one heading that wraps onto as many lines as a small phone needs
/// (never cut off). The title is the product name: not translated.
class BrandTitle extends StatelessWidget {
  const BrandTitle({super.key, this.style, this.textAlign});

  final TextStyle? style;
  final TextAlign? textAlign;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      header: true,
      child: Text(
        BrandIdentity.title,
        style: style ?? Theme.of(context).textTheme.headlineSmall,
        textAlign: textAlign,
        softWrap: true,
      ),
    );
  }
}
