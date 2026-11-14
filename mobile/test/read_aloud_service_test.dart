import 'dart:async';
import 'dart:convert';

import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarmaan_eplaybook/db/local_database.dart';
import 'package:sarmaan_eplaybook/services/narration_builder.dart';
import 'package:sarmaan_eplaybook/services/read_aloud_service.dart';

/// Read aloud: voice choice, reading order, pause/resume, quiz stops, speed,
/// interruptions and one module at a time, against a fake speech engine.

class FakeEngine implements SpeechEngine {
  List<Map<String, String>> voiceList;
  bool failVoices;
  final spoken = <String>[];
  final rates = <double>[];
  Map<String, String>? voice;
  Completer<void>? _current;
  bool hold = false; // keep each utterance "speaking" until release()

  FakeEngine(this.voiceList, {this.failVoices = false});

  @override
  Future<List<Map<String, String>>> voices() async {
    if (failVoices) throw Exception('no engine');
    return voiceList;
  }

  @override
  Future<int?> maxInputLength() async => 4000;

  @override
  Future<void> setVoice(Map<String, String> v) async => voice = v;

  @override
  Future<void> setRate(double rate) async => rates.add(rate);

  @override
  Future<void> speak(String text) async {
    spoken.add(text);
    if (!hold) return;
    _current = Completer<void>();
    await _current!.future;
  }

  void release() => _current?.complete();

  @override
  Future<void> stop() async {
    if (_current != null && !_current!.isCompleted) _current!.complete();
  }
}

class FakeFocus implements AudioFocus {
  final lostController = StreamController<void>.broadcast();
  int requests = 0, abandons = 0;
  @override
  Stream<void> get lost => lostController.stream;
  @override
  Future<void> request() async => requests++;
  @override
  Future<void> abandon() async => abandons++;
}

const _enGbLocal = {'name': 'en-gb-x-gba-local', 'locale': 'en-GB', 'network_required': '0'};
const _enNgNetwork = {'name': 'en-ng-x-tfn-network', 'locale': 'en-NG', 'network_required': '1'};
const _enNgLocal = {'name': 'en-ng-x-tfn-local', 'locale': 'en-NG', 'network_required': '0'};
const _enUsLocal = {'name': 'en-us-x-sfg-local', 'locale': 'en-US', 'network_required': '0'};
const _haLocal = {'name': 'ha-ng-local', 'locale': 'ha-NG', 'network_required': '0'};

const _chunks = [
  NarrationChunk('', 'Module one.'),
  NarrationChunk('s1', 'Heading.'),
  NarrationChunk('s2', 'Part one of a long section.'),
  NarrationChunk('s2', 'Part two of a long section.'),
  NarrationChunk('q1', '', quizStop: true),
  NarrationChunk('s3', 'After the quiz.'),
];

Future<void> _settle() async {
  for (var i = 0; i < 20; i++) {
    await Future<void>.delayed(Duration.zero);
  }
}

void main() {
  late LocalDatabase db;
  setUp(() => db = LocalDatabase.forTesting(NativeDatabase.memory()));
  tearDown(() => db.close());

  ReadAloudService service(FakeEngine e, [FakeFocus? f]) => ReadAloudService(engine: e, focus: f ?? FakeFocus(), db: db);

  test('Read aloud is offered for English only', () {
    expect(readAloudAllowedFor('en'), isTrue);
    expect(readAloudAllowedFor(null), isTrue, reason: 'English is the default content language');
    expect(readAloudAllowedFor('ha'), isFalse);
    expect(readAloudAllowedFor('fr'), isFalse);
  });

  test('voice choice: offline first, then en-NG, en-GB, any English; never another language', () {
    expect(pickEnglishVoice([_enUsLocal, _enGbLocal, _enNgLocal, _enNgNetwork]), _enNgLocal);
    expect(pickEnglishVoice([_enUsLocal, _enGbLocal, _enNgNetwork]), _enGbLocal, reason: 'an offline voice works in the field');
    expect(pickEnglishVoice([_enUsLocal, _haLocal]), _enUsLocal);
    expect(pickEnglishVoice([_enNgNetwork, _haLocal]), _enNgNetwork, reason: 'a network voice only when no offline one');
    expect(pickEnglishVoice([_haLocal]), isNull);
    expect(pickEnglishVoice([{'name': 'English', 'locale': 'en_GB'}]), isNotNull, reason: 'iOS-style locale');
  });

  test('the chosen voice is saved in app_settings and reused', () async {
    final e = FakeEngine([_enUsLocal, _enGbLocal]);
    expect(await service(e).ensureVoice(), VoiceCheck.ready);
    expect(e.voice!['name'], _enGbLocal['name']);
    expect(jsonDecode((await db.getSetting(kReadAloudVoiceKey))!)['name'], _enGbLocal['name']);
    final e2 = FakeEngine([_enNgLocal, _enGbLocal]); // an en-NG voice installed later: the saved one stays
    await service(e2).ensureVoice();
    expect(e2.voice!['name'], _enGbLocal['name']);
  });

  test('no English voice or no engine: a clear result, nothing is spoken', () async {
    for (final e in [FakeEngine([_haLocal]), FakeEngine(const [], failVoices: true)]) {
      final s = service(e);
      expect(await s.start('M', _chunks), VoiceCheck.noEnglishVoice);
      await _settle();
      expect(e.spoken, isEmpty);
      expect(s.status, ReadAloudStatus.idle);
    }
  });

  test('reads in order, stops at the quiz, and Play continues after it', () async {
    final e = FakeEngine([_enGbLocal]);
    final s = service(e);
    await s.start('M', _chunks);
    await _settle();
    expect(e.spoken, ['Module one.', 'Heading.', 'Part one of a long section.', 'Part two of a long section.']);
    expect(s.status, ReadAloudStatus.quizPause);
    await s.resume();
    await _settle();
    expect(e.spoken.last, 'After the quiz.');
    expect(s.status, ReadAloudStatus.idle, reason: 'the end of the module');
  });

  test('pause, then Play, starts again at the beginning of the current section', () async {
    final e = FakeEngine([_enGbLocal])..hold = true;
    final s = service(e);
    await s.start('M', _chunks, fromSection: 's2');
    await _settle();
    e.release(); // part one done
    await _settle();
    expect(e.spoken.last, 'Part two of a long section.');
    expect(s.currentSectionId, 's2');
    await s.pause();
    expect(s.status, ReadAloudStatus.paused);
    await s.resume();
    await _settle();
    expect(e.spoken.last, 'Part one of a long section.', reason: 'from the start of the section, not mid-way');
  });

  test('next, previous and tapping a section move the reading', () async {
    final e = FakeEngine([_enGbLocal])..hold = true;
    final s = service(e);
    await s.start('M', _chunks);
    await _settle();
    await s.next();
    await _settle();
    expect(e.spoken.last, 'Heading.');
    await s.next();
    await _settle();
    expect(e.spoken.last, 'Part one of a long section.');
    await s.previous();
    await _settle();
    expect(e.spoken.last, 'Heading.');
    await s.jumpToSection('s3');
    await _settle();
    expect(e.spoken.last, 'After the quiz.');
    expect(s.currentSectionId, 's3');
    await s.stop();
  });

  test('speed: three steps, remembered, mapped per platform', () async {
    final e = FakeEngine([_enGbLocal]);
    final s = service(e);
    await s.setSpeed(ReadAloudSpeed.fast);
    expect(await db.getSetting(kReadAloudSpeedKey), 'fast');
    final again = service(e);
    await again.start('M', const [NarrationChunk('', 'Hi.')]);
    await _settle();
    expect(again.speed, ReadAloudSpeed.fast);
    expect(e.rates.last, speechRate(ReadAloudSpeed.fast, ios: false));
    expect([for (final sp in ReadAloudSpeed.values) speechRate(sp, ios: false)], [0.375, 0.5, 0.625],
        reason: 'flutter_tts doubles the Android value: 0.75x, 1x, 1.25x');
    expect([for (final sp in ReadAloudSpeed.values) speechRate(sp, ios: true)], [0.42, 0.5, 0.56]);
    expect(ReadAloudSpeed.fast.next, ReadAloudSpeed.slow);
  });

  test('another app taking the audio (a phone call) pauses the reading', () async {
    final e = FakeEngine([_enGbLocal])..hold = true;
    final f = FakeFocus();
    final s = service(e, f);
    await s.start('M', _chunks);
    await _settle();
    expect(f.requests, 1);
    f.lostController.add(null);
    await _settle();
    expect(s.status, ReadAloudStatus.paused);
    expect(f.abandons, greaterThan(0));
  });

  test('only one module reads at a time', () async {
    final e = FakeEngine([_enGbLocal])..hold = true;
    final s = service(e);
    await s.start('A', _chunks);
    await _settle();
    await s.start('B', const [NarrationChunk('', 'Module B.')]);
    await _settle();
    expect(s.moduleId, 'B');
    expect(e.spoken.last, 'Module B.');
    await s.stop();
    expect(s.status, ReadAloudStatus.idle);
    expect(s.moduleId, isNull);
  });
}
