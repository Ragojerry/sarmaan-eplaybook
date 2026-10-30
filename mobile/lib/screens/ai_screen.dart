import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../qa/qa_engine.dart';
import '../qa/question_answer_service.dart';
import '../theme/app_theme.dart';
import '../widgets/app_bottom_nav.dart';

class _Message {
  final String? question; // set for the user's turn
  final AnswerResult? answer; // set for the app's turn

  const _Message.user(String this.question) : answer = null;
  const _Message.app(AnswerResult this.answer) : question = null;
}

/// Offline question answering (revised Phases 10/11). Answers are copied
/// verbatim from the downloaded training materials and always carry a source;
/// if the materials don't support an answer the app says so rather than
/// guessing. Works with no connection once content has been downloaded.
class AiScreen extends ConsumerStatefulWidget {
  const AiScreen({super.key});

  @override
  ConsumerState<AiScreen> createState() => _AiScreenState();
}

class _AiScreenState extends ConsumerState<AiScreen> {
  final _controller = TextEditingController();
  final _scroll = ScrollController();
  final List<_Message> _messages = [];
  bool _asking = false;

  @override
  void dispose() {
    _controller.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _ask(String text) async {
    final q = text.trim();
    if (q.length < 2 || _asking) return;
    _controller.clear();
    setState(() {
      _messages.add(_Message.user(q));
      _asking = true;
    });
    _scrollToEnd();
    try {
      final result = await ref.read(questionAnswerServiceProvider).ask(q);
      if (!mounted) return;
      setState(() => _messages.add(_Message.app(result)));
    } finally {
      if (mounted) setState(() => _asking = false);
      _scrollToEnd();
    }
  }

  void _scrollToEnd() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent, duration: const Duration(milliseconds: 200), curve: Curves.easeOut);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Ask')),
      body: Column(
        children: [
          Expanded(
            child: _messages.isEmpty
                ? _buildWelcome()
                : ListView(
                    controller: _scroll,
                    padding: const EdgeInsets.fromLTRB(22, 16, 22, 8),
                    children: [
                      for (final m in _messages) m.question != null ? _UserBubble(text: m.question!) : _AnswerCard(result: m.answer!, onAsk: _ask),
                      if (_asking) const Padding(padding: EdgeInsets.all(12), child: Center(child: CircularProgressIndicator(strokeWidth: 2))),
                    ],
                  ),
          ),
          _buildInputBar(),
        ],
      ),
      bottomNavigationBar: const AppBottomNav(currentRoute: '/ai'),
    );
  }

  Widget _buildWelcome() {
    return ListView(
      padding: const EdgeInsets.fromLTRB(22, 22, 22, 8),
      children: [
        Text('ASK THE TRAINING MATERIALS', style: Theme.of(context).textTheme.labelSmall),
        const SizedBox(height: 8),
        Text('Ask a question', style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 6),
        const Text(
          'Answers come only from the training content downloaded on this phone — so this works without internet. '
          'Every answer shows where it came from.',
          style: TextStyle(fontSize: 12, height: 1.55, color: AppColors.textSecondary),
        ),
        const SizedBox(height: 18),
        for (final s in kSuggestions) _SuggestionChip(text: s, onTap: () => _ask(s)),
      ],
    );
  }

  Widget _buildInputBar() {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 10),
      decoration: const BoxDecoration(color: AppColors.sand, border: Border(top: BorderSide(color: AppColors.line))),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _controller,
              textInputAction: TextInputAction.send,
              onSubmitted: _ask,
              decoration: const InputDecoration(hintText: 'e.g. What if a child vomits after the medicine?', isDense: true),
              style: const TextStyle(fontSize: 13),
            ),
          ),
          const SizedBox(width: 8),
          IconButton.filled(
            onPressed: _asking ? null : () => _ask(_controller.text),
            style: IconButton.styleFrom(backgroundColor: AppColors.tealDeep),
            icon: const Icon(Icons.arrow_upward_rounded, color: Colors.white),
          ),
        ],
      ),
    );
  }
}

class _SuggestionChip extends StatelessWidget {
  final String text;
  final VoidCallback onTap;

  const _SuggestionChip({required this.text, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 9),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: AppColors.white,
          border: Border.all(color: AppColors.line),
          borderRadius: BorderRadius.circular(AppRadius.standard),
        ),
        child: Row(
          children: [
            Expanded(child: Text(text, style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600, color: AppColors.ink))),
            const Icon(Icons.north_east_rounded, size: 15, color: AppColors.textMuted),
          ],
        ),
      ),
    );
  }
}

class _UserBubble extends StatelessWidget {
  final String text;

  const _UserBubble({required this.text});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerRight,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12, left: 48),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(color: AppColors.tealDeep, borderRadius: BorderRadius.circular(AppRadius.standard)),
        child: Text(text, style: const TextStyle(fontSize: 12.8, color: AppColors.sand, height: 1.45)),
      ),
    );
  }
}

String _sentenceCase(String s) => s.isEmpty ? s : s[0].toUpperCase() + s.substring(1);

class _AnswerCard extends StatelessWidget {
  final AnswerResult result;
  final void Function(String) onAsk;

  const _AnswerCard({required this.result, required this.onAsk});

  @override
  Widget build(BuildContext context) {
    final matched = result.matched;
    return Container(
      margin: const EdgeInsets.only(bottom: 16, right: 24),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: matched ? AppColors.white : AppColors.claySoft,
        borderRadius: BorderRadius.circular(AppRadius.standard),
        border: matched ? Border.all(color: AppColors.line) : const Border(left: BorderSide(color: AppColors.clay, width: 3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            matched ? _sentenceCase(result.answer) : result.answer,
            style: TextStyle(fontSize: 13, height: 1.55, color: matched ? AppColors.ink : AppColors.calloutWarningText, fontWeight: matched ? FontWeight.w600 : FontWeight.w500),
          ),
          if (matched) ...[
            const SizedBox(height: 10),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                _Pill(text: 'Match ${(result.confidence * 100).round()}%', color: AppColors.tealSoft, textColor: AppColors.tealDeep),
                if (result.offline) const _Pill(text: 'ANSWERED OFFLINE', color: AppColors.sandDeep, textColor: AppColors.textSecondary),
              ],
            ),
            const SizedBox(height: 12),
            const Text('SOURCE', style: TextStyle(fontFamily: AppFonts.mono, fontSize: 9.5, fontWeight: FontWeight.w700, letterSpacing: 0.6, color: AppColors.textMuted)),
            const SizedBox(height: 4),
            for (final s in result.sources)
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text(
                  '${s.moduleCode} · ${s.moduleTitle}${s.sectionTitle != null ? ' — ${s.sectionTitle}' : ''}',
                  style: const TextStyle(fontSize: 11, color: AppColors.textSecondary, height: 1.4),
                ),
              ),
            const SizedBox(height: 6),
            const Text(
              'Copied from the training materials. For doses, always follow your job aid and the DIGIT HCM app.',
              style: TextStyle(fontSize: 10.5, color: AppColors.textMuted, fontStyle: FontStyle.italic, height: 1.4),
            ),
          ] else if (result.suggestions.isNotEmpty) ...[
            const SizedBox(height: 12),
            const Text('Try asking about:', style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w700, color: AppColors.calloutWarningText)),
            const SizedBox(height: 6),
            for (final s in result.suggestions) _SuggestionChip(text: s, onTap: () => onAsk(s)),
          ],
        ],
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  final String text;
  final Color color;
  final Color textColor;

  const _Pill({required this.text, required this.color, required this.textColor});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(6)),
      child: Text(text, style: TextStyle(fontFamily: AppFonts.mono, fontSize: 9.5, fontWeight: FontWeight.w700, color: textColor)),
    );
  }
}
