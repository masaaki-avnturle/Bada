# frozen_string_literal: true

require "erb"
require "cgi"

module Bada
  module Web
    # The view layer — ERB templates with a layout, Rails-style view helpers,
    # and the router's named path helpers (`posts_path`, `post_path(p)`, ...).
    #
    # Templates are looked up by "controller/action" either from a registered
    # in-memory template table or from a views directory of `.html.erb` files.
    # A layout (default "layouts/application") wraps the rendered body and may
    # use `<%= yield %>` just like Rails.
    class View
      class MissingTemplate < StandardError; end

      def initialize(templates: {}, view_paths: [], url_helpers: Module.new)
        @templates   = templates          # "posts/index" => erb source
        @view_paths  = Array(view_paths)
        @url_helpers = url_helpers
      end

      def register(name, source)
        @templates[name.to_s] = source
      end

      def template?(name)
        return true if @templates.key?(name.to_s)

        !resolve_path(name).nil?
      end

      def source_for(name)
        return @templates[name.to_s] if @templates.key?(name.to_s)

        path = resolve_path(name)
        raise MissingTemplate, "template not found: #{name}" unless path

        File.read(path)
      end

      # Render template `name` with `assigns` (instance vars) inside `layout`.
      def render(name, assigns = {}, layout: "layouts/application")
        ctx  = Context.new(assigns, @url_helpers, self)
        body = ctx.render_source(source_for(name))
        return body unless layout && template?(layout)

        ctx.render_layout(source_for(layout), body)
      end

      private

      def resolve_path(name)
        @view_paths.each do |base|
          %W[#{name}.html.erb #{name}.erb].each do |rel|
            candidate = File.join(base, rel)
            return candidate if File.file?(candidate)
          end
        end
        nil
      end

      # The binding context in which an ERB template runs. Holds the assigns as
      # instance variables and mixes in the view helpers + named path helpers.
      class Context
        def initialize(assigns, url_helpers, view)
          @__view    = view
          @__assigns = assigns
          assigns.each { |k, v| instance_variable_set("@#{k}", v) }
          extend(Bada::Web::ViewHelpers)
          extend(url_helpers)
          @__url_helpers = url_helpers
        end

        # Render a nested partial template, inheriting assigns + extra locals.
        def render(name, locals = {})
          merged = @__assigns.merge(locals)
          ctx = Context.new(merged, @__url_helpers, @__view)
          ctx.render_source(@__view.source_for(name))
        end

        def render_source(src)
          ERB.new(src, trim_mode: "-").result(binding)
        end

        # Wrap rendered `inner` content with a layout that may call `yield`.
        def render_layout(layout_src, inner)
          ERB.new(layout_src, trim_mode: "-").result(layout_binding { inner })
        end

        private

        # Capture a binding whose `yield` returns the inner content. Because the
        # binding is taken inside this method (which receives the block), a bare
        # `<%= yield %>` in the layout yields the page body — exactly like Rails.
        def layout_binding
          binding
        end
      end
    end
  end
end
