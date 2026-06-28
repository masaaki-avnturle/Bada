# frozen_string_literal: true

require_relative "request"
require_relative "response"
require_relative "router"
require_relative "view"

module Bada
  module Web
    # The application — the Rails app object. Holds the router, the controller
    # registry and the view layer, and turns an HTTP request into a response by
    # routing -> instantiating the controller -> dispatching the action.
    #
    #   app = Bada::Web::Application.new do
    #     routes { resources :posts; root "posts#index" }
    #     controller "posts", PostsController
    #     template "posts/index", "<h1>Posts</h1> ..."
    #     layout "<html><body><%= yield %></body></html>"
    #   end
    #   app.call(method: "GET", path: "/posts")   # => Bada::Web::Response
    class Application
      attr_reader :router, :controllers, :view, :config

      def initialize(&block)
        @router      = Router.new
        @controllers = {}
        @templates   = {}
        @view_paths  = []
        @config      = { logger: nil }
        instance_eval(&block) if block
        rebuild_view!
      end

      # --- configuration DSL -------------------------------------------------

      def routes(&block)
        @router = Router.new(&block)
        rebuild_view!
        @router
      end

      # Install a pre-built Router (e.g. one loaded from config/routes.rb).
      def router=(router)
        @router = router
        rebuild_view!
        @router
      end

      # Register a controller class for a path name ("posts" => PostsController).
      def controller(name, klass)
        @controllers[name.to_s] = klass
      end

      def template(name, source)
        @templates[name.to_s] = source
        @view&.register(name, source)
      end

      def layout(source)
        template("layouts/application", source)
      end

      def view_path(path)
        @view_paths << path
        rebuild_view!
      end

      # --- request handling --------------------------------------------------

      # Accepts either a Request or the keyword args to build one.
      def call(request = nil, **kwargs)
        request ||= Request.new(**kwargs)
        route = @router.recognize(request.method, request.path)
        return not_found(request) unless route

        klass = @controllers[route[:controller]] || resolve_controller(route[:controller])
        return not_found(request) unless klass

        request.path_params = route[:params]
        response = Response.new
        controller = klass.new(request: request, response: response,
                               app: self, params: request.params)
        controller.dispatch(route[:action])
      rescue Model::RecordNotFound => e
        not_found(request, e.message)
      rescue StandardError => e
        server_error(request, e)
      end

      # Convenience for tests: returns the Response.
      def get(path, **kw)    = call(method: "GET", path: path, **kw)
      def post(path, **kw)   = call(method: "POST", path: path, **kw)
      def patch(path, **kw)  = call(method: "PATCH", path: path, **kw)
      def put(path, **kw)    = call(method: "PUT", path: path, **kw)
      def delete(path, **kw) = call(method: "DELETE", path: path, **kw)

      def url_helpers
        @router.url_helpers
      end

      private

      def rebuild_view!
        @view = View.new(templates: @templates, view_paths: @view_paths,
                         url_helpers: @router.url_helpers)
      end

      # Convention fallback: "posts" -> PostsController if such a constant exists.
      def resolve_controller(name)
        const = "#{camelize(name)}Controller"
        Object.const_defined?(const) ? Object.const_get(const) : nil
      end

      def camelize(str)
        str.to_s.split(/[_\/]/).map { |p| p[0].to_s.upcase + p[1..].to_s }.join
      end

      def not_found(_request, message = "Not Found")
        Response.new(status: 404,
                     body: "<html><body><h1>404 Not Found</h1>" \
                           "<p>#{message}</p></body></html>")
      end

      def server_error(_request, error)
        @config[:logger]&.call("ERROR: #{error.class}: #{error.message}")
        trace = error.backtrace ? error.backtrace.first(8).join("\n") : ""
        Response.new(status: 500,
                     body: "<html><body><h1>500 Internal Server Error</h1>" \
                           "<pre>#{CGI.escapeHTML("#{error.class}: #{error.message}\n#{trace}")}</pre>" \
                           "</body></html>")
      end
    end
  end
end
