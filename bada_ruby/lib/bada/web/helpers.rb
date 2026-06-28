# frozen_string_literal: true

require "cgi"

module Bada
  module Web
    # Rails-style view helpers, mixed into every template Context.
    module ViewHelpers
      # HTML-escape.
      def h(text)
        CGI.escapeHTML(text.to_s)
      end

      def content_tag(name, content = nil, attrs = {})
        content = yield if block_given?
        "<#{name}#{attributes(attrs)}>#{content}</#{name}>"
      end

      def tag(name, attrs = {})
        "<#{name}#{attributes(attrs)}>"
      end

      def link_to(text, url, attrs = {})
        if attrs[:method] && attrs[:method].to_s.upcase != "GET"
          return button_to(text, url, attrs)
        end

        "<a href=\"#{h(url)}\"#{attributes(attrs.reject { |k, _| k == :method })}>#{h(text)}</a>"
      end

      # A button that submits a tiny form, so it can issue non-GET verbs
      # (DELETE/PATCH) via the `_method` override — same trick as Rails.
      def button_to(text, url, attrs = {})
        verb = (attrs.delete(:method) || "POST").to_s.upcase
        hidden = +""
        unless %w[GET POST].include?(verb)
          hidden = "<input type=\"hidden\" name=\"_method\" value=\"#{verb}\">"
        end
        form_method = verb == "GET" ? "get" : "post"
        confirm = attrs.delete(:data)&.dig(:confirm)
        onsubmit = confirm ? " onsubmit=\"return confirm('#{h(confirm)}')\"" : ""
        "<form action=\"#{h(url)}\" method=\"#{form_method}\" style=\"display:inline\"#{onsubmit}>" \
          "#{hidden}<button type=\"submit\">#{h(text)}</button></form>"
      end

      # form_tag("/posts", method: :post) { ... }
      def form_tag(url, method: :post, &block)
        verb   = method.to_s.upcase
        hidden = +""
        actual = %w[GET POST].include?(verb) ? verb : "POST"
        unless %w[GET POST].include?(verb)
          hidden = "<input type=\"hidden\" name=\"_method\" value=\"#{verb}\">"
        end
        inner = block ? capture(&block) : ""
        "<form action=\"#{h(url)}\" method=\"#{actual.downcase}\">#{hidden}#{inner}</form>"
      end

      def label_tag(name, text = nil)
        "<label for=\"#{h(name)}\">#{h(text || name.to_s.capitalize)}</label>"
      end

      def text_field_tag(name, value = nil, attrs = {})
        tag(:input, { type: "text", name: name, id: name, value: value }.merge(attrs))
      end

      def text_area_tag(name, value = nil, attrs = {})
        "<textarea name=\"#{h(name)}\" id=\"#{h(name)}\"#{attributes(attrs)}>#{h(value)}</textarea>"
      end

      def submit_tag(value = "Save")
        tag(:input, type: "submit", value: value)
      end

      # Nested form field names, e.g. field_name(:post, :title) => "post[title]".
      def field_name(model, attr)
        "#{model}[#{attr}]"
      end

      # Capture an ERB block's output (for helpers that take a block).
      def capture
        yield
      end

      private

      def attributes(attrs)
        return "" if attrs.nil? || attrs.empty?

        attrs.map do |k, v|
          next "" if v.nil?

          " #{k}=\"#{h(v)}\""
        end.join
      end
    end
  end
end
