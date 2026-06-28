# frozen_string_literal: true

module Bada
  module Web
    # The router — maps an incoming (verb, path) onto a controller#action and
    # extracts path params. Provides a Rails-style DSL:
    #
    #   Bada::Web::Router.new do
    #     root "home#index"
    #     get  "/about", to: "pages#about"
    #     resources :posts
    #   end
    #
    # `resources :posts` expands to the seven RESTful routes and registers the
    # named path helpers (posts_path, new_post_path, post_path(id),
    # edit_post_path(id)) on the url-helpers module.
    class Router
      Route = Struct.new(:verb, :segments, :controller, :action, :name, keyword_init: true)

      attr_reader :routes, :named

      def initialize(&block)
        @routes = []
        @named  = {} # name => template string with :id placeholders
        instance_eval(&block) if block
      end

      # --- DSL ---------------------------------------------------------------

      def root(target)
        map("GET", "/", target, name: "root")
      end

      def get(path, to:, as: nil)    = map("GET", path, to, name: as)
      def post(path, to:, as: nil)   = map("POST", path, to, name: as)
      def patch(path, to:, as: nil)  = map("PATCH", path, to, name: as)
      def put(path, to:, as: nil)    = map("PUT", path, to, name: as)
      def delete(path, to:, as: nil) = map("DELETE", path, to, name: as)

      # RESTful resource — the seven canonical Rails routes.
      def resources(name)
        n  = name.to_s            # plural, e.g. "posts"
        s  = singularize(n)       # singular, e.g. "post"
        map("GET",    "/#{n}",          "#{n}#index",   name: "#{n}")
        map("GET",    "/#{n}/new",      "#{n}#new",     name: "new_#{s}")
        map("POST",   "/#{n}",          "#{n}#create",  name: nil)
        map("GET",    "/#{n}/:id",      "#{n}#show",    name: s)
        map("GET",    "/#{n}/:id/edit", "#{n}#edit",    name: "edit_#{s}")
        map("PATCH",  "/#{n}/:id",      "#{n}#update",  name: nil)
        map("PUT",    "/#{n}/:id",      "#{n}#update",  name: nil)
        map("DELETE", "/#{n}/:id",      "#{n}#destroy", name: nil)
      end

      # --- matching ----------------------------------------------------------

      # Recognize a request -> { controller:, action:, params: } or nil.
      def recognize(verb, path)
        verb = verb.to_s.upcase
        path_segs = split(path)
        @routes.each do |r|
          next unless r.verb == verb
          params = match(r.segments, path_segs)
          next unless params

          return { controller: r.controller, action: r.action, params: params }
        end
        nil
      end

      # Build "/posts/3" from a named route + args.
      def path_for(name, *args)
        template = @named.fetch(name.to_s) do
          raise ArgumentError, "no named route #{name.inspect}"
        end
        i = 0
        template.gsub(/:(\w+)/) do
          arg = args[i]
          i += 1
          id_of(arg)
        end
      end

      # A module exposing `<name>_path` helpers, bound to this router.
      def url_helpers
        router = self
        Module.new do
          router.named.each_key do |name|
            define_method("#{name}_path") { |*args| router.path_for(name, *args) }
          end
        end
      end

      private

      def map(verb, path, target, name: nil)
        controller, action = target.to_s.split("#", 2)
        @routes << Route.new(verb: verb, segments: split(path),
                             controller: controller, action: action, name: name)
        @named[name] = path if name && !@named.key?(name)
        self
      end

      def split(path)
        path.to_s.split("/").reject(&:empty?)
      end

      # Returns extracted params hash if route segments match the request path.
      def match(route_segs, path_segs)
        return nil unless route_segs.length == path_segs.length

        params = {}
        route_segs.each_with_index do |seg, i|
          if seg.start_with?(":")
            params[seg[1..]] = unescape(path_segs[i])
          elsif seg != path_segs[i]
            return nil
          end
        end
        params
      end

      def id_of(arg)
        if arg.respond_to?(:id) && !arg.is_a?(Integer) && !arg.is_a?(String)
          arg.id
        else
          arg
        end.to_s
      end

      def unescape(str)
        require "uri"
        URI.decode_www_form_component(str)
      rescue StandardError
        str
      end

      def singularize(word)
        if word.end_with?("ies")
          "#{word[0..-4]}y"
        elsif word.end_with?("ses", "xes", "zes", "ches", "shes")
          word[0..-3]
        elsif word.end_with?("s")
          word[0..-2]
        else
          word
        end
      end
    end
  end
end
