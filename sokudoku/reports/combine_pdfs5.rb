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
  page_text = "Page #{page_number}"
  
  # 新しいテキストオブジェクトを作成
  text_object = CombinePDF::PageText.new
  text_object.text = page_text
  text_object.font_size = 12
  text_object.font = 'Helvetica'
  
  # テキストの位置を設定
  text_object.position = [100, 700]  # ページの下部または任意の位置
  
  # ページにテキストを追加
  page << text_object
end

# 結合したPDFを保存
combined_pdf.save(output_file)

puts "PDFファイルの結合とページ番号の書き換えが完了しました: #{output_file}"
