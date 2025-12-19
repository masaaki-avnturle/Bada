use strict;
use warnings;
use CAM::PDF;

# 結合するPDFファイルリスト
my @pdf_files = ('entrade.pdf', 'esist.pdf', 'zeta_dalanversian.pdf');
my $output_file = 'merged.pdf';

# PDFファイルを結合
my $pdf = CAM::PDF->new();
$pdf->addPage($_) for @pdf_files;

# ページ番号を変更
my $page_count = 1;
foreach my $file (@pdf_files) {
    my $pdf_part = CAM::PDF->new($file);
    my $num_pages = $pdf_part->numPages();
    
    for (my $i = 1; $i <= $num_pages; $i++) {
        my $page = $pdf_part->getPage($i);
        my $text = "Page $page_count";  # 新しいページ番号
        $page->{Contents} .= "\nBT /F1 12 Tf 100 700 Td ($text) Tj ET";  # ページ番号を追加
        $pdf->addPage($page);
        $page_count++;
    }
}

# 結合したPDFを保存
$pdf->clean();
$pdf->saveAs($output_file);

print "PDFファイルの結合とページ番号の書き換えが完了しました: $output_file\n";
