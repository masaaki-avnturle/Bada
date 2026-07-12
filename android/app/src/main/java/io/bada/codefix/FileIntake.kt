package io.bada.codefix

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import com.tom_roush.pdfbox.android.PDFBoxResourceLoader
import com.tom_roush.pdfbox.pdmodel.PDDocument
import com.tom_roush.pdfbox.text.PDFTextStripper

/**
 * Shared file intake for uploaded documents (source code and PDFs).
 * PDFs are text-extracted with PdfBox-Android; everything else is read as
 * UTF-8. Used by both the code-fixer and the AGI report ingestion.
 */
object FileIntake {

    fun displayName(context: Context, uri: Uri): String {
        context.contentResolver.query(uri, null, null, null, null)?.use { c ->
            val idx = c.getColumnIndex(OpenableColumns.DISPLAY_NAME)
            if (idx >= 0 && c.moveToFirst()) return c.getString(idx)
        }
        return uri.lastPathSegment ?: "uploaded"
    }

    fun extractText(context: Context, uri: Uri, name: String): String {
        val type = context.contentResolver.getType(uri) ?: ""
        val isPdf = name.lowercase().endsWith(".pdf") || type == "application/pdf"
        context.contentResolver.openInputStream(uri).use { input ->
            requireNotNull(input) { "ストリームを開けません" }
            return if (isPdf) {
                PDFBoxResourceLoader.init(context.applicationContext)
                PDDocument.load(input).use { doc -> PDFTextStripper().getText(doc) }
            } else {
                input.readBytes().toString(Charsets.UTF_8)
            }
        }
    }
}
