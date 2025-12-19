import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.List;
import com.itextpdf.kernel.pdf.PdfDocument;
import com.itextpdf.kernel.pdf.PdfPage;
import com.itextpdf.kernel.pdf.PdfReader;
import com.itextpdf.kernel.pdf.PdfWriter;
import com.itextpdf.kernel.pdf.canvas.parser.PdfCanvasProcessor;
import com.itextpdf.kernel.pdf.canvas.parser.listener.SimpleTextExtractionStrategy;
import org.apache.commons.cli.*;

public class PDFMerger {
    public static void main(String[] args) {
        Options options = new Options();
        Option filesOption = new Option("f", "files", true, "List of PDF files to merge");
        filesOption.setRequired(true);
        filesOption.setArgs(Option.UNLIMITED_VALUES);
        options.addOption(filesOption);

        CommandLineParser parser = new DefaultParser();
        try {
            CommandLine cmd = parser.parse(options, args);
            String[] files = cmd.getOptionValues("files");
            merge(files);
        } catch (ParseException e) {
            System.out.println(e.getMessage());
            HelpFormatter formatter = new HelpFormatter();
            formatter.printHelp("pdf-merger", options);
            System.exit(1);
        }
    }

    public static void merge(String[] files) {
        PdfDocument mergedPdf = new PdfDocument(new PdfWriter("merged.pdf"));
        int pageNumber = 1;

        for (String file : files) {
            PdfDocument pdf = new PdfDocument(new PdfReader(file));
            for (int i = 1; i <= pdf.getNumberOfPages(); i++) {
                PdfPage page = pdf.getPage(i);
                page.setPageNumber(pageNumber);
                mergedPdf.addPage(page);
                pageNumber++;
            }
            pdf.close();
        }

        mergedPdf.close();
        System.out.println("PDF files merged and saved as 'merged.pdf'");
    }
}
```

このコードの説明は以下の通りです:

1. `com.itextpdf.kernel.pdf`パッケージからPDFファイルの操作に必要なクラスをインポートしています。
2. `org.apache.commons.cli`パッケージからコマンドライン引数の処理に必要なクラスをインポートしています。
3. `main`メソッドでは、コマンドライン引数を処理しています。`Option`オブジェクトを作成して`Options`に追加し、`CommandLineParser`を使ってコマンドライン引数を解析しています。
4. 引数の解析に成功した場合は`merge`メソッドを呼び出し、PDFファイルの結合を行っています。
5. `merge`メソッドでは、各PDFファイルをロードし、ページ番号を書き換えながら`PdfDocument`オブジェクトに追加していきます。
6. 最終的に、結合されたPDFファイルを`merged.pdf`として保存しています。

このコードを実行するには以下のようにします:

```
java -jar pdf-merger.jar -f file1.pdf file2.pdf file3.pdf
```

このコマンドを実行すると、指定したPDFファイルが結合され、ページ番号が1から順番に振り直された`merged.pdf`が生成されます。
