/// Deterministic extractive question answering — the on-device half of the
/// revised Phases 10/11. THIS FILE IS A LINE-FOR-LINE MIRROR of
/// backend/app/ai/qa_engine.py so the phone answers identically with or
/// without a connection. Parity is enforced by test/qa_vectors.json (generated
/// by backend/scripts/generate_qa_vectors.py): test/qa_engine_test.dart
/// replays the exact vectors the Python tests do. If you change the algorithm
/// here, change it in Python, regenerate the vectors, and re-run both suites.
///
/// Pipeline: tokenize -> drop stopwords -> light stemming -> synonym
/// expansion into "concepts" -> a trainer-approved curated answer whose
/// question matches (chunks with [QaChunk.faqQuestions]; see [matchFaq]) ->
/// BM25 candidate chunks -> sentence scoring
/// (rare words weigh more, matching section headings help, dose questions
/// prefer "N ml" sentences, definition questions prefer defining sentences,
/// example codes count half) -> verbatim sentence extraction -> citation ->
/// refusal when the evidence covers less than half the question's weight.
/// No model, no network, nothing generated: every word of an answer is copied
/// from approved training content.
///
/// Float-sensitive steps use integer arithmetic (percentages, scaled scores)
/// so Dart and Python cannot disagree on rounding.
library;

import 'dart:math' as math;

const int kDefaultMinCoveragePct = 50;
const int kFaqMinPct = 67; // share of terms a curated question and the user's must have in common, both ways
const double _k1 = 1.5;
const double _b = 0.75;

const String kFallbackMessage =
    "I couldn't find a reliable answer to this question in your downloaded training materials.";

const String kGreetingMessage =
    'Hello! I answer questions from your AZM training modules. Ask in your own words, or tap one of the questions below.';

const List<String> kSuggestions = [
  'Who is eligible for AZM?',
  'How much AZM should a child receive?',
  'When should a child be referred to a health facility?',
  'What should I do if a child vomits after the medicine?',
];

final Set<String> kStopwords = ('a about above after again all also am an and any are as at be because been before being below between '
        'both but by can could did do does doing down during each few for from further had has have having he her '
        'here hers him his how i if in into is it its just me more most my no nor not of off on only or other '
        'our out over own same she should so some such than that the their them then there these they this those '
        'through to too under until up very was we were what when where which while who whom why will with would '
        'you your many now please tell give given gives giving receive received receives receiving get gets got')
    .split(' ')
    .toSet();

const List<List<String>> kSynonymGroups = [
  ['vomit', 'vomiting', 'vomited', 'retch', 'puke', 'regurgitate', 'threw', 'throw', 'thrown', 'spit', 'spat'],
  ['medicine', 'drug', 'medication', 'tablet', 'suspension', 'antibiotic', 'dose', 'dosage', 'dosing'],
  ['azm', 'azithromycin', 'medicine', 'drug', 'medication'],
  ['much', 'amount', 'quantity', 'volume', 'ml', 'dose', 'dosage', 'dosing'],
  ['prepare', 'mix', 'reconstitute', 'dissolve', 'shake', 'dilute'],
  ['child', 'children', 'infant', 'baby', 'toddler', 'kid', 'kids'],
  ['age', 'aged', 'old', 'older', 'year', 'years', 'month', 'months', 'young', 'younger', 'newborn', 'neonate', 'group'],
  ['eligible', 'eligibility', 'qualify', 'allowed', 'target', 'targets', 'targeted'],
  ['sick', 'ill', 'unwell', 'illness'],
  ['fever', 'temperature', 'hot'],
  ['refer', 'referral', 'referred', 'facility', 'clinic', 'hospital'],
  ['report', 'contact', 'email', 'concern', 'complaint', 'escalate'],
  ['malnutrition', 'malnourished', 'muac', 'wasting', 'sam', 'thin', 'skinny', 'underweight', 'emaciated', 'armband'],
  ['allergy', 'allergic', 'allergies', 'reaction', 'rash', 'swelling', 'swollen', 'swell'],
  ['photo', 'photograph', 'picture', 'camera'],
  ['house', 'home', 'household', 'compound', 'chalk', 'mark', 'marking', 'marked'],
  ['record', 'recording', 'card', 'register'],
  ['caregiver', 'parent', 'mother', 'guardian', 'mum'],
  ['safeguard', 'safeguarding', 'abuse', 'abused', 'protection', 'protect', 'harm', 'exploitation', 'misconduct'],
  ['pregnant', 'pregnancy', 'anc', 'antenatal'],
  ['often', 'frequency', 'frequently', 'once', 'twice', 'times', 'annually', 'biannually', 'interval'],
  ['cut', 'cutoff', 'threshold', 'range', 'classification', 'classify', 'level'],
];

final Set<String> kGreetings =
    'hi hello hey hiya good morning afternoon evening day thanks thank you ok okay greetings sannu salam'.split(' ').toSet();

// ---------------------------------------------------------------- models

class QaChunk {
  final String id;
  final String? moduleId;
  final String? sectionId;
  final String moduleCode;
  final String sourceTitle;
  final String? sectionTitle;
  final String chunkText;

  /// Set on a curated answer: the question it answers and its other wordings.
  final List<String> faqQuestions;

  const QaChunk({
    required this.id,
    this.moduleId,
    this.sectionId,
    required this.moduleCode,
    required this.sourceTitle,
    this.sectionTitle,
    required this.chunkText,
    this.faqQuestions = const [],
  });

  factory QaChunk.fromJson(Map<String, dynamic> j) => QaChunk(
        id: j['id'] as String,
        moduleId: j['module_id'] as String?,
        sectionId: j['section_id'] as String?,
        moduleCode: j['module_code'] as String,
        sourceTitle: j['source_title'] as String,
        sectionTitle: j['section_title'] as String?,
        chunkText: j['chunk_text'] as String,
        faqQuestions: [for (final q in (j['faq_questions'] as List?) ?? const []) q as String],
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

  /// 'module', or 'reference' for the server's reference library (moduleId
  /// is then null and moduleTitle is the document's title).
  final String kind;

  const AnswerSource({
    required this.chunkId,
    this.moduleId,
    this.sectionId,
    required this.moduleCode,
    required this.moduleTitle,
    this.sectionTitle,
    required this.snippet,
    this.kind = 'module',
  });

  bool get isReference => kind == 'reference';

  factory AnswerSource.fromJson(Map<String, dynamic> j) => AnswerSource(
        chunkId: j['chunk_id'] as String,
        moduleId: j['module_id'] as String?,
        sectionId: j['section_id'] as String?,
        moduleCode: j['module_code'] as String,
        moduleTitle: j['module_title'] as String,
        sectionTitle: j['section_title'] as String?,
        snippet: j['snippet'] as String,
        kind: (j['kind'] as String?) ?? 'module',
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

final RegExp _definitionQ = RegExp(
    r"^\s*(?:what\s+(?:is|are|does|do)|what's|whats|define|meaning\s+of|who\s+(?:is|are))\b",
    caseSensitive: false);
final RegExp _definitionWords =
    RegExp(r'\b(?:stands?\s+for|full\s+(?:meaning|form)|meaning|means?|definition|define)\b', caseSensitive: false);
final RegExp _whoGets =
    RegExp(r'^\s*(?:who|which)\b.*\b(?:receive[sd]?|get|gets|given|give)\b', caseSensitive: false);

bool isDefinitionQuestion(String question) => _definitionQ.hasMatch(question);

/// How much / dose questions: the answer should state an amount.
bool isQuantityQuestion(String question) {
  final terms = contentTerms(question).toSet();
  return terms.contains('much') || terms.intersection(const {'dos', 'dosag', 'amount', 'quantity', 'volum', 'ml'}).isNotEmpty;
}

/// 'Which children should receive AZM?' asks who is eligible, though it never
/// says so; the verbs themselves are stopwords.
bool isEligibilityQuestion(String question) => _whoGets.hasMatch(question);

bool isGreeting(String question) {
  final tokens = tokenize(question);
  return tokens.isNotEmpty && tokens.every(kGreetings.contains);
}

/// One concept per distinct (synonym-expanded) question term. Wording that
/// only says "define this" (stand for, meaning) is not a concept.
List<Set<String>> buildConcepts(String question) {
  final terms = contentTerms(normalizeAges(question).replaceAll(_definitionWords, ' '));
  if (isEligibilityQuestion(question)) terms.add(stem('eligible'));
  final concepts = <Set<String>>[];
  final seen = <String>{};
  for (final term in terms) {
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
  List<_Scored> scored = const [];
  int best = 0;

  _Ranked(this.doc, this.scoreI, this.matched);
}

List<double> _idfs(List<Set<String>> concepts, List<QaDoc> docs) {
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
  return idfs;
}

List<_Ranked> _rank(List<Set<String>> concepts, QaIndex index) {
  final docs = index.docs;
  final avgdl = index.avgdl;
  if (concepts.isEmpty || docs.isEmpty || avgdl == 0) return [];
  final idfs = _idfs(concepts, docs);
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

final RegExp _ml = RegExp(r'\b[0-9]+(?:\.[0-9]+)?\s?ml\b', caseSensitive: false);
final RegExp _code = RegExp(r'[A-Za-z0-9]+(?:/[A-Za-z0-9]+){3,}');
final RegExp _parenText = RegExp(r'\(([^)]*)\)');
const Set<String> _definingVerbs = {'stands', 'means', 'refers'};
const Set<String> _linkingVerbs = {'is', 'are'};

const int kQuantityBonus = 2000;
const int kDefinesBonus = 2000;
const int kDescribesBonus = 1000;

/// kDefinesBonus if the sentence spells a question term out: 'Community Drug
/// Distributors (CDDs)', 'AZM stands for ...'; kDescribesBonus for
/// 'Safeguarding is ...'; else 0. Only a one-word bracket is an abbreviation;
/// '(that would suggest >59 months)' defines nothing.
int _definitionBonus(String sentence, List<Set<String>> concepts) {
  for (final m in _parenText.allMatches(sentence)) {
    final inside = tokenize(m.group(1)!);
    if (inside.length == 1 && concepts.any((c) => c.contains(stem(inside[0])))) return kDefinesBonus;
  }
  final tokens = tokenize(sentence);
  var best = 0;
  for (var i = 0; i < tokens.length - 1; i++) {
    final st = stem(tokens[i]);
    if (!concepts.any((c) => c.contains(st))) continue;
    if (_definingVerbs.contains(tokens[i + 1])) return kDefinesBonus;
    if (_linkingVerbs.contains(tokens[i + 1])) best = kDescribesBonus;
  }
  return best;
}

List<bool> _hits(String sentence, List<Set<String>> concepts) {
  final stems = _docTerms(sentence).toSet();
  final ranges = _ranges(sentence);
  return [for (final c in concepts) _conceptHit(stems, ranges, c)];
}

class _Scored {
  final int i;
  final int score;
  final int covered;
  final String s;
  final Set<int> hitSet;

  _Scored(this.i, this.score, this.covered, this.s, this.hitSet);
}

/// Every sentence that hits at least one concept, best first. A hit in the
/// sentence counts twice a concept's weight; a hit in the chunk's section
/// heading adds it once.
List<_Scored> _scoreSentences(QaChunk chunk, List<Set<String>> concepts, List<int> weights, bool quantity, bool definition) {
  final titleHits = _hits(chunk.sectionTitle ?? '', concepts);
  final out = <_Scored>[];
  final sentences = splitSentences(chunk.chunkText);
  for (var i = 0; i < sentences.length; i++) {
    final sent = sentences[i];
    final hits = _hits(sent, concepts);
    if (!hits.contains(true)) continue;
    var score = 0;
    var covered = 0;
    for (var j = 0; j < weights.length; j++) {
      if (hits[j]) score += 2 * weights[j];
      if (titleHits[j]) score += weights[j];
      if (hits[j] || titleHits[j]) covered += weights[j];
    }
    if (quantity && _ml.hasMatch(sent)) score += kQuantityBonus;
    if (definition) score += _definitionBonus(sent, concepts);
    if (_code.hasMatch(sent)) score ~/= 2; // an example code line is not an explanation
    final hitSet = {for (var j = 0; j < concepts.length; j++) if (hits[j] || titleHits[j]) j};
    out.add(_Scored(i, score, covered, sent, hitSet));
  }
  out.sort((a, b) {
    final c = b.score.compareTo(a.score);
    if (c != 0) return c;
    return a.i.compareTo(b.i);
  });
  return out;
}

/// The best sentence verbatim, plus any sentence scoring exactly as well (the
/// rows of a dose table), in reading order. Outside dose questions, one more
/// sentence is added if it covers a part of the question the best one does
/// not and scores at least a third as well: 'Who is eligible?' gets 'given
/// only to children 1-59 months' beside 'younger ... not eligible'.
List<String> _bestSentences(List<_Scored> scored, bool quantity, {int limit = 3}) {
  if (scored.isEmpty) return [];
  final top = scored[0];
  final chosen = scored.where((x) => x.score == top.score).take(limit).toList();
  if (!quantity && chosen.length == 1) {
    for (final x in scored.skip(1)) {
      if (x.hitSet.difference(top.hitSet).isNotEmpty && x.score * 3 >= top.score) {
        chosen.add(x);
        break;
      }
    }
  }
  chosen.sort((a, b) => a.i.compareTo(b.i));
  return chosen.map((x) => x.s).toList();
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

AnswerResult _fallback([int confidencePct = 0, String message = kFallbackMessage]) => AnswerResult(
      answer: message,
      matched: false,
      confidence: confidencePct / 100,
      offline: false,
      sources: const [],
      suggestions: List<String>.from(kSuggestions),
    );

Set<String> _numbers(List<Set<String>> concepts) => {
      for (final c in concepts)
        for (final s in c)
          if (_isNumber(s)) s,
    };

/// % of [concepts] that share a stem with some concept in [other].
int _sharedPct(List<Set<String>> concepts, List<Set<String>> other) {
  var hit = 0;
  for (final c in concepts) {
    for (final o in other) {
      if (c.intersection(o).isNotEmpty) {
        hit++;
        break;
      }
    }
  }
  return _pct(hit, concepts.length);
}

/// The curated answer whose question (or one of its other wordings) best
/// matches, with its %, or null. Both questions must share at least
/// [kFaqMinPct] of their terms, each way, and exactly the same numbers: a
/// curated answer for an 8-month-old must never answer a 3-month-old.
(QaChunk, int)? matchFaq(String question, List<QaChunk> chunks) {
  final concepts = buildConcepts(question);
  if (concepts.isEmpty) return null;
  final numbers = _numbers(concepts);
  (QaChunk, int)? best;
  for (final ch in chunks) {
    for (final phrasing in ch.faqQuestions) {
      final other = buildConcepts(phrasing);
      if (other.isEmpty) continue;
      final otherNumbers = _numbers(other);
      if (otherNumbers.length != numbers.length || !otherNumbers.containsAll(numbers)) continue;
      final a = _sharedPct(concepts, other);
      final b = _sharedPct(other, concepts);
      final pct = a < b ? a : b;
      if (pct < kFaqMinPct) continue;
      if (best == null || pct > best.$2 || (pct == best.$2 && ch.id.compareTo(best.$1.id) < 0)) {
        best = (ch, pct);
      }
    }
  }
  return best;
}

/// Answers [question] from [chunks], or returns the strict fallback.
AnswerResult answerQuestion(String question, List<QaChunk> chunks, {int minCoveragePct = kDefaultMinCoveragePct}) {
  if (isGreeting(question)) return _fallback(0, kGreetingMessage);
  final faq = matchFaq(question, chunks);
  if (faq != null) {
    final (ch, pct) = faq;
    return AnswerResult(
      answer: ch.chunkText,
      matched: true,
      confidence: pct / 100,
      offline: false,
      sources: [_source(ch, splitSentences(ch.chunkText).first)],
      suggestions: const [],
    );
  }
  // A curated answer only makes sense next to its own question ("Give 4 ml"
  // answers "...an 8 month old?"), so it is never searched as a passage.
  final index = buildIndex([for (final ch in chunks) if (ch.faqQuestions.isEmpty) ch]);
  final concepts = buildConcepts(question);
  final ranked = _rank(concepts, index);
  final candidates = ranked.where((r) => r.matched > 0 && r.scoreI > 0).toList();
  if (candidates.isEmpty) return _fallback();

  // Words found in nearly every chunk ("AZM", "child") weigh little; rare
  // ones ("eligible", "vomit") decide which sentence answers the question.
  final weights = [for (final idf in _idfs(concepts, index.docs)) (idf * 1000 + 0.5).floor()];
  final total = weights.fold<int>(0, (a, b) => a + b);
  final quantity = isQuantityQuestion(question);
  final definition = isDefinitionQuestion(question);
  for (final r in candidates) {
    r.scored = _scoreSentences(r.doc.chunk, concepts, weights, quantity, definition);
    r.best = r.scored.isEmpty ? 0 : r.scored[0].score;
  }
  candidates.sort((a, b) {
    var c = b.best.compareTo(a.best);
    if (c != 0) return c;
    c = b.scoreI.compareTo(a.scoreI);
    if (c != 0) return c;
    return a.doc.chunk.id.compareTo(b.doc.chunk.id);
  });

  final best = candidates[0];
  if (best.scored.isEmpty) return _fallback();
  final coveragePct = _pct(best.scored[0].covered, total);
  if (coveragePct < minCoveragePct) return _fallback(coveragePct);

  final bestChunk = best.doc.chunk;
  final sentences = _bestSentences(best.scored, quantity);
  final sources = <AnswerSource>[_source(bestChunk, sentences[0])];

  for (final r in candidates.skip(1)) {
    if (sources.length >= 3) break;
    if (r.scored.isEmpty || r.best * 2 < best.best) continue;
    if (_pct(r.scored[0].covered, total) < minCoveragePct) continue;
    sources.add(_source(r.doc.chunk, r.scored[0].s));
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
