# frozen_string_literal: true

# Bada::Web demo — a Rails-equivalent MVC blog in pure Ruby on Ω::DATABASE.
#
#   ruby -Ilib examples/web_demo.rb          # dispatch requests in-process
#   ruby -Ilib examples/web_demo.rb serve    # boot the HTTP server on :3000
#
$LOAD_PATH.unshift(File.expand_path("../lib", __dir__))
require "bada"

app = Bada::Web.demo_app

if ARGV.first == "serve"
  Bada::Web::Server.new(app, port: 3000).start
else
  puts "GET /        -> #{app.get('/').status}"
  res = app.post("/posts",
                 headers: { "Content-Type" => "application/x-www-form-urlencoded" },
                 body: "post[title]=Bada&post[body]=Rails-equivalent on Omega::DATABASE")
  puts "POST /posts  -> #{res.status} (Location: #{res['Location']})"
  id = res["Location"].split("/").last
  puts "GET /posts/#{id} ->"
  puts app.get("/posts/#{id}").body.lines.grep(/<h1>|<p>/).map(&:strip)

  puts "\nΩ::DATABASE (Akashic) now holds #{Bada::Web::Model.akashic.size} manifold points:"
  Bada::Web::Model.akashic.each { |t| puts "  #{t.key}  Ξ=#{format('%.4f', t.stats[:invariant])}  #{t.text[0, 40]}" }
end
