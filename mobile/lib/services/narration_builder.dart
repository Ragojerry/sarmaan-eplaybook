import '../models/api_models.dart';

/// What "Read aloud" says for a module: one chunk per content section, in order
/// (long sections split for the speech engine). Built on the phone from the same
/// sections the reader shows, so it always matches the screen.
///
/// [NarrationSource] is the seam for later: server-written narration (planned
/// server-generated audio) can implement it and the reader UI stays the same.
/// test/narration_vectors.json holds this builder's output for three real
/// modules, so a future server builder can be checked against the same text.

/// One piece of narration. [sectionId] is the section it belongs to ('' for the
/// module title and description). A quiz stop has no text: reading pauses there
/// until the learner has done the quiz and presses Play.
class NarrationChunk {
  final String sectionId;
  final String text;
  final bool quizStop;

  const NarrationChunk(this.sectionId, this.text, {this.quizStop = false});

  Map<String, dynamic> toJson() => {'section_id': sectionId, 'text': text, if (quizStop) 'quiz_stop': true};

  @override
  String toString() => quizStop ? '[quiz $sectionId]' : '[$sectionId] $text';
}

abstract class NarrationSource {
  List<NarrationChunk> build({required String title, String? description, required List<ContentSection> sections, int maxLength});
}

/// Fallback when the engine does not report its maximum input length.
const kDefaultMaxSpeechInput = 3500;

/// How English abbreviations are spoken (a const list for now).
const kPronunciations = <String, String>{
  'CDDs': 'C-D-Ds',
  'AZM': 'A-Z-M',
  'SAM': 'S-A-M',
  'MAM': 'M-A-M',
  'CDD': 'C-D-D',
  'SBC': 'S-B-C',
  'IPC': 'I-P-C',
  'ANC': 'A-N-C',
};

/// The section types read aloud; everything else (TRUE_FALSE handled as a quiz
/// stop, VIDEO, AUDIO, unknown types) is skipped.
const _readTypes = {'HEADING', 'TEXT', 'LIST', 'IMAGE', 'WARNING', 'CALLOUT', 'JOB_AID', 'TABLE'};

class LocalNarrationBuilder implements NarrationSource {
  const LocalNarrationBuilder();

  @override
  List<NarrationChunk> build({
    required String title,
    String? description,
    required List<ContentSection> sections,
    int maxLength = kDefaultMaxSpeechInput,
  }) {
    final out = <NarrationChunk>[];
    void add(String sectionId, String raw) {
      final text = speakable(raw);
      if (text.isEmpty) return;
      for (final part in splitForEngine(text, maxLength)) {
        // The same words twice in a row (a heading repeated as a caption) are read once.
        if (out.isNotEmpty && !out.last.quizStop && out.last.text == part) continue;
        out.add(NarrationChunk(sectionId, part));
      }
    }

    add('', [title, if (description != null) description].map(_sentence).join(' '));
    String? lastHeading;
    for (final s in sections) {
      final c = s.content;
      final type = s.contentType;
      if (type == 'TRUE_FALSE') {
        // One stop per quiz block (consecutive statements are one quiz).
        if (out.isEmpty || !out.last.quizStop) out.add(NarrationChunk(s.id, '', quizStop: true));
        continue;
      }
      if (!_readTypes.contains(type)) continue;
      final parts = <String>[];
      switch (type) {
        case 'HEADING':
          parts.add(_str(c['text']));
          lastHeading = _str(c['text']);
        case 'TEXT':
          parts.add(_str(c['text']));
        case 'LIST':
          final listTitle = _str(s.title ?? c['title']);
          if (listTitle.isNotEmpty && !_same(listTitle, lastHeading)) parts.add(listTitle);
          parts.addAll([for (final i in (c['items'] as List? ?? const [])) _str(i)]);
        case 'IMAGE':
          parts.add(_str(c['caption'])); // never the alt text
        case 'WARNING':
        case 'CALLOUT':
        case 'JOB_AID':
          final heading = _str(c['heading']);
          final sectionTitle = _str(s.title);
          if (type == 'WARNING') parts.add('Warning');
          if (sectionTitle.isNotEmpty && !_same(sectionTitle, heading)) parts.add(sectionTitle);
          parts.add(heading);
          parts.add(_str(c['text']));
        case 'TABLE':
          parts.addAll(tableSentences(c));
      }
      // A list title repeats the heading just above it (several lists can share one heading).
      if (type != 'HEADING' && type != 'LIST') lastHeading = null;
      add(s.id, parts.where((p) => p.trim().isNotEmpty).map(_sentence).join(' '));
    }
    return out;
  }
}

/// One sentence per table row: "<first cell>. <header>: <value>. ..."; "No mark" is read as "No".
List<String> tableSentences(Map<String, dynamic> c) {
  final headers = [for (final h in (c['headers'] as List? ?? const [])) _str(h)];
  final rows = <String>[];
  for (final r in (c['rows'] as List? ?? const [])) {
    final cells = [for (final x in (r as List)) _str(x)];
    if (cells.isEmpty) continue;
    final parts = <String>[if (cells.first.isNotEmpty) _sentence(_noMark(cells.first))];
    for (var i = 1; i < cells.length; i++) {
      if (cells[i].isEmpty) continue;
      final label = i < headers.length ? headers[i] : '';
      parts.add(_sentence(label.isEmpty ? _noMark(cells[i]) : '$label: ${_noMark(cells[i])}'));
    }
    rows.add(parts.join(' '));
  }
  return rows;
}

String _noMark(String v) => v.trim().toLowerCase() == 'no mark' ? 'No' : v;

String _str(Object? v) => v == null ? '' : v.toString().trim();

bool _same(String a, String? b) => b != null && a.trim().toLowerCase() == b.trim().toLowerCase();

String _sentence(String s) {
  final t = s.trim();
  if (t.isEmpty) return t;
  return RegExp(r'[.!?:;]$').hasMatch(t) ? t : '$t.';
}

final _flipbookNote = RegExp(r'\s*\((?:marked|transcribed|shown)\b[^)]*\)', caseSensitive: false);
final _leadIn = RegExp(r'(^|(?<=[.!?]\s))(?:Step|In the field)\s*[—–-]\s*', caseSensitive: false);
final _emphasis = RegExp(r'\b(NOT|CANNOT|DO|NEVER|ONLY|MUST)\b');
final _range = RegExp(r'(\d+)\s*[–—-]\s*(\d+)');
final _secs = RegExp(r'\bsecs?\b');
final _url = RegExp(r'https?://\S+');
final _blankDate = RegExp(r'_+/_+/[\d_.]*');
final _wordSlash = RegExp(r'(?<=[A-Za-z])\s*/\s*(?=[A-Za-z])');

/// The spoken form of a piece of content text (English).
String speakable(String text) {
  // Web addresses are left for the engine, untouched by the rules below.
  final urls = <String>[];
  var t = text.replaceAllMapped(_url, (m) {
    urls.add(m[0]!);
    return '\u0000${urls.length - 1}\u0000';
  });
  t = t.replaceAll(_flipbookNote, '');
  t = t.replaceAll(_leadIn, '');
  t = t.replaceAllMapped(_emphasis, (m) => m[1]!.toLowerCase());
  t = t.replaceAllMapped(_range, (m) => '${m[1]} to ${m[2]}');
  t = t.replaceAll(_secs, 'seconds');
  // Slashes: "Yes/No" -> "Yes or No"; a blank date "_/_/202_" -> "date"; codes such as
  // AZM/26/3/... read "slash".
  t = t.replaceAll(_blankDate, 'date');
  t = t.replaceAll(_wordSlash, ' or ');
  t = t.replaceAll('/', ' slash ');
  t = t.replaceAllMapped(RegExp('\u0000(\\d+)\u0000'), (m) => urls[int.parse(m[1]!)]);
  kPronunciations.forEach((word, spoken) {
    t = t.replaceAll(RegExp('\\b$word\\b'), spoken);
  });
  return t.replaceAll(RegExp(r'\s+'), ' ').replaceAll(' .', '.').trim();
}

/// Splits [text] into pieces no longer than [maxLength], at sentence ends (then
/// at commas or spaces for a sentence that is itself too long).
List<String> splitForEngine(String text, int maxLength) {
  if (text.length <= maxLength) return [text];
  // Only at a space after . ! or ? so nothing is ever dropped ("etc.)" stays in its sentence).
  final sentences = text.split(RegExp(r'(?<=[.!?])\s+')).map((s) => s.trim()).where((s) => s.isNotEmpty);
  final out = <String>[];
  var current = '';
  void flush() {
    if (current.isNotEmpty) out.add(current);
    current = '';
  }

  for (final s in sentences) {
    if (s.length > maxLength) {
      flush();
      var rest = s;
      while (rest.length > maxLength) {
        var cut = rest.lastIndexOf(', ', maxLength);
        if (cut < maxLength ~/ 2) cut = rest.lastIndexOf(' ', maxLength);
        if (cut <= 0) cut = maxLength;
        out.add(rest.substring(0, cut + (rest[cut] == ',' ? 1 : 0)).trim());
        rest = rest.substring(cut + 1).trim();
      }
      current = rest;
    } else if (current.isEmpty) {
      current = s;
    } else if (current.length + 1 + s.length <= maxLength) {
      current = '$current $s';
    } else {
      flush();
      current = s;
    }
  }
  flush();
  return out;
}
