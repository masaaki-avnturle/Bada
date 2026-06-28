# frozen_string_literal: true

require "uri"

module Bada
  module Web
    # An incoming HTTP request — the "stream" entering the manifold.
    #
    # Carries the verb, path, headers and a merged params hash built from the
    # query string, the urlencoded/JSON body, and (later) the route's path
    # segments. Rails-style nested keys are supported: a form field named
    # `post[title]` becomes `params["post"]["title"]`.
    class Request
      attr_reader :method, :path, :headers, :query_params, :body_params, :body
      attr_accessor :path_params

      def initialize(method:, path:, headers: {}, body: "")
        @raw_method   = method.to_s.upcase
        uri           = URI.parse(path)
        @path         = uri.path.empty? ? "/" : uri.path
        @headers      = normalize_headers(headers)
        @body         = body.to_s
        @query_params = Web.parse_query(uri.query || "")
        @body_params  = parse_body
        @path_params  = {}
        @method       = resolve_method
      end

      # The effective HTTP verb, honouring Rails' `_method` override so that
      # HTML forms (which can only GET/POST) can drive PATCH/PUT/DELETE.
      def resolve_method
        override = (@body_params["_method"] || @query_params["_method"] ||
                    @headers["x-http-method-override"]).to_s.upcase
        return override unless override.empty?

        @raw_method
      end

      def get?    = @method == "GET"
      def post?   = @method == "POST"
      def patch?  = @method == "PATCH"
      def put?    = @method == "PUT"
      def delete? = @method == "DELETE"

      # All params merged: path segments win over body, body wins over query.
      def params
        deep_merge(deep_merge(@query_params, @body_params), stringify(@path_params))
      end

      def content_type
        @headers["content-type"].to_s
      end

      private

      def parse_body
        return {} if @body.empty?

        if content_type.include?("application/json")
          begin
            require "json"
            parsed = JSON.parse(@body)
            return parsed.is_a?(Hash) ? parsed : { "_json" => parsed }
          rescue StandardError
            return {}
          end
        end
        Web.parse_query(@body)
      end

      def normalize_headers(headers)
        headers.each_with_object({}) do |(k, v), h|
          h[k.to_s.downcase] = v
        end
      end

      def stringify(hash)
        hash.each_with_object({}) { |(k, v), h| h[k.to_s] = v }
      end

      def deep_merge(a, b)
        merged = a.dup
        b.each do |k, v|
          merged[k] = if merged[k].is_a?(Hash) && v.is_a?(Hash)
                        deep_merge(merged[k], v)
                      else
                        v
                      end
        end
        merged
      end
    end
  end
end
