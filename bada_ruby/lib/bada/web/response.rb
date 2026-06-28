# frozen_string_literal: true

module Bada
  module Web
    # An outgoing HTTP response — the "stream" leaving the manifold.
    class Response
      STATUS_TEXT = {
        200 => "OK", 201 => "Created", 204 => "No Content",
        301 => "Moved Permanently", 302 => "Found", 303 => "See Other",
        400 => "Bad Request", 401 => "Unauthorized", 403 => "Forbidden",
        404 => "Not Found", 422 => "Unprocessable Entity",
        500 => "Internal Server Error"
      }.freeze

      attr_accessor :status, :headers, :body

      def initialize(status: 200, headers: {}, body: "")
        @status  = status
        @headers = { "Content-Type" => "text/html; charset=utf-8" }.merge(headers)
        @body    = body
      end

      def []=(key, value)
        @headers[key] = value
      end

      def [](key) = @headers[key]

      def status_text
        STATUS_TEXT.fetch(@status, "Status #{@status}")
      end

      # Serialize to a raw HTTP/1.1 response string.
      def to_http
        bytes = @body.to_s.b
        head  = +"HTTP/1.1 #{@status} #{status_text}\r\n"
        h = @headers.dup
        h["Content-Length"] = bytes.bytesize.to_s
        h.each { |k, v| head << "#{k}: #{v}\r\n" }
        head << "\r\n"
        head.b + bytes
      end
    end
  end
end
