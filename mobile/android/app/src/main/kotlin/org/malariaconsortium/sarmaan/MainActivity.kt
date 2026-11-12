package org.malariaconsortium.sarmaan

import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

/**
 * Saving a file the learner keeps (the training certificate PDF): Android's own
 * "Save as" screen (ACTION_CREATE_DOCUMENT), which opens in Downloads, works on
 * every supported Android version and needs no storage permission. "open" shows
 * a saved file in the phone's PDF viewer.
 */
class MainActivity : FlutterActivity() {
    private var pendingResult: MethodChannel.Result? = null
    private var pendingBytes: ByteArray? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
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

    private fun finish(uri: String?, error: String?) {
        val result = pendingResult
        pendingResult = null
        pendingBytes = null
        if (error != null) result?.error(error, error, null) else result?.success(uri)
    }

    companion object {
        private const val CHANNEL = "org.malariaconsortium.sarmaan/files"
        private const val SAVE_REQUEST = 4207
    }
}
