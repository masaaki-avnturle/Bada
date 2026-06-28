# frozen_string_literal: true

require "json"

module Bada
  module Web
    # The base controller — ActionController, rebuilt from scratch.
    #
    #   class PostsController < Bada::Web::Controller
    #     before_action :set_post, only: %i[show edit update destroy]
    #
    #     def index = (@posts = Post.all)
    #     def show; end
    #     def create
    #       @post = Post.new(post_params)
    #       if @post.save then redirect_to post_path(@post)
    #       else render :new end
    #     end
    #
    #     private
    #     def set_post  = (@post = Post.find(params["id"]))
    #     def post_params = params["post"] || {}
    #   end
    class Controller
      attr_reader :request, :response, :app

      def initialize(request:, response:, app:, params: {})
        @request   = request
        @response  = response
        @app       = app
        @params    = params
        @performed = false
        extend(app.url_helpers) if app.respond_to?(:url_helpers)
      end

      # --- before_action filters --------------------------------------------
      class << self
        def before_actions
          @before_actions ||= []
        end

        def inherited(subclass)
          super
          subclass.instance_variable_set(:@before_actions, before_actions.dup)
        end

        def before_action(name, only: nil, except: nil)
          before_actions << { name: name, only: arr(only), except: arr(except) }
        end

        private

        def arr(v)
          v.nil? ? nil : Array(v).map(&:to_sym)
        end
      end

      # Run filters then the action, auto-rendering if nothing was performed.
      def dispatch(action)
        run_before_actions(action.to_sym)
        public_send(action) unless @performed
        render(action.to_sym) unless @performed
        @response
      end

      def params
        @params
      end

      # --- rendering / redirecting ------------------------------------------

      # render :index
      # render "posts/show"
      # render text: "ok"   /  render html: "<h1>",  / render json: {...}
      # render plain: "ok", status: 201
      def render(target = nil, status: 200, layout: "layouts/application", **opts)
        guard_performed!
        @response.status = status

        if (txt = opts[:plain] || opts[:text])
          @response["Content-Type"] = "text/plain; charset=utf-8"
          @response.body = txt.to_s
        elsif (html = opts[:html])
          @response.body = html.to_s
        elsif opts.key?(:json)
          @response["Content-Type"] = "application/json; charset=utf-8"
          @response.body = JSON.generate(opts[:json])
        else
          name = template_name(target)
          @response.body = @app.view.render(name, assigns, layout: layout)
        end
        @performed = true
        @response
      end

      def redirect_to(url, status: 302, notice: nil)
        guard_performed!
        @flash_notice = notice
        @response.status = status
        @response["Location"] = url
        @response.body = "<html><body>Redirecting to " \
                         "<a href=\"#{url}\">#{url}</a></body></html>"
        @performed = true
        @response
      end

      def head(status)
        guard_performed!
        @response.status = status
        @response.body = ""
        @performed = true
        @response
      end

      def performed? = @performed

      private

      def guard_performed!
        raise DoubleRenderError, "render/redirect called more than once" if @performed
      end

      class DoubleRenderError < StandardError; end

      def run_before_actions(action)
        self.class.before_actions.each do |f|
          next if f[:only] && !f[:only].include?(action)
          next if f[:except]&.include?(action)

          send(f[:name])
          break if @performed
        end
      end

      # Collect instance variables set by the action as view assigns.
      def assigns
        out = {}
        instance_variables.each do |iv|
          name = iv.to_s.delete_prefix("@")
          next if name.start_with?("_") ||
                  %w[request response app params performed flash_notice].include?(name)

          out[name] = instance_variable_get(iv)
        end
        out[:flash] = { notice: @flash_notice } if @flash_notice
        out
      end

      def template_name(target)
        t = (target || "").to_s
        return "#{controller_path}/#{t}" unless t.include?("/")

        t
      end

      # "PostsController" -> "posts"
      def controller_path
        self.class.name.to_s.split("::").last
            .sub(/Controller\z/, "")
            .gsub(/([a-z])([A-Z])/, '\1_\2').downcase
      end
    end
  end
end
