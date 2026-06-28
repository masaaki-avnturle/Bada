# frozen_string_literal: true

require "socket"
require_relative "request"

module Bada
  module Web
    # A minimal, pure-Ruby HTTP/1.1 server (stdlib `socket` only — no WEBrick,
    # no Rack) that drives a Bada::Web::Application. Single-threaded but
    # connection-per-request; good enough to serve the framework live.
    #
    #   Bada::Web::Server.new(app, port: 3000).start
    class Server
      def initialize(app, host: "127.0.0.1", port: 3000, logger: $stdout)
        @app    = app
        @host   = host
        @port   = port
        @logger = logger
      end

      def start
        server = TCPServer.new(@host, @port)
        log "Bada::Web listening on http://#{@host}:#{@port}  (Ctrl-C to stop)"
        loop do
          begin
            session = server.accept
            handle(session)
          rescue Interrupt
            break
          rescue StandardError => e
            log "connection error: #{e.class}: #{e.message}"
          ensure
            session&.close
          end
        end
      ensure
        server&.close
        log "Bada::Web stopped."
      end

      private

      def handle(session)
        request = read_request(session)
        return unless request

        response = @app.call(request)
        session.write(response.to_http)
        log "#{request.method} #{request.path} -> #{response.status}"
      end

      def read_request(session)
        request_line = session.gets
        return nil unless request_line

        method, path, = request_line.split(" ")
        headers = {}
        while (line = session.gets) && line != "\r\n" && line != "\n"
          key, value = line.split(":", 2)
          headers[key.strip.downcase] = value.to_s.strip if value
        end

        body = ""
        if (len = headers["content-length"]&.to_i) && len.positive?
          body = session.read(len).to_s
        end

        Request.new(method: method, path: path, headers: headers, body: body)
      end

      def log(msg)
        @logger&.puts("[#{Time.now.strftime('%H:%M:%S')}] #{msg}")
      end
    end
  end
end
