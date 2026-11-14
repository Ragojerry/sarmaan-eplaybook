import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:sarmaan_eplaybook/models/api_models.dart';
import 'package:sarmaan_eplaybook/services/narration_builder.dart';

/// "Read aloud" narration from the real HFW and CDD module content
/// (content/*/content_sections.json, what the content import loads).
///
/// test/narration_vectors.json keeps the builder's output for three real modules,
/// for a future server builder to match. Regenerate after a deliberate change:
///   UPDATE_NARRATION_VECTORS=1 flutter test test/narration_builder_test.dart

class _Module {
  final String code, title;
  final String? description;
  final List<ContentSection> sections;
  _Module(this.code, this.title, this.description, this.sections);
}

List<_Module> _load(String path) {
  final data = jsonDecode(File(path).readAsStringSync()) as List;
  return [
    for (final m in data.cast<Map<String, dynamic>>())
      _Module(
        m['module_code'] as String,
        m['title'] as String,
        m['description'] as String?,
        [
          for (final (i, s) in (m['sections'] as List).cast<Map<String, dynamic>>().indexed)
            ContentSection(
              id: (s['id'] ?? '${m['module_code']}-$i').toString(),
              moduleId: m['module_code'] as String,
              sectionNumber: (s['section_number'] as num?)?.toInt() ?? i,
              title: s['title'] as String?,
              contentType: s['content_type'] as String,
              content: Map<String, dynamic>.from(s['content'] as Map? ?? const {}),
              sortOrder: i,
            ),
        ],
      ),
  ];
}

final _hfw = _load('../content/hfw_flipbook/content_sections.json');
final _cdd = _load('../content/cdd_flipbook/content_sections.json');
final _all = [..._hfw, ..._cdd];
const _builder = LocalNarrationBuilder();

List<NarrationChunk> _narrate(_Module m, {int maxLength = kDefaultMaxSpeechInput}) =>
    _builder.build(title: m.title, description: m.description, sections: m.sections, maxLength: maxLength);

String _spoken(_Module m) => _narrate(m).map((c) => c.text).join(' ');

void main() {
  test('the fixtures are the real content', () {
    expect(_hfw.length, greaterThanOrEqualTo(10));
    expect(_cdd.length, greaterThanOrEqualTo(5));
  });

  test('image alt text is never read; captions are', () {
    var checked = 0;
    for (final m in _all) {
      final spoken = _spoken(m);
      for (final s in m.sections.where((s) => s.contentType == 'IMAGE')) {
        final alt = s.content['alt'] as String?;
        final caption = s.content['caption'] as String?;
        if (alt != null && alt.length > 20 && alt != caption) {
          expect(spoken.contains(speakable(alt)), isFalse, reason: 'alt text of ${s.id}');
          checked++;
        }
        if (caption != null && caption.trim().isNotEmpty) expect(spoken, contains(speakable(caption).replaceAll(RegExp(r'\.$'), '')));
      }
    }
    expect(checked, greaterThan(30));
  });

  test('True/False quiz statements are never read; reading stops once per quiz block', () {
    var statements = 0;
    for (final m in _cdd) {
      final chunks = _narrate(m);
      // (A key take-away can repeat a statement's wording; what matters is that the quiz sections say nothing.)
      for (final s in m.sections.where((s) => s.contentType == 'TRUE_FALSE')) {
        expect(chunks.where((c) => c.sectionId == s.id && c.text.isNotEmpty), isEmpty, reason: s.id);
        statements++;
      }
      final hasQuiz = m.sections.any((s) => s.contentType == 'TRUE_FALSE');
      expect(chunks.any((c) => c.quizStop), hasQuiz, reason: m.code);
      for (var i = 1; i < chunks.length; i++) {
        expect(chunks[i].quizStop && chunks[i - 1].quizStop, isFalse, reason: 'consecutive statements are one stop');
      }
    }
    expect(statements, greaterThanOrEqualTo(18));
  });

  test('table rows are read as sentences', () {
    final acronyms = _hfw.first.sections.firstWhere((s) => s.contentType == 'TABLE');
    final spoken = _narrate(_hfw.first).where((c) => c.sectionId == acronyms.id).map((c) => c.text).join(' ');
    expect(spoken, contains('A-Z-M. Meaning: Azithromycin.'));
    expect(spoken, contains('ADR. Meaning: Adverse Drug Reactions.'));
    expect(tableSentences({
      'headers': ['Sign', 'Child 1', 'Child 2'],
      'rows': [
        ['Fever', 'Yes', 'No mark'],
      ],
    }), ['Fever. Child 1: Yes. Child 2: No.']);
    for (final m in _all) {
      expect(_spoken(m).contains('No mark'), isFalse, reason: m.code);
    }
  });

  test('pronunciations are applied and emphasis capitals are lowered', () {
    for (final m in _all) {
      final spoken = _spoken(m);
      for (final word in kPronunciations.keys) {
        expect(RegExp('\\b$word\\b').hasMatch(spoken), isFalse, reason: '$word in ${m.code}');
      }
      expect(RegExp(r'\b(NOT|CANNOT|NEVER|MUST)\b').hasMatch(spoken), isFalse, reason: m.code);
    }
    final all = _all.map(_spoken).join(' ');
    expect(all, contains('C-D-Ds'));
    expect(all, contains('S-A-M'));
    expect(speakable('Do NOT give AZM to CDDs. You CANNOT.'), 'Do not give A-Z-M to C-D-Ds. You cannot.');
  });

  test('clean-up: flipbook notes, lead-ins, ranges, secs and slashes', () {
    final all = _all.map(_spoken).join(' ');
    expect(all.contains('transcribed from image'), isFalse);
    expect(all.contains('marked with a red X'), isFalse);
    expect(RegExp(r'(^|[.!?] )(Step|In the field) ?[—–-]').hasMatch(all), isFalse);
    expect(all, contains('1 to 59 months'));
    expect(all.contains('secs'), isFalse);
    expect(speakable('Step — Greet the caregiver (marked with a red X).'), 'Greet the caregiver.');
    expect(speakable('Stand for 10 secs. Ages 12-59 months.'), 'Stand for 10 seconds. Ages 12 to 59 months.');
    expect(speakable('SMC: Yes/No. Received: _/_/202_'), 'SMC: Yes or No. Received: date');
    expect(speakable('he/she'), 'he or she');
    expect(speakable('Code AZM/26/3/C'), 'Code A-Z-M slash 26 slash 3 slash C');
    expect(speakable('Report at https://vigiflow-eforms.who-umc.org/ng/adr'), 'Report at https://vigiflow-eforms.who-umc.org/ng/adr');
  });

  test('a warning reads "Warning", its heading and text, without repeating an identical title', () {
    final w = _hfw.expand((m) => m.sections).firstWhere((s) => s.contentType == 'WARNING' && s.title == s.content['heading']);
    final out = _builder.build(title: 'T', sections: [w]).last.text;
    expect(out, startsWith('Warning. ${speakable(w.content['heading'] as String)}'));
    expect(RegExp(RegExp.escape(speakable(w.title!))).allMatches(out).length, 1);
  });

  test('videos and audio sections are skipped; the module title and description come first', () {
    final s = [
      ContentSection(id: 'v', moduleId: 'M', sectionNumber: 1, title: 'Clip', contentType: 'VIDEO', content: {'video_id': 'x', 'title': 'Watch me'}, sortOrder: 1),
      ContentSection(id: 'a', moduleId: 'M', sectionNumber: 2, title: 'Listen', contentType: 'AUDIO', content: {'text': 'Audio note'}, sortOrder: 2),
      ContentSection(id: 't', moduleId: 'M', sectionNumber: 3, title: null, contentType: 'TEXT', content: {'text': 'Hello'}, sortOrder: 3),
    ];
    final out = _builder.build(title: 'Module one', description: 'About AZM', sections: s);
    expect(out.map((c) => c.toString()), ['[] Module one. About A-Z-M.', '[t] Hello.']);
  });

  test('long sections are split at sentence ends, within the engine limit, losing nothing', () {
    for (final m in _all) {
      final whole = _narrate(m);
      final split = _narrate(m, maxLength: 160);
      for (final c in split) {
        expect(c.text.length, lessThanOrEqualTo(160), reason: c.text);
      }
      String joined(List<NarrationChunk> cs) => cs.map((c) => c.text).join(' ').replaceAll(RegExp(r'\s+'), ' ');
      expect(joined(split), joined(whole), reason: m.code);
    }
    final parts = splitForEngine('One two three. Four five six. Seven eight nine.', 30);
    expect(parts, ['One two three. Four five six.', 'Seven eight nine.']);
    final long = splitForEngine('${'word ' * 50}end.', 60);
    expect(long.every((p) => p.length <= 60), isTrue);
    expect(long.join(' ').replaceAll(RegExp(r'\s+'), ' '), '${'word ' * 50}end.'.trim());
  });

  test('narration for three real modules matches test/narration_vectors.json', () {
    final picked = [_hfw[0], _hfw[2], _cdd[1]];
    final vectors = {
      '_about': 'Expected "Read aloud" narration (English) from LocalNarrationBuilder for three real modules '
          '(content/*/content_sections.json). A server-side builder must produce the same chunks.',
      'max_length': kDefaultMaxSpeechInput,
      'modules': [
        for (final m in picked) {'module_code': m.code, 'chunks': [for (final c in _narrate(m)) c.toJson()]},
      ],
    };
    final file = File('test/narration_vectors.json');
    final encoded = '${const JsonEncoder.withIndent('  ').convert(vectors)}\n';
    if (Platform.environment['UPDATE_NARRATION_VECTORS'] == '1' || !file.existsSync()) file.writeAsStringSync(encoded);
    expect(jsonDecode(file.readAsStringSync()), jsonDecode(encoded));
  });
}
