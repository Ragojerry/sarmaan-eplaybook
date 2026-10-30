/// Deterministic extractive question answering — the on-device half of the
/// revised Phases 10/11. THIS FILE IS A LINE-FOR-LINE MIRROR of
/// backend/app/ai/qa_engine.py so the phone answers identically with or
/// without a connection. Parity is enforced by test/qa_vectors.json (generated
/// by backend/scripts/generate_qa_vectors.py): test/qa_engine_test.dart
/// replays the exact vectors the Python tests do. If you change the algorithm
/// here, change it in Python, regenerate the vectors, and re-run both suites.
///
/// Pipeline: tokenize -> drop stopwords -> light stemming -> synonym
/// expansion into "concepts" -> BM25 -> sentence-level re-rank -> verbatim
/// sentence extraction -> citation -> strict refusal when evidence is thin.
/// No model, no network, nothing generated: every word of an answer is copied
/// from approved training content.
///
/// Float-sensitive steps use integer arithmetic (percentages, scaled scores)
/// so Dart and Python cannot disagree on rounding.
library;

import 'dart:math' as math;

const int kDefaultMinCoveragePct = 50;
const double _k1 = 1.5;
const double _b = 0.75;

const String kFallbackMessage =
    "I couldn't find a reliable answer to this question in your downloaded training materials.";

const List<String> kSuggestions = [
  'Who is eligible for AZM?',
  'How much AZM should a child receive?',
  'When should a child be referred to a health facility?',
  'What should I do if a child vomits after the medicine?',
];

final Set<String> kStopwords = ('a about above after again all also am an and any are as at be because been before being below between '
        'both but by can could did do does doing down during each few for from further had has have having he her '
        'here hers him his how i if in into is it its just me more most my no nor not of off on once only or other '
        'our out over own same she should so some such than that the their them then there these they this those '
        'through to too under until up very was we were what when where which while who whom why will with would '
        'you your')
    .split(' ')
    .toSet();

const List<List<String>> kSynonymGroups = [
  ['vomit', 'vomiting', 'vomited', 'retch', 'puke', 'regurgitate', 'threw', 'throw', 'thrown', 'spit', 'spat'],
  ['medicine', 'drug', 'medication', 'tablet', 'suspension', 'antibiotic', 'dose', 'dosage', 'dosing'],
  ['azm', 'azithromycin', 'medicine', 'drug', 'medication'],
  ['much', 'amount', 'quantity', 'volume', 'ml', 'dose', 'dosage', 'dosing'],
  ['prepare', 'mix', 'reconstitute', 'dissolve', 'shake', 'dilute'],
  ['child', 'children', 'infant', 'baby', 'toddler', 'kid', 'kids'],
  ['age', 'aged', 'old', 'older', 'year', 'years', 'month', 'months', 'young', 'younger', 'newborn', 'neonate'],
  ['eligible', 'eligibility', 'qualify', 'allowed', 'receive'],
  ['sick', 'ill', 'unwell', 'illness'],
  ['fever', 'temperature', 'hot'],
  ['refer', 'referral', 'referred', 'facility', 'clinic', 'hospital'],
  ['report', 'contact', 'email', 'concern', 'complaint', 'escalate'],
  ['malnutrition', 'malnourished', 'muac', 'wasting', 'sam', 'thin', 'skinny', 'underweight', 'emaciated', 'armband'],
  ['allergy', 'allergic', 'allergies', 'reaction', 'rash', 'swelling'],
  ['photo', 'photograph', 'picture', 'camera'],
  ['house', 'home', 'household', 'compound', 'chalk', 'mark', 'marking', 'marked'],
  ['record', 'recording', 'card', 'register'],
  ['caregiver', 'parent', 'mother', 'guardian', 'mum'],
  ['safeguard', 'safeguarding', 'abuse', 'abused', 'protection', 'protect', 'harm', 'exploitation', 'misconduct'],
  ['pregnant', 'pregnancy', 'anc', 'antenatal'],
];

// ---------------------------------------------------------------- models

class QaChunk {
  final String id;
  final String? moduleId;
  final String? sectionId;
  final String moduleCode;
  final String sourceTitle;
  final String? sectionTitle;
  final String chunkText;

  const QaChunk({
    required this.id,
    this.moduleId,
    this.sectionId,
    required this.moduleCode,
    required this.sourceTitle,
    this.sectionTitle,
    required this.chunkText,
  });

  factory QaChunk.fromJson(Map<String, dynamic> j) => QaChunk(
        id: j['id'] as String,
        moduleId: j['module_id'] as String?,
        sectionId: j['section_id'] as String?,
        moduleCode: j['module_code'] as String,
        sourceTitle: j['source_title'] as String,
        sectionTitle: j['section_title'] as String?,
        chunkText: j['chunk_text'] as String,
      );
}

class AnswerSource {
  final String chunkId;
  final String? moduleId;
  final String? sectionId;
  final String moduleCode;
  final String moduleTitle;
  final String? sectionTitle;
  final String snippet;

  const AnswerSource({
    required this.chunkId,
    this.moduleId,
    this.sectionId,
    required this.moduleCode,
    required this.moduleTitle,
    this.sectionTitle,
    required this.snippet,
  });

  factory AnswerSource.fromJson(Map<String, dynamic> j) => AnswerSource(
        chunkId: j['chunk_id'] as String,
        moduleId: j['module_id'] as String?,
        sectionId: j['section_id'] as String?,
        moduleCode: j['module_code'] as String,
        moduleTitle: j['module_title'] as String,
        sectionTitle: j['section_title'] as String?,
        snippet: j['snippet'] as String,
      );
}

class AnswerResult {
  final String answer;
  final bool matched;
  final double confidence;
  final bool offline;
  final List<AnswerSource> sources;
  final List<String> suggestions;

  const AnswerResult({
    required this.answer,
    required this.matched,
    required this.confidence,
    required this.offline,
    required this.sources,
    required this.suggestions,
  });

  factory AnswerResult.fromJson(Map<String, dynamic> j) => AnswerResult(
        answer: j['answer'] as String,
        matched: j['matched'] as bool,
        confidence: (j['confidence'] as num).toDouble(),
        offline: (j['offline'] as bool?) ?? false,
        sources: [for (final s in (j['sources'] as List)) AnswerSource.fromJson(s as Map<String, dynamic>)],
        suggestions: [for (final s in (j['suggestions'] as List)) s as String],
      );

  AnswerResult copyWith({bool? offline}) => AnswerResult(
        answer: answer,
        matched: matched,
        confidence: confidence,
        offline: offline ?? this.offline,
        sources: sources,
        suggestions: suggestions,
      );
}

class QaDoc {
  final QaChunk chunk;
  final Map<String, int> tf;
  final int len;

  QaDoc(this.chunk, this.tf, this.len);
}

class QaIndex {
  final List<QaDoc> docs;
  final double avgdl;

  QaIndex(this.docs, this.avgdl);
}

// ---------------------------------------------------------------- text

final RegExp _alnum = RegExp(r'[\p{L}\p{N}]', unicode: true);

bool _isNumber(String token) {
  if (token.isEmpty) return false;
  for (var i = 0; i < token.length; i++) {
    final c = token.codeUnitAt(i);
    if (c < 48 || c > 57) return false;
  }
  return true;
}

/// Lowercase, split on any non-alphanumeric character (Unicode-aware, so
/// Hausa/Fulfulde/Kanuri letters survive), keep numbers and tokens of 2+
/// characters.
List<String> tokenize(String text) {
  final tokens = <String>[];
  final current = StringBuffer();
  for (final rune in text.toLowerCase().runes) {
    final ch = String.fromCharCode(rune);
    if (_alnum.hasMatch(ch)) {
      current.write(ch);
    } else if (current.isNotEmpty) {
      tokens.add(current.toString());
      current.clear();
    }
  }
  if (current.isNotEmpty) tokens.add(current.toString());
  return tokens.where((t) => _isNumber(t) || t.length >= 2).toList();
}

String stem(String token) {
  var t = token;
  if (_isNumber(t)) return t;
  if (t.length > 5 && t.endsWith('ing')) {
    t = t.substring(0, t.length - 3);
  } else if (t.length > 4 && t.endsWith('ed')) {
    t = t.substring(0, t.length - 2);
  } else if (t.length > 4 && t.endsWith('es')) {
    t = t.substring(0, t.length - 2);
  } else if (t.length > 3 && t.endsWith('s') && !t.endsWith('ss')) {
    t = t.substring(0, t.length - 1);
  }
  if (t.length > 3 && t.endsWith('e')) {
    t = t.substring(0, t.length - 1);
  }
  return t;
}

/// Stemmed, de-duplicated, stopword-free terms of a question, in order.
List<String> contentTerms(String text) {
  final seen = <String>{};
  final out = <String>[];
  for (final tok in tokenize(text)) {
    if (kStopwords.contains(tok)) continue;
    final s = stem(tok);
    if (seen.add(s)) out.add(s);
  }
  return out;
}

Map<String, Set<String>> _buildSynonymIndex() {
  final index = <String, Set<String>>{};
  for (final group in kSynonymGroups) {
    final stems = group.map(stem).toSet();
    for (final s in stems) {
      index.putIfAbsent(s, () => <String>{}).addAll(stems);
    }
  }
  return index;
}

final Map<String, Set<String>> _synonymIndex = _buildSynonymIndex();

Set<String> expand(String termStem) {
  final out = <String>{termStem};
  final syn = _synonymIndex[termStem];
  if (syn != null) out.addAll(syn);
  return out;
}

final RegExp _yearsRe = RegExp(r'\b(\d{1,2})\s*(?:-|\s)?\s*(?:years?|yrs?)\b', caseSensitive: false);

/// The training tables are written in months, so "2 year old" is read as
/// "24 month old" (otherwise it matched the 1-2 month dose row).
String normalizeAges(String question) =>
    question.replaceAllMapped(_yearsRe, (m) => '${int.parse(m.group(1)!) * 12} months');

/// One concept per distinct (synonym-expanded) question term.
List<Set<String>> buildConcepts(String question) {
  question = normalizeAges(question);
  final concepts = <Set<String>>[];
  final seen = <String>{};
  for (final term in contentTerms(question)) {
    final c = expand(term);
    final key = (c.toList()..sort()).join('|');
    if (!seen.add(key)) continue;
    concepts.add(c);
  }
  return concepts;
}

List<String> _docTerms(String text) =>
    tokenize(text).where((t) => !kStopwords.contains(t)).map(stem).toList();

QaIndex buildIndex(List<QaChunk> chunks) {
  final docs = <QaDoc>[];
  var totalLen = 0;
  for (final ch in chunks) {
    final title = ch.sectionTitle ?? '';
    final terms = _docTerms('$title . ${ch.chunkText}');
    final tf = <String, int>{};
    for (final t in terms) {
      tf[t] = (tf[t] ?? 0) + 1;
    }
    docs.add(QaDoc(ch, tf, terms.length));
    totalLen += terms.length;
  }
  final avgdl = docs.isEmpty ? 0.0 : totalLen / docs.length;
  return QaIndex(docs, avgdl);
}

class _Ranked {
  final QaDoc doc;
  final int scoreI;
  final int matched;
  int sentCov = 0;

  _Ranked(this.doc, this.scoreI, this.matched);
}

List<_Ranked> _rank(List<Set<String>> concepts, QaIndex index) {
  final docs = index.docs;
  final avgdl = index.avgdl;
  if (concepts.isEmpty || docs.isEmpty || avgdl == 0) return [];
  final n = docs.length;
  final idfs = <double>[];
  for (final c in concepts) {
    var df = 0;
    for (final d in docs) {
      for (final s in c) {
        if (d.tf.containsKey(s)) {
          df += 1;
          break;
        }
      }
    }
    idfs.add(math.log(1 + (n - df + 0.5) / (df + 0.5)));
  }
  final results = <_Ranked>[];
  for (final d in docs) {
    var score = 0.0;
    var matched = 0;
    for (var i = 0; i < concepts.length; i++) {
      var tf = 0;
      for (final s in concepts[i]) {
        tf += d.tf[s] ?? 0;
      }
      if (tf > 0) {
        matched += 1;
        final denom = tf + _k1 * (1 - _b + _b * d.len / avgdl);
        score += idfs[i] * (tf * (_k1 + 1)) / denom;
      }
    }
    results.add(_Ranked(d, (score * 1000000 + 0.5).floor(), matched));
  }
  results.sort((a, b) {
    final c = b.scoreI.compareTo(a.scoreI);
    if (c != 0) return c;
    return a.doc.chunk.id.compareTo(b.doc.chunk.id);
  });
  return results;
}

List<String> splitSentences(String text) {
  var t = text;
  for (final mark in ['.', '!', '?']) {
    t = t.replaceAll('$mark ', '$mark\n');
  }
  t = t.replaceAll(' \u00b7 ', '\n');
  return t.split('\n').map((s) => s.trim()).where((s) => s.isNotEmpty).toList();
}

final RegExp _decimal = RegExp(r'[0-9]+\.[0-9]+');
final RegExp _parens = RegExp(r'\([^)]*\)');
final RegExp _range = RegExp(r'([0-9]{1,9})\s*[\u2013\u2014-]\s*([0-9]{1,9})');

/// Numeric ranges like '3-4 months' in a sentence. Parenthesised text (a
/// table header '(1-11 months)') and decimals ('11.5 - 12.4 cm') are ignored
/// so they can't create bogus ranges.
List<List<int>> _ranges(String sentence) {
  var t = sentence.replaceAll(_parens, ' ');
  t = t.replaceAll(_decimal, ' ');
  final out = <List<int>>[];
  for (final m in _range.allMatches(t)) {
    final lo = int.parse(m.group(1)!);
    final hi = int.parse(m.group(2)!);
    if (lo <= hi) out.add([lo, hi]);
  }
  return out;
}

/// A concept is hit if any of its stems appears in the sentence. Numbers are
/// range-aware: in a sentence containing ranges, a number only matches if it
/// falls INSIDE one (so '4' matches '3-4 months' but not the dose value in
/// '5-11 months; Dose: 4 ml') — this stops a dosing question picking the
/// wrong age row.
bool _conceptHit(Set<String> stems, List<List<int>> ranges, Set<String> concept) {
  for (final s in concept) {
    if (_isNumber(s)) {
      if (ranges.isNotEmpty) {
        if (s.length <= 9) {
          final n = int.parse(s);
          for (final r in ranges) {
            if (r[0] <= n && n <= r[1]) return true;
          }
        }
      } else if (stems.contains(s)) {
        return true;
      }
    } else if (stems.contains(s)) {
      return true;
    }
  }
  return false;
}

int _sentenceCoverage(String sentence, List<Set<String>> concepts) {
  final stems = _docTerms(sentence).toSet();
  final ranges = _ranges(sentence);
  var covered = 0;
  for (final c in concepts) {
    if (_conceptHit(stems, ranges, c)) covered += 1;
  }
  return covered;
}

int _bestSentenceCov(String chunkText, List<Set<String>> concepts) {
  var best = 0;
  for (final sentence in splitSentences(chunkText)) {
    final c = _sentenceCoverage(sentence, concepts);
    if (c > best) best = c;
  }
  return best;
}

class _Scored {
  final int i;
  final int cov;
  final String s;

  _Scored(this.i, this.cov, this.s);
}

/// The most relevant sentence(s), verbatim. A second sentence is added only
/// when it is AS relevant as the first. Empty if no sentence matches.
List<String> bestSentences(String chunkText, List<Set<String>> concepts, {int limit = 2}) {
  final sentences = splitSentences(chunkText);
  final scored = <_Scored>[];
  for (var i = 0; i < sentences.length; i++) {
    final cov = _sentenceCoverage(sentences[i], concepts);
    if (cov > 0) scored.add(_Scored(i, cov, sentences[i]));
  }
  if (scored.isEmpty) return [];
  scored.sort((a, b) {
    final c = b.cov.compareTo(a.cov);
    if (c != 0) return c;
    return a.i.compareTo(b.i);
  });
  final chosen = <_Scored>[scored[0]];
  if (limit > 1 && scored.length > 1 && scored[1].cov == scored[0].cov) {
    chosen.add(scored[1]);
  }
  chosen.sort((a, b) => a.i.compareTo(b.i));
  return chosen.map((c) => c.s).toList();
}

int _pct(int matched, int total) => (100 * matched + total ~/ 2) ~/ total;

AnswerSource _source(QaChunk chunk, String snippet) => AnswerSource(
      chunkId: chunk.id,
      moduleId: chunk.moduleId,
      sectionId: chunk.sectionId,
      moduleCode: chunk.moduleCode,
      moduleTitle: chunk.sourceTitle,
      sectionTitle: chunk.sectionTitle,
      snippet: snippet,
    );

AnswerResult _fallback([int confidencePct = 0]) => AnswerResult(
      answer: kFallbackMessage,
      matched: false,
      confidence: confidencePct / 100,
      offline: false,
      sources: const [],
      suggestions: List<String>.from(kSuggestions),
    );

/// Answers [question] from [chunks], or returns the strict fallback.
AnswerResult answerQuestion(String question, List<QaChunk> chunks, {int minCoveragePct = kDefaultMinCoveragePct}) {
  final index = buildIndex(chunks);
  final concepts = buildConcepts(question);
  final ranked = _rank(concepts, index);
  final candidates = ranked.where((r) => r.matched > 0 && r.scoreI > 0).toList();
  if (candidates.isEmpty) return _fallback();

  // Re-rank: the chunk holding the single sentence that covers the most
  // question concepts wins; chunk-level coverage, then BM25, break ties.
  for (final r in candidates) {
    r.sentCov = _bestSentenceCov(r.doc.chunk.chunkText, concepts);
  }
  candidates.sort((a, b) {
    var c = b.sentCov.compareTo(a.sentCov);
    if (c != 0) return c;
    c = b.matched.compareTo(a.matched);
    if (c != 0) return c;
    c = b.scoreI.compareTo(a.scoreI);
    if (c != 0) return c;
    return a.doc.chunk.id.compareTo(b.doc.chunk.id);
  });

  final best = candidates[0];
  final coveragePct = _pct(best.matched, concepts.length);
  if (best.sentCov == 0 || coveragePct < minCoveragePct) return _fallback(coveragePct);

  final bestChunk = best.doc.chunk;
  final sentences = bestSentences(bestChunk.chunkText, concepts, limit: 2);
  final sources = <AnswerSource>[_source(bestChunk, sentences[0])];

  for (final r in candidates.skip(1)) {
    if (sources.length >= 3) break;
    final minCov = best.sentCov < 2 ? best.sentCov : 2;
    if (r.sentCov < minCov || _pct(r.matched, concepts.length) < minCoveragePct) continue;
    if (r.scoreI * 2 < best.scoreI) continue;
    final sn = bestSentences(r.doc.chunk.chunkText, concepts, limit: 1);
    if (sn.isNotEmpty) sources.add(_source(r.doc.chunk, sn[0]));
  }

  return AnswerResult(
    answer: sentences.join(' '),
    matched: true,
    confidence: coveragePct / 100,
    offline: false,
    sources: sources,
    suggestions: const [],
  );
}
