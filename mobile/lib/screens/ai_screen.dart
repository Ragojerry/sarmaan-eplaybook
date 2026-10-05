import 'package:flutter/material.dart';

import '../widgets/app_bottom_nav.dart';

/// Phase 2 stub. AI/RAG is confirmed in MVP scope (docs/architecture.md §6).
/// Real chat (later AI phase) is backed by real retrieval — server RAG
/// online, on-device vector index + quantized LLM offline (master prompt
/// §25-§38) — never the prototype's 10-entry keyword substring match
/// (docs/prototype-analysis.md §6).
class AiScreen extends StatefulWidget {
  const AiScreen({super.key});

  @override
  State<AiScreen> createState() => _AiScreenState();
}

class _AiScreenState extends State<AiScreen> {
  final _controller = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Ask')),
      body: Column(
        children: [
          const Expanded(
            child: Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Text(
                  'Real RAG-backed Q&A implemented in the AI phase, once scope '
                  'and technology are confirmed. Chat/message log persistence '
                  'in ai_question_log, not just in-memory (unlike the prototype).',
                  textAlign: TextAlign.center,
                ),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(
                      hintText: 'Ask a question about AZM administration…',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(onPressed: () {}, icon: const Icon(Icons.send)),
              ],
            ),
          ),
        ],
      ),
      bottomNavigationBar: const AppBottomNav(currentRoute: '/ai'),
    );
  }
}
