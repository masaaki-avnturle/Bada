require 'combine_pdf'

# 結合するPDFファイルリスト
pdf_files = ['entrade.pdf', 'esist.pdf', 'zeta_dalanversian.pdf']
output_file = 'merged.pdf'

# PDFファイルを読み込み
combined_pdf = CombinePDF.new

pdf_files.each do |file|
  pdf = CombinePDF.load(file)
  combined_pdf << pdf
end

# ページ番号を追加
combined_pdf.pages.each_with_index do |page, index|
  page_number = index + 1
  page_text = "#{page_number}"
  
  # ページにテキストを追加
  page.text << page_text
  page.text_style = { size: 12, font: 'Helvetica' }
  page.text_position = [100, 700]  # テキストの位置を設定
end

# 結合したPDFを保存
combined_pdf.save(output_file)

puts "PDFファイルの結合とページ番号の書き換えが完了しました: #{output_file}"
