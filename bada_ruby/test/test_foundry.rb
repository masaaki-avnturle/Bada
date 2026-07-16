# frozen_string_literal: true

require_relative "helper" if File.exist?(File.expand_path("helper.rb", __dir__))
$LOAD_PATH.unshift(File.expand_path("../lib", __dir__))
require "minitest/autorun" rescue nil
require "bada"

# Minimal test harness that also works without minitest.
if defined?(Minitest)
  class TestFoundry < Minitest::Test
    EQS = [
      "β(p,q) = Γ(p)Γ(q)/Γ(p+q)",
      "ζ(s) = β(p,q)/logx = x·logx",
      "□ = cos(ix·logx) - i·sin(ix·logx)"
    ].freeze

    def test_meaning_has_geometry_and_archetype
      m = Bada::Foundry.meaning(EQS[0], index: 0)
      assert m[:xi].finite?, "Xi must be finite"
      assert Bada::Thurston::GEOMETRIES.map { |g| g[:name] }.include?(m[:geometry])
      assert m[:archetype].is_a?(String)
      assert m[:branches] >= 1
    end

    def test_forge_produces_runnable_bada_and_app
      f = Bada::Foundry.forge(EQS, app_name: "TestApp")
      assert_equal "TestApp", f[:spec][:name]
      assert_equal 3, f[:spec][:module_count]
      # Generated Bada source must run through the interpreter without error.
      out = Bada::Foundry.run_bada(f[:bada_source])
      assert out.length >= 3, "Bada program should produce output lines"
      # Child app HTML must be a self-contained runnable document.
      assert_includes f[:app_html], "<!DOCTYPE html>"
      assert_includes f[:app_html], "MODULES="
      assert_includes f[:app_html], "requestAnimationFrame"
    end

    def test_name_derived_from_network
      f = Bada::Foundry.forge(EQS)
      assert_match(/\ABada::/, f[:spec][:name])
    end
  end
else
  # Fallback assertions (no minitest available).
  f = Bada::Foundry.forge(
    ["β(p,q) = Γ(p)Γ(q)/Γ(p+q)", "ζ(s) = x·logx"], app_name: "TestApp"
  )
  raise "name" unless f[:spec][:name] == "TestApp"
  raise "modules" unless f[:spec][:module_count] == 2
  out = Bada::Foundry.run_bada(f[:bada_source])
  raise "run" unless out.length >= 2
  raise "html" unless f[:app_html].include?("<!DOCTYPE html>")
  puts "test_foundry (fallback): OK"
end
