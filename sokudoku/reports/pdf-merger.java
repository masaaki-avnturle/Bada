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
