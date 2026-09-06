use strict;
use warnings;
use CAM::PDF;

sub merge_pdfs {
    my ($output_file, @input_files) = @_;
    my $pdf = CAM::PDF->new();

    my $page_count = 0;

    # 各PDFファイルを読み込み、結合する
    foreach my $input_file (@input_files) {
        my $src_pdf = CAM::PDF->new($input_file);
        for my $i (1 .. $src_pdf->numPages()) {
            my $page = $src_pdf->getPage($i);
            $pdf->addPage($page);
            $page_count++;
        }
    }

    # ページ番号を設定
    for my $i (1 .. $page_count) {
        my $page = $pdf->getPage($i);
        my $text = "$i";  # ページ番号

        # ページ番号をページの下部に描画
        $page->setText($text, 500, 10, { 
            'Font' => 'Helvetica', 
            'FontSize' => 12 
        });
    }

    # 結合したPDFを保存
    $pdf->save($output_file);
}

# メイン処理
if (@ARGV < 2) {
    die "Usage: perl merge_pdfs.pl output.pdf input1.pdf input2.pdf [...]\n";
}

my $output_file = shift @ARGV;
merge_pdfs($output_file, @ARGV);
