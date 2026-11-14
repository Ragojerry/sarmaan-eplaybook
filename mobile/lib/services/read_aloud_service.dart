import 'dart:async';
import 'dart:convert';
import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_tts/flutter_tts.dart';

import '../db/local_database.dart';
import '../offline/content_sync_service.dart' show localDatabaseProvider;
import 'narration_builder.dart';

/// "Read aloud" in the module reader: the phone's own text-to-speech engine reads
/// the narration (narration_builder.dart), English only for now, offline once an
/// English voice is installed. Screens never call flutter_tts directly.
///
/// Reading is a list of chunks played one after another. Pause is stop + resume
/// from the start of the current section (pause support differs between Android
/// versions; this works everywhere). A quiz block pauses reading; Play continues
/// after it. One module reads at a time (one shared service).

/// Read aloud is offered only when the learner's content language is English:
/// English text is never read with another language selected, or the reverse.
bool readAloudAllowedFor(String? languageCode) => (languageCode ?? 'en').toLowerCase() == 'en';

enum ReadAloudSpeed { slow, normal, fast }

extension ReadAloudSpeedLabel on ReadAloudSpeed {
  String get label => switch (this) { ReadAloudSpeed.slow => '0.75x', ReadAloudSpeed.normal => '1x', ReadAloudSpeed.fast => '1.25x' };
  ReadAloudSpeed get next => ReadAloudSpeed.values[(index + 1) % ReadAloudSpeed.values.length];
}

/// flutter_tts rates differ by platform. Android: the plugin doubles the value, so
/// 0.375 / 0.5 / 0.625 are Android's 0.75x / 1x / 1.25x exactly. iOS: 0.5 is
/// AVSpeech's normal rate and the scale is not linear, so the steps are smaller.
double speechRate(ReadAloudSpeed speed, {required bool ios}) => switch ((speed, ios)) {
      (ReadAloudSpeed.slow, false) => 0.375,
      (ReadAloudSpeed.normal, false) => 0.5,
      (ReadAloudSpeed.fast, false) => 0.625,
      (ReadAloudSpeed.slow, true) => 0.42,
      (ReadAloudSpeed.normal, true) => 0.5,
      (ReadAloudSpeed.fast, true) => 0.56,
    };

/// The English voice to use: offline (local) voices first, because the app works
/// in the field without data; among them, and then among network voices,
/// en-NG, then en-GB, then any English. Null when the phone has no English voice.
Map<String, String>? pickEnglishVoice(List<Map<String, String>> voices) {
  String locale(Map<String, String> v) => (v['locale'] ?? '').replaceAll('_', '-').toLowerCase();
  bool online(Map<String, String> v) => v['network_required'] == '1' || (v['name'] ?? '').toLowerCase().contains('network');
  final english = voices.where((v) => locale(v) == 'en' || locale(v).startsWith('en-')).toList();
  for (final offline in [true, false]) {
    for (final want in ['en-ng', 'en-gb', 'en']) {
      for (final v in english) {
        if (online(v) == offline) continue;
        if (want == 'en' || locale(v) == want) return v;
      }
    }
  }
  return null;
}

// ---- what the service talks to (real ones at the bottom; fakes in tests) ----

abstract class SpeechEngine {
  /// Voices as the engine lists them (name, locale, and on Android network_required).
  Future<List<Map<String, String>>> voices();
  Future<int?> maxInputLength();
  Future<void> setVoice(Map<String, String> voice);
  Future<void> setRate(double rate);

  /// Completes when the text has been spoken, or when [stop] cuts it short.
  Future<void> speak(String text);
  Future<void> stop();
}

abstract class AudioFocus {
  Future<void> request();
  Future<void> abandon();

  /// Another app (a phone call, music) took the audio.
  Stream<void> get lost;
}

enum ReadAloudStatus { idle, reading, paused, quizPause }

enum VoiceCheck { ready, noEnglishVoice }

const kReadAloudVoiceKey = 'read_aloud_voice';
const kReadAloudSpeedKey = 'read_aloud_speed';

class ReadAloudService extends ChangeNotifier {
  final SpeechEngine engine;
  final AudioFocus focus;
  final LocalDatabase db;
  final bool ios;

  ReadAloudService({required this.engine, required this.focus, required this.db, this.ios = false}) {
    _focusLost = focus.lost.listen((_) => pause());
  }

  late final StreamSubscription<void> _focusLost;
  ReadAloudStatus status = ReadAloudStatus.idle;
  ReadAloudSpeed speed = ReadAloudSpeed.normal;
  Map<String, String>? voice;
  String? moduleId; // the module reading (only one at a time)
  List<NarrationChunk> _chunks = const [];
  int _index = 0;
  int _generation = 0; // bumped by every stop/pause/jump: a running loop sees it and ends
  bool _settingsLoaded = false;

  @override
  void dispose() {
    _focusLost.cancel();
    super.dispose();
  }

  /// The section being read (highlighted and kept in view by the reader).
  String? get currentSectionId => status == ReadAloudStatus.idle || _chunks.isEmpty || _index >= _chunks.length ? null : _chunks[_index].sectionId;

  bool get active => status != ReadAloudStatus.idle;

  Future<void> _loadSettings() async {
    if (_settingsLoaded) return;
    _settingsLoaded = true;
    final s = await db.getSetting(kReadAloudSpeedKey);
    speed = ReadAloudSpeed.values.firstWhere((v) => v.name == s, orElse: () => ReadAloudSpeed.normal);
  }

  /// Finds (first time) or re-checks the saved English voice. A phone without a
  /// text-to-speech engine or without an English voice gets noEnglishVoice.
  Future<VoiceCheck> ensureVoice() async {
    await _loadSettings();
    List<Map<String, String>> all;
    try {
      all = await engine.voices();
    } catch (_) {
      all = const [];
    }
    Map<String, String>? chosen;
    final saved = await db.getSetting(kReadAloudVoiceKey);
    if (saved != null && saved.isNotEmpty) {
      try {
        final s = Map<String, String>.from(jsonDecode(saved) as Map);
        chosen = all.where((v) => v['name'] == s['name'] && v['locale'] == s['locale']).firstOrNull;
      } catch (_) {}
    }
    chosen ??= pickEnglishVoice(all);
    if (chosen == null) {
      voice = null;
      return VoiceCheck.noEnglishVoice;
    }
    if (voice == null || voice!['name'] != chosen['name']) {
      try {
        await engine.setVoice({'name': chosen['name'] ?? '', 'locale': chosen['locale'] ?? ''});
      } catch (_) {
        return VoiceCheck.noEnglishVoice;
      }
      voice = chosen;
      await db.setSetting(kReadAloudVoiceKey, jsonEncode({'name': chosen['name'], 'locale': chosen['locale']}));
    }
    return VoiceCheck.ready;
  }

  /// The longest text the engine takes at once (3,500 characters when it cannot say).
  Future<int> maxChunkLength() async {
    try {
      final n = await engine.maxInputLength();
      if (n != null && n > 200) return n < kDefaultMaxSpeechInput ? n : kDefaultMaxSpeechInput;
    } catch (_) {}
    return kDefaultMaxSpeechInput;
  }

  /// Starts reading [chunks] of [module] (stopping any other module), from
  /// [fromSection] if given.
  Future<VoiceCheck> start(String module, List<NarrationChunk> chunks, {String? fromSection}) async {
    final check = await ensureVoice();
    if (check != VoiceCheck.ready) return check;
    await stop();
    moduleId = module;
    _chunks = chunks;
    _index = fromSection == null ? 0 : _firstOf(fromSection);
    unawaited(_play());
    return check;
  }

  Future<void> pause() async {
    if (status != ReadAloudStatus.reading) return;
    _generation++;
    _index = _sectionStart(_index);
    status = ReadAloudStatus.paused;
    notifyListeners();
    await engine.stop();
    await focus.abandon();
  }

  /// Play after Pause (from the start of that section) or after a quiz.
  Future<void> resume() async {
    if (status != ReadAloudStatus.paused && status != ReadAloudStatus.quizPause) return;
    unawaited(_play());
  }

  Future<void> next() => _jumpTo(_nextSectionStart(_index));

  Future<void> previous() {
    final here = _sectionStart(_index);
    return _jumpTo(_sectionStart(here == 0 ? 0 : here - 1));
  }

  /// The learner tapped a section while reading: continue from there.
  Future<void> jumpToSection(String sectionId) => _jumpTo(_firstOf(sectionId));

  Future<void> setSpeed(ReadAloudSpeed s) async {
    speed = s;
    await db.setSetting(kReadAloudSpeedKey, s.name);
    if (status == ReadAloudStatus.reading) {
      await _jumpTo(_sectionStart(_index)); // the rest of this section at the new speed
    } else {
      notifyListeners();
    }
  }

  /// Leaving the reader, opening a quiz, the app going to the background.
  Future<void> stop() async {
    _generation++;
    final wasActive = status != ReadAloudStatus.idle;
    status = ReadAloudStatus.idle;
    moduleId = null;
    if (wasActive) notifyListeners();
    await engine.stop();
    await focus.abandon();
  }

  Future<void> _jumpTo(int index) async {
    if (status == ReadAloudStatus.idle || _chunks.isEmpty) return;
    _index = index.clamp(0, _chunks.length - 1);
    if (status == ReadAloudStatus.reading) {
      _generation++;
      await engine.stop();
      unawaited(_play());
    } else {
      status = ReadAloudStatus.paused; // a quiz pause moved elsewhere is an ordinary pause
      notifyListeners();
    }
  }

  Future<void> _play() async {
    final gen = ++_generation;
    status = ReadAloudStatus.reading;
    notifyListeners();
    await focus.request();
    await engine.setRate(speechRate(speed, ios: ios));
    while (gen == _generation && _index < _chunks.length) {
      final chunk = _chunks[_index];
      if (chunk.quizStop) {
        _index++; // Play continues after the quiz
        status = ReadAloudStatus.quizPause;
        notifyListeners();
        await focus.abandon();
        return;
      }
      await engine.speak(chunk.text);
      if (gen != _generation) return; // stopped, paused or moved while speaking
      _index++;
      notifyListeners();
    }
    if (gen == _generation) {
      // The end of the module.
      status = ReadAloudStatus.idle;
      moduleId = null;
      notifyListeners();
      await focus.abandon();
    }
  }

  int _firstOf(String sectionId) {
    final i = _chunks.indexWhere((c) => c.sectionId == sectionId);
    return i < 0 ? 0 : i;
  }

  int _sectionStart(int i) {
    if (_chunks.isEmpty) return 0;
    var j = i.clamp(0, _chunks.length - 1);
    final id = _chunks[j].sectionId;
    while (j > 0 && _chunks[j - 1].sectionId == id && !_chunks[j - 1].quizStop) {
      j--;
    }
    return j;
  }

  int _nextSectionStart(int i) {
    if (_chunks.isEmpty) return 0;
    var j = i.clamp(0, _chunks.length - 1);
    final id = _chunks[j].sectionId;
    while (j < _chunks.length && _chunks[j].sectionId == id) {
      j++;
    }
    return j >= _chunks.length ? _chunks.length - 1 : j;
  }
}

// ---- the real engine, audio focus and settings shortcut ----

class FlutterTtsEngine implements SpeechEngine {
  final FlutterTts _tts = FlutterTts();
  bool _ready = false;

  Future<void> _init() async {
    if (_ready) return;
    _ready = true;
    await _tts.awaitSpeakCompletion(true);
    if (!kIsWeb && Platform.isIOS) {
      // Playback category: speech plays with the silent switch on.
      await _tts.setSharedInstance(true);
      await _tts.setIosAudioCategory(IosTextToSpeechAudioCategory.playback,
          [IosTextToSpeechAudioCategoryOptions.duckOthers], IosTextToSpeechAudioMode.spokenAudio);
    }
  }

  @override
  Future<List<Map<String, String>>> voices() async {
    await _init();
    final raw = await _tts.getVoices;
    if (raw is! List) return const [];
    return [
      for (final v in raw)
        if (v is Map) {for (final e in v.entries) e.key.toString(): e.value?.toString() ?? ''},
    ];
  }

  @override
  Future<int?> maxInputLength() async {
    if (kIsWeb || !Platform.isAndroid) return null;
    return _tts.getMaxSpeechInputLength;
  }

  @override
  Future<void> setVoice(Map<String, String> voice) async {
    await _init();
    await _tts.setVoice(voice);
  }

  @override
  Future<void> setRate(double rate) => _tts.setSpeechRate(rate);

  @override
  Future<void> speak(String text) async {
    await _init();
    await _tts.speak(text); // focus handled by AudioFocus, which hears when it is lost
  }

  @override
  Future<void> stop() async {
    await _tts.stop();
  }
}

/// Android audio focus with a listener (MainActivity, channel ".../audio"): a phone
/// call or another app taking the audio stops reading. Elsewhere it does nothing.
class ChannelAudioFocus implements AudioFocus {
  static const _channel = MethodChannel('org.malariaconsortium.sarmaan/audio');
  final _lost = StreamController<void>.broadcast();

  ChannelAudioFocus() {
    _channel.setMethodCallHandler((call) async {
      if (call.method == 'focusLost') _lost.add(null);
    });
  }

  @override
  Stream<void> get lost => _lost.stream;

  @override
  Future<void> request() async {
    try {
      await _channel.invokeMethod('requestFocus');
    } catch (_) {}
  }

  @override
  Future<void> abandon() async {
    try {
      await _channel.invokeMethod('abandonFocus');
    } catch (_) {}
  }
}

/// Opens the phone's text-to-speech settings (to install an English voice).
Future<bool> openVoiceSettings() async {
  try {
    return await const MethodChannel('org.malariaconsortium.sarmaan/device').invokeMethod<bool>('openTtsSettings') ?? false;
  } catch (_) {
    return false;
  }
}

final readAloudServiceProvider = ChangeNotifierProvider<ReadAloudService>((ref) => ReadAloudService(
      engine: FlutterTtsEngine(),
      focus: ChannelAudioFocus(),
      db: ref.read(localDatabaseProvider),
      ios: !kIsWeb && Platform.isIOS,
    ));
