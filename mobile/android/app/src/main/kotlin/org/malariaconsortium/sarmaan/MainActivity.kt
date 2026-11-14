package org.malariaconsortium.sarmaan

import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioManager
import android.net.Uri
import android.os.Build
import android.os.StatFs
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

/**
 * Saving a file the learner keeps (the training certificate PDF): Android's own
 * "Save as" screen (ACTION_CREATE_DOCUMENT), which opens in Downloads, works on
 * every supported Android version and needs no storage permission. "open" shows
 * a saved file in the phone's PDF viewer.
 *
 * The device channel answers "osVersion" (for example "Android 14 (API 34)") for
 * the admin portal's device list, "freeBytes" (free storage) before a video download, and
 * "openTtsSettings" (text-to-speech settings, to install an English voice for Read aloud). No model, hardware id, IMEI or phone number is read.
 */
class MainActivity : FlutterActivity() {
    private var pendingResult: MethodChannel.Result? = null
    private var pendingBytes: ByteArray? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, DEVICE_CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "osVersion" -> result.success("Android ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})")
                // Free space where videos are saved, checked before a download starts.
                "freeBytes" -> result.success(StatFs(filesDir.absolutePath).availableBytes)
                // Read aloud: where the learner installs an English voice.
                "openTtsSettings" -> {
                    val opened = listOf(Intent("com.android.settings.TTS_SETTINGS"), Intent(android.provider.Settings.ACTION_SETTINGS))
                        .any { intent ->
                            try {
                                startActivity(intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)); true
                            } catch (e: ActivityNotFoundException) {
                                false
                            }
                        }
                    result.success(opened)
                }
                else -> result.notImplemented()
            }
        }
        // Read aloud holds audio focus with a listener, so a phone call or another app
        // taking the audio stops the reading (flutter_tts asks for focus without one).
        val audioChannel = MethodChannel(flutterEngine.dartExecutor.binaryMessenger, AUDIO_CHANNEL)
        audioChannel.setMethodCallHandler { call, result ->
            when (call.method) {
                "requestFocus" -> result.success(requestReadAloudFocus(audioChannel))
                "abandonFocus" -> {
                    abandonReadAloudFocus()
                    result.success(true)
                }
                else -> result.notImplemented()
            }
        }
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "save" -> {
                    val name = call.argument<String>("name")
                    val mime = call.argument<String>("mime")
                    val bytes = call.argument<ByteArray>("bytes")
                    if (name == null || mime == null || bytes == null) {
                        result.error("bad_args", "name, mime and bytes are required", null)
                    } else if (pendingResult != null) {
                        result.error("busy", "A save is already in progress", null)
                    } else {
                        pendingResult = result
                        pendingBytes = bytes
                        val intent = Intent(Intent.ACTION_CREATE_DOCUMENT).apply {
                            addCategory(Intent.CATEGORY_OPENABLE)
                            type = mime
                            putExtra(Intent.EXTRA_TITLE, name)
                        }
                        try {
                            startActivityForResult(intent, SAVE_REQUEST)
                        } catch (e: ActivityNotFoundException) {
                            finish(null, "no_picker")
                        }
                    }
                }
                "open" -> {
                    val uri = call.argument<String>("uri")
                    val mime = call.argument<String>("mime") ?: "application/pdf"
                    try {
                        startActivity(Intent(Intent.ACTION_VIEW).apply {
                            setDataAndType(Uri.parse(uri), mime)
                            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                        })
                        result.success(true)
                    } catch (e: ActivityNotFoundException) {
                        result.success(false) // no app on the phone opens this type
                    }
                }
                else -> result.notImplemented()
            }
        }
    }

    @Deprecated("Deprecated in Java")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != SAVE_REQUEST) return
        val uri = data?.data
        if (resultCode != Activity.RESULT_OK || uri == null) {
            finish(null, null) // the learner cancelled
            return
        }
        try {
            contentResolver.openOutputStream(uri, "w")?.use { it.write(pendingBytes) }
                ?: throw IllegalStateException("cannot write")
            finish(uri.toString(), null)
        } catch (e: Exception) {
            finish(null, "write_failed")
        }
    }

    private var focusRequest: AudioFocusRequest? = null
    private var focusListener: AudioManager.OnAudioFocusChangeListener? = null

    private fun requestReadAloudFocus(channel: MethodChannel): Boolean {
        val audio = getSystemService(Context.AUDIO_SERVICE) as AudioManager
        abandonReadAloudFocus()
        val listener = AudioManager.OnAudioFocusChangeListener { change ->
            if (change == AudioManager.AUDIOFOCUS_LOSS || change == AudioManager.AUDIOFOCUS_LOSS_TRANSIENT) {
                runOnUiThread { channel.invokeMethod("focusLost", null) }
            }
        }
        focusListener = listener
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val request = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK)
                .setAudioAttributes(AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_ASSISTANCE_ACCESSIBILITY)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
                .setOnAudioFocusChangeListener(listener)
                .build()
            focusRequest = request
            audio.requestAudioFocus(request) == AudioManager.AUDIOFOCUS_REQUEST_GRANTED
        } else {
            @Suppress("DEPRECATION")
            audio.requestAudioFocus(listener, AudioManager.STREAM_MUSIC, AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK) ==
                AudioManager.AUDIOFOCUS_REQUEST_GRANTED
        }
    }

    private fun abandonReadAloudFocus() {
        val audio = getSystemService(Context.AUDIO_SERVICE) as AudioManager
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            focusRequest?.let { audio.abandonAudioFocusRequest(it) }
        } else {
            @Suppress("DEPRECATION")
            focusListener?.let { audio.abandonAudioFocus(it) }
        }
        focusRequest = null
        focusListener = null
    }

    private fun finish(uri: String?, error: String?) {
        val result = pendingResult
        pendingResult = null
        pendingBytes = null
        if (error != null) result?.error(error, error, null) else result?.success(uri)
    }

    companion object {
        private const val CHANNEL = "org.malariaconsortium.sarmaan/files"
        private const val DEVICE_CHANNEL = "org.malariaconsortium.sarmaan/device"
        private const val AUDIO_CHANNEL = "org.malariaconsortium.sarmaan/audio"
        private const val SAVE_REQUEST = 4207
    }
}
