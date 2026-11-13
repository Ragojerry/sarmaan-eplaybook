import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:share_plus/share_plus.dart';

import '../l10n/l10n.dart';
import '../offline/content_sync_service.dart' show localDatabaseProvider;
import '../sync/analytics_recorder.dart';
import '../theme/app_theme.dart';
import '../tools/tools_service.dart';
import '../widgets/partner_logo_row.dart';
import '../widgets/support_deck.dart' show supportLauncherProvider, supportOnlineCheckProvider;

/// Shares a link through the phone's share sheet; replaced in tests.
typedef ToolSharer = Future<void> Function(String text, String subject);

final toolSharerProvider = Provider<ToolSharer>((ref) => (text, subject) async {
      await Share.share(text, subject: subject);
    });

String toolTypeLabel(BuildContext context, ToolType type) => switch (type) {
      ToolType.document => context.t('tools.typeDocument'),
      ToolType.spreadsheet => context.t('tools.typeSpreadsheet'),
      ToolType.presentation => context.t('tools.typePresentation'),
      ToolType.pdf => context.t('tools.typePdf'),
      ToolType.image => context.t('tools.typeImage'),
      ToolType.videoLink => context.t('tools.typeVideoLink'),
      ToolType.website => context.t('tools.typeWebsite'),
      ToolType.form => context.t('tools.typeForm'),
      ToolType.other => context.t('tools.typeOther'),
    };

// A different shape per type; the type is also written on every row.
IconData _icon(ToolType type) => switch (type) {
      ToolType.document => Icons.description_outlined,
      ToolType.spreadsheet => Icons.table_chart_outlined,
      ToolType.presentation => Icons.slideshow_outlined,
      ToolType.pdf => Icons.picture_as_pdf_outlined,
      ToolType.image => Icons.image_outlined,
      ToolType.videoLink => Icons.smart_display_outlined,
      ToolType.website => Icons.language_rounded,
      ToolType.form => Icons.assignment_outlined,
      ToolType.other => Icons.link_rounded,
    };

// Service names, shown as written (not translated).
const _hostNames = {
  'GOOGLE_DRIVE': 'Google Drive',
  'ONEDRIVE': 'OneDrive',
  'SHAREPOINT': 'SharePoint',
  'DROPBOX': 'Dropbox',
  'YOUTUBE': 'YouTube',
};

/// The Tools repository: links to job aids, forms, guidelines and websites for
/// this account's roles. Not training: no progress, ticks, locks, time or
/// quizzes, and always open (even before the General pre-test). Links open
/// outside the app (browser, Drive or OneDrive app); nothing is downloaded.
class ToolsScreen extends ConsumerStatefulWidget {
  const ToolsScreen({super.key});

  @override
  ConsumerState<ToolsScreen> createState() => _ToolsScreenState();
}

class _ToolsScreenState extends ConsumerState<ToolsScreen> {
  String _query = '';
  String? _category;

  bool _matches(ToolLink l) {
    if (_category != null && l.category != _category) return false;
    final q = _query.trim().toLowerCase();
    if (q.isEmpty) return true;
    return [l.title, l.description ?? '', l.category ?? ''].any((t) => t.toLowerCase().contains(q));
  }

  @override
  Widget build(BuildContext context) {
    final data = ref.watch(toolsProvider).valueOrNull ?? ToolsData.empty;
    final categories = data.categories;
    final sections = [
      for (final s in data.sections)
        if (s.links.any(_matches)) ToolSection(s.id, s.title, s.description, s.links.where(_matches).toList()),
    ];
    return Scaffold(
      appBar: BrandTopBar(
        appBar: AppBar(
          title: Text(context.t('tools.title')),
          leading: BackButton(onPressed: () => context.canPop() ? context.pop() : context.go('/home')),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(18, 16, 18, 32),
        children: [
          Text(context.t('tools.intro'), style: const TextStyle(fontSize: 12.5, height: 1.5, color: AppColors.textMuted)),
          const SizedBox(height: 12),
          TextField(
            onChanged: (v) => setState(() => _query = v),
            textInputAction: TextInputAction.search,
            decoration: InputDecoration(
              hintText: context.t('tools.search'),
              prefixIcon: const Icon(Icons.search_rounded),
              isDense: true,
            ),
          ),
          if (categories.isNotEmpty) ...[
            const SizedBox(height: 10),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  for (final c in [null, ...categories])
                    Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ChoiceChip(
                        label: Text(c ?? context.t('tools.allCategories')),
                        selected: _category == c,
                        onSelected: (_) => setState(() => _category = c),
                        materialTapTargetSize: MaterialTapTargetSize.padded,
                      ),
                    ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 8),
          if (sections.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 24),
              child: Text(data.isEmpty ? context.t('tools.empty') : context.t('tools.noMatch'),
                  style: const TextStyle(fontSize: 13, color: AppColors.textMuted)),
            ),
          for (final s in sections) ...[
            if (data.sections.length > 1)
              Semantics(
                header: true,
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(2, 14, 2, 6),
                  child: Text(s.title,
                      style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w800, color: AppColors.textStrong)),
                ),
              ),
            for (final l in s.links) ToolRow(link: l),
          ],
        ],
      ),
    );
  }
}

class ToolRow extends ConsumerWidget {
  final ToolLink link;

  const ToolRow({super.key, required this.link});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = link;
    final type = toolTypeLabel(context, l.type);
    final meta = [type, if (l.host != null && _hostNames[l.host] != null) _hostNames[l.host]!, context.t('tools.opensOnline')].join(' · ');
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Material(
        color: AppColors.surface,
        shape: RoundedRectangleBorder(
          side: const BorderSide(color: AppColors.divider),
          borderRadius: BorderRadius.circular(AppRadius.small),
        ),
        child: Row(
          children: [
            Expanded(
              child: Semantics(
                button: true,
                label: '$type: ${l.title}${l.description != null ? '. ${l.description}' : ''}. ${context.t('tools.opensOnline')}',
                excludeSemantics: true,
                child: InkWell(
                  borderRadius: BorderRadius.circular(AppRadius.small),
                  onTap: () => openTool(context, ref, l),
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(minHeight: 56),
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(12, 10, 4, 10),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Padding(
                            padding: const EdgeInsets.only(top: 2),
                            child: Icon(_icon(l.type), size: 24, color: AppColors.primaryText),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(l.title,
                                    style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w700, color: AppColors.textStrong, height: 1.3)),
                                if (l.description != null && l.description!.trim().isNotEmpty) ...[
                                  const SizedBox(height: 2),
                                  Text(l.description!, style: const TextStyle(fontSize: 12, color: AppColors.text, height: 1.4)),
                                ],
                                if (l.languages != null && l.languages!.trim().isNotEmpty)
                                  Text(context.t('tools.languages', {'languages': l.languages!.trim()}),
                                      style: const TextStyle(fontSize: 11.5, color: AppColors.textMuted, height: 1.4)),
                                const SizedBox(height: 4),
                                Row(
                                  children: [
                                    const Icon(Icons.open_in_new_rounded, size: 13, color: AppColors.textMuted),
                                    const SizedBox(width: 4),
                                    Flexible(
                                      child: Text(meta, style: const TextStyle(fontSize: 11.5, color: AppColors.textMuted)),
                                    ),
                                  ],
                                ),
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
            Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(
                  tooltip: context.t('tools.copyLink'),
                  constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
                  icon: const Icon(Icons.copy_rounded, size: 20, color: AppColors.textMuted),
                  onPressed: () => copyToolLink(context, l),
                ),
                IconButton(
                  tooltip: context.t('tools.shareLink'),
                  constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
                  icon: const Icon(Icons.share_outlined, size: 20, color: AppColors.textMuted),
                  onPressed: () => ref.read(toolSharerProvider)('${l.title}\n${l.url}', l.title),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

Future<void> copyToolLink(BuildContext context, ToolLink l) async {
  await Clipboard.setData(ClipboardData(text: l.url));
  if (!context.mounted) return;
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(content: Text(context.t('tools.linkCopied'))));
}

/// Opens [l] outside the app (browser, or the Drive/OneDrive app when installed;
/// never an in-app web view). Needs a connection; otherwise offers to copy the link.
Future<void> openTool(BuildContext context, WidgetRef ref, ToolLink l) async {
  if (!await ref.read(supportOnlineCheckProvider)()) {
    if (context.mounted) await _offerCopy(context, l, context.t('tools.needsInternet'));
    return;
  }
  final uri = l.uri;
  var opened = false;
  if (uri != null) {
    try {
      opened = await ref.read(supportLauncherProvider)(uri);
    } catch (_) {}
  }
  if (opened) {
    // Anonymous, opt-in only (analytics_recorder.dart): which link, nothing about the person.
    recordAnalyticsEvent(ref.read(localDatabaseProvider), 'TOOL_OPEN', payload: {'item_id': l.id});
  } else if (context.mounted) {
    await _offerCopy(context, l, context.t('tools.openFailed'));
  }
}

Future<void> _offerCopy(BuildContext context, ToolLink l, String message) {
  return showDialog<void>(
    context: context,
    builder: (ctx) => AlertDialog(
      content: Text(message, style: const TextStyle(fontSize: 14, height: 1.5, color: AppColors.text)),
      actions: [
        TextButton(onPressed: () => Navigator.of(ctx).pop(), child: Text(ctx.t('tools.close'))),
        FilledButton.icon(
          icon: const Icon(Icons.copy_rounded, size: 18),
          label: Text(ctx.t('tools.copyLink')),
          onPressed: () {
            Navigator.of(ctx).pop();
            copyToolLink(context, l);
          },
        ),
      ],
    ),
  );
}
