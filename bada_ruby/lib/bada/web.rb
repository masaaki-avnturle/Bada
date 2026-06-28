# frozen_string_literal: true

require "uri"

module Bada
  # Bada::Web — a Ruby-on-Rails-equivalent MVC web framework, rebuilt from
  # scratch in pure Ruby (stdlib only, no Rails, no Rack, no WEBrick) on top of
  # the Bada Ω::DATABASE (TupleSpace / Akashic Record).
  #
  # It provides the same building blocks as Rails:
  #
  #   Router       RESTful `resources`, named path helpers     -> web/router.rb
  #   Model        ActiveRecord-style ORM (Ω::DATABASE-backed) -> web/model.rb
  #   Controller   ActionController (params/render/redirect)    -> web/controller.rb
  #   View         ERB templates + layout + view helpers        -> web/view.rb
  #   Migration    schema/migration DSL                         -> web/migration.rb
  #   Application   the app object: route -> controller -> view -> web/application.rb
  #   Server       pure-stdlib HTTP/1.1 server                  -> web/server.rb
  #   Generator    `new` app + `scaffold` resource generators   -> web/generator.rb
  #
  #   app = Bada::Web.demo_app          # a working blog
  #   Bada::Web::Server.new(app).start  # serve on http://127.0.0.1:3000
  module Web
    module_function

    # Parse an x-www-form-urlencoded string, supporting Rails nested keys:
    #   "post[title]=Hi&post[body]=Yo&tags[]=a&tags[]=b"
    #   => {"post"=>{"title"=>"Hi","body"=>"Yo"}, "tags"=>["a","b"]}
    def parse_query(str)
      out = {}
      str.to_s.split("&").each do |pair|
        next if pair.empty?

        raw_key, raw_val = pair.split("=", 2)
        key   = URI.decode_www_form_component(raw_key.to_s)
        value = URI.decode_www_form_component(raw_val.to_s)
        assign_nested(out, key, value)
      end
      out
    end

    def assign_nested(hash, key, value)
      if (m = key.match(/\A(\w+)\[(\w*)\](.*)\z/))
        base, inner, rest = m[1], m[2], m[3]
        if inner.empty? # array: tags[]
          (hash[base] ||= []) << value
        else
          hash[base] ||= {}
          assign_nested(hash[base], inner + rest, value)
        end
      else
        hash[key] = value
      end
    end
  end
end

require_relative "web/helpers"
require_relative "web/request"
require_relative "web/response"
require_relative "web/router"
require_relative "web/model"
require_relative "web/view"
require_relative "web/controller"
require_relative "web/migration"
require_relative "web/application"
require_relative "web/server"
require_relative "web/generator"
require_relative "web/demo"
