import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:url_launcher/url_launcher.dart';

import '../l10n/l10n.dart';
import '../offline/content_sync_service.dart' show localDatabaseProvider;
import '../support/support_contacts.dart';
import '../sync/analytics_recorder.dart';
import '../theme/app_theme.dart';

/// Opens [uri] in the app that handles it; false when none could. Replaced in tests.
typedef SupportLauncher = Future<bool> Function(Uri uri);

/// Whether the phone has any network; replaced in tests.
typedef SupportOnlineCheck = Future<bool> Function();

final supportLauncherProvider = Provider<SupportLauncher>(
    (ref) => (uri) => launchUrl(uri, mode: LaunchMode.externalApplication));

final supportOnlineCheckProvider = Provider<SupportOnlineCheck>((ref) => () async {
      try {
        final c = await Connectivity().checkConnectivity();
        return !c.every((r) => r == ConnectivityResult.none);
      } catch (_) {
        return true; // plugin problem: let the launch decide
      }
    });

String supportTypeLabel(BuildContext context, SupportContactType type) => switch (type) {
      SupportContactType.phone => context.t('support.typePhone'),
      SupportContactType.sms => context.t('support.typeSms'),
      SupportContactType.email => context.t('support.typeEmail'),
      SupportContactType.whatsapp => context.t('support.typeWhatsapp'),
      SupportContactType.link => context.t('support.typeLink'),
    };

// A different shape per type; the type is also written on every row, so colour never carries it.
IconData _icon(SupportContactType type) => switch (type) {
      SupportContactType.phone => Icons.call_outlined,
      SupportContactType.sms => Icons.sms_outlined,
      SupportContactType.email => Icons.mail_outline_rounded,
      SupportContactType.whatsapp => Icons.forum_outlined,
      SupportContactType.link => Icons.language_rounded,
    };

/// "Need help from a person?": one button per support contact (call, SMS,
/// email, WhatsApp, link), managed in the admin portal and cached on the phone.
/// Hidden completely when no contact is active for this account.
///
/// [collapsible]: a header that opens the list (the Ask screen's welcome);
/// otherwise the list is shown open, with a short intro (under an answer the
/// app could not find).
class SupportDeck extends ConsumerStatefulWidget {
  final bool collapsible;

  const SupportDeck({super.key, this.collapsible = false});

  @override
  ConsumerState<SupportDeck> createState() => _SupportDeckState();
}

class _SupportDeckState extends ConsumerState<SupportDeck> {
  bool _open = false;

  @override
  Widget build(BuildContext context) {
    final data = ref.watch(supportDeckProvider).valueOrNull ?? SupportDeckData.empty;
    if (data.contacts.isEmpty) return const SizedBox.shrink();
    final open = !widget.collapsible || _open;

    return Container(
      margin: const EdgeInsets.only(top: 6, bottom: 12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border.all(color: AppColors.divider),
        borderRadius: BorderRadius.circular(AppRadius.standard),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _header(open),
          if (open) ...[
            if (!widget.collapsible)
              Padding(
                padding: const EdgeInsets.fromLTRB(14, 0, 14, 6),
                child: Text(context.t('support.intro'), style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
              ),
            for (final c in data.contacts) _ContactRow(contact: c),
            if (data.note != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(14, 4, 14, 0),
                child: Text(data.note!, style: const TextStyle(fontSize: 11.5, height: 1.45, color: AppColors.textMuted)),
              ),
            const SizedBox(height: 10),
          ],
        ],
      ),
    );
  }

  Widget _header(bool open) {
    final title = Row(
      children: [
        const Icon(Icons.support_agent_rounded, size: 20, color: AppColors.primaryText),
        const SizedBox(width: 8),
        Expanded(
          child: Text(context.t('support.heading'),
              style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w700, color: AppColors.textStrong)),
        ),
        if (widget.collapsible)
          Icon(open ? Icons.expand_less_rounded : Icons.expand_more_rounded, color: AppColors.textMuted),
      ],
    );
    final padded = ConstrainedBox(
      constraints: const BoxConstraints(minHeight: 48),
      child: Padding(padding: const EdgeInsets.fromLTRB(14, 10, 12, 8), child: title),
    );
    if (!widget.collapsible) return Semantics(header: true, child: padded);
    return Semantics(
      button: true,
      expanded: open,
      hint: open ? context.t('support.hideContacts') : context.t('support.showContacts'),
      child: InkWell(
        borderRadius: BorderRadius.circular(AppRadius.standard),
        onTap: () => setState(() => _open = !_open),
        child: padded,
      ),
    );
  }
}

class _ContactRow extends ConsumerWidget {
  final SupportContact contact;

  const _ContactRow({required this.contact});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final c = contact;
    final type = supportTypeLabel(context, c.type);
    final details = [
      if (c.availability != null && c.availability!.trim().isNotEmpty) c.availability!.trim(),
      if (c.languages != null && c.languages!.trim().isNotEmpty) context.t('support.languages', {'languages': c.languages!.trim()}),
    ];
    return Padding(
      padding: const EdgeInsets.fromLTRB(10, 0, 10, 6),
      child: Material(
        color: AppColors.surfaceSelected,
        borderRadius: BorderRadius.circular(AppRadius.small),
        child: Row(
          children: [
            Expanded(
              child: Semantics(
                button: true,
                label: '$type: ${c.label}, ${c.value}${details.isEmpty ? '' : ', ${details.join(', ')}'}',
                excludeSemantics: true,
                child: InkWell(
                  borderRadius: BorderRadius.circular(AppRadius.small),
                  onTap: () => contactSupport(context, ref, c),
                  onLongPress: () => copySupportValue(context, c),
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(minHeight: 52),
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(10, 8, 4, 8),
                      child: Row(
                        children: [
                          Icon(_icon(c.type), size: 22, color: AppColors.primaryText),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(c.label,
                                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.textStrong, height: 1.3)),
                                const SizedBox(height: 2),
                                Text('$type · ${c.value}', style: const TextStyle(fontSize: 12, color: AppColors.text, height: 1.35)),
                                for (final d in details)
                                  Text(d, style: const TextStyle(fontSize: 11.5, color: AppColors.textMuted, height: 1.35)),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
            IconButton(
              tooltip: context.t('support.copy'),
              constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
              icon: const Icon(Icons.copy_rounded, size: 20, color: AppColors.textMuted),
              onPressed: () => copySupportValue(context, c),
            ),
          ],
        ),
      ),
    );
  }
}

/// Copies the number or address and says so.
Future<void> copySupportValue(BuildContext context, SupportContact c) async {
  await Clipboard.setData(ClipboardData(text: c.value));
  if (!context.mounted) return;
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(content: Text(context.t('support.copied', {'value': c.value}))));
}

/// Opens the dialer, messaging app, mail app, WhatsApp chat or browser for [c].
/// Email, WhatsApp and links first check for a connection. When nothing can
/// open it, the learner is offered to copy the details instead.
Future<void> contactSupport(BuildContext context, WidgetRef ref, SupportContact c) async {
  // Anonymous, opt-in only (analytics_recorder.dart): the contact type, nothing else.
  recordAnalyticsEvent(ref.read(localDatabaseProvider), 'SUPPORT_CONTACT_TAP', payload: {'contact_type': c.type.name.toUpperCase()});
  final type = supportTypeLabel(context, c.type);

  if (needsInternet(c.type) && !await ref.read(supportOnlineCheckProvider)()) {
    if (context.mounted) await _offerCopy(context, c, context.t('support.needsInternet', {'type': type}));
    return;
  }
  String? versionLine;
  if (c.includeAppVersion) {
    try {
      final version = (await PackageInfo.fromPlatform()).version;
      if (context.mounted) versionLine = context.t('support.appVersion', {'version': version});
    } catch (_) {}
  }
  final uri = supportUri(c, appVersionLine: versionLine);
  var opened = false;
  if (uri != null) {
    try {
      opened = await ref.read(supportLauncherProvider)(uri);
    } catch (_) {}
  }
  if (!opened && context.mounted) await _offerCopy(context, c, context.t('support.openFailed', {'type': type}));
}

Future<void> _offerCopy(BuildContext context, SupportContact c, String message) {
  return showDialog<void>(
    context: context,
    builder: (ctx) => AlertDialog(
      content: Text(message, style: const TextStyle(fontSize: 14, height: 1.5, color: AppColors.text)),
      actions: [
        TextButton(onPressed: () => Navigator.of(ctx).pop(), child: Text(ctx.t('support.close'))),
        FilledButton.icon(
          icon: const Icon(Icons.copy_rounded, size: 18),
          label: Text(ctx.t('support.copyDetails')),
          onPressed: () {
            Navigator.of(ctx).pop();
            copySupportValue(context, c);
          },
        ),
      ],
    ),
  );
}
