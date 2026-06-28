# frozen_string_literal: true

require "fileutils"

module Bada
  module Web
    # The code generator — the Bada::Web equivalent of `rails new` and
    # `rails generate scaffold`. It writes a working MVC app to disk: model,
    # controller, ERB views, a routes file and a migration — the same set of
    # artifacts described in src/omegascript_from_to_Rails.txt, but for the
    # pure-Ruby Bada::Web framework instead of Rails itself.
    class Generator
      def initialize(root = ".", out: $stdout)
        @root = root
        @out  = out
      end

      # Create a new application skeleton.
      def new_app(name)
        base = File.join(@root, name)
        %w[app/models app/controllers app/views/layouts
           config db/migrate].each { |d| mkdir(File.join(base, d)) }

        write(File.join(base, "config/routes.rb"), <<~RUBY)
          # frozen_string_literal: true
          # Bada::Web routes for #{name}
          AppRoutes = Bada::Web::Router.new do
            root "home#index"
          end
        RUBY

        write(File.join(base, "app/controllers/home_controller.rb"), <<~RUBY)
          # frozen_string_literal: true
          class HomeController < Bada::Web::Controller
            def index; end
          end
        RUBY

        write(File.join(base, "app/views/layouts/application.html.erb"), layout_erb(name))
        write(File.join(base, "app/views/home/index.html.erb"),
              "<h1>Welcome to #{name}</h1>\n<p>Powered by Bada::Web (Ω::DATABASE).</p>\n")
        write(File.join(base, "config.ru.rb"), boot_erb(name))
        @out.puts "created Bada::Web app -> #{base}"
        base
      end

      # Scaffold a resource: model + controller + views + routes + migration.
      #   generate_scaffold("Post", %w[title body])
      def generate_scaffold(model, fields, base: @root)
        singular = model.to_s.downcase
        plural   = pluralize(singular)
        klass    = camelize(singular)

        write_model(base, klass, fields)
        write_migration(base, plural, fields)
        write_controller(base, klass, singular, plural, fields)
        write_views(base, singular, plural, klass, fields)
        append_route(base, plural)
        @out.puts "scaffolded #{klass} (#{fields.join(', ')})"
      end

      # --- the individual file generators (mirrors RailsFileGenerator) -------

      def write_model(base, klass, fields)
        attrs = fields.map { |f| "  attribute :#{f}" }.join("\n")
        first = fields.first
        validation = first ? "\n  validates :#{first}, presence: true\n" : ""
        write(File.join(base, "app/models/#{klass.downcase}.rb"), <<~RUBY)
          # frozen_string_literal: true
          class #{klass} < Bada::Web::Model
          #{attrs}
          #{validation}end
        RUBY
      end

      def write_migration(base, plural, fields)
        stamp = "00000000000000" # deterministic; replace with timestamp if desired
        cols  = fields.map { |f| "        t.string :#{f}" }.join("\n")
        write(File.join(base, "db/migrate/#{stamp}_create_#{plural}.rb"), <<~RUBY)
          # frozen_string_literal: true
          class Create#{camelize(plural)} < Bada::Web::Migration
            def change
              create_table :#{plural} do |t|
          #{cols}
                t.timestamps
              end
            end
          end
        RUBY
      end

      def write_controller(base, klass, singular, plural, fields)
        permitted = fields.map { |f| "\"#{f}\"" }.join(", ")
        write(File.join(base, "app/controllers/#{plural}_controller.rb"), <<~RUBY)
          # frozen_string_literal: true
          class #{camelize(plural)}Controller < Bada::Web::Controller
            before_action :set_#{singular}, only: %i[show edit update destroy]

            def index = (@#{plural} = #{klass}.all)
            def show; end
            def new = (@#{singular} = #{klass}.new)
            def edit; end

            def create
              @#{singular} = #{klass}.new(#{singular}_params)
              if @#{singular}.save
                redirect_to #{singular}_path(@#{singular}), notice: "#{klass} created"
              else
                render :new
              end
            end

            def update
              if @#{singular}.update(#{singular}_params)
                redirect_to #{singular}_path(@#{singular}), notice: "#{klass} updated"
              else
                render :edit
              end
            end

            def destroy
              @#{singular}.destroy
              redirect_to #{plural}_path, notice: "#{klass} deleted"
            end

            private

            def set_#{singular} = (@#{singular} = #{klass}.find(params["id"]))
            def #{singular}_params = (params["#{singular}"] || {}).slice(#{permitted})
          end
        RUBY
      end

      def write_views(base, singular, plural, klass, fields)
        dir = File.join(base, "app/views/#{plural}")
        mkdir(dir)
        write(File.join(dir, "index.html.erb"), index_erb(singular, plural, klass, fields))
        write(File.join(dir, "show.html.erb"), show_erb(singular, plural, fields))
        write(File.join(dir, "new.html.erb"),
              "<h1>New #{klass}</h1>\n<%= render \"#{plural}/form\", #{singular}: @#{singular} %>\n" \
              "<p><a href=\"<%= #{plural}_path %>\">Back</a></p>\n")
        write(File.join(dir, "edit.html.erb"),
              "<h1>Edit #{klass}</h1>\n<%= render \"#{plural}/form\", #{singular}: @#{singular} %>\n" \
              "<p><a href=\"<%= #{plural}_path %>\">Back</a></p>\n")
        write(File.join(dir, "form.html.erb"), form_erb(singular, plural, fields))
      end

      def append_route(base, plural)
        path = File.join(base, "config/routes.rb")
        return unless File.exist?(path)

        content = File.read(path)
        return if content.include?("resources :#{plural}")

        content = content.sub(/\nend\s*\z/, "\n  resources :#{plural}\nend\n")
        File.write(path, content)
      end

      private

      def index_erb(singular, plural, klass, fields)
        cols = fields.map { |f| "      <td><%= h #{singular}.#{f} %></td>" }.join("\n")
        heads = fields.map { |f| "    <th>#{f.capitalize}</th>" }.join("\n")
        <<~ERB
          <h1>#{klass.capitalize}s</h1>
          <% if @flash ||= nil %><p class="notice"><%= h @flash[:notice] %></p><% end %>
          <table border="1">
            <tr>
          #{heads}
              <th>Actions</th>
            </tr>
            <% @#{plural}.each do |#{singular}| %>
            <tr>
          #{cols}
              <td>
                <%= link_to "Show", #{singular}_path(#{singular}) %>
                <%= link_to "Edit", edit_#{singular}_path(#{singular}) %>
                <%= button_to "Delete", #{singular}_path(#{singular}), method: :delete, data: { confirm: "Sure?" } %>
              </td>
            </tr>
            <% end %>
          </table>
          <p><a href="<%= new_#{singular}_path %>">New #{singular}</a></p>
        ERB
      end

      def show_erb(singular, _plural, fields)
        rows = fields.map { |f| "<p><strong>#{f.capitalize}:</strong> <%= h @#{singular}.#{f} %></p>" }.join("\n")
        "<h1>Show</h1>\n#{rows}\n<p><a href=\"<%= edit_#{singular}_path(@#{singular}) %>\">Edit</a></p>\n"
      end

      def form_erb(singular, plural, fields)
        action_index = "<%= #{plural}_path %>"
        action_member = "<%= #{singular}_path(#{singular}) %>"
        inputs = fields.map do |f|
          "  <p>#{f.capitalize}:<br>" \
            "<input type=\"text\" name=\"#{singular}[#{f}]\" value=\"<%= h #{singular}.#{f} %>\"></p>"
        end.join("\n")
        <<~ERB
          <% #{singular} ||= @#{singular} %>
          <% if #{singular}.errors.any? %>
            <ul><% #{singular}.errors.each do |e| %><li><%= h e %></li><% end %></ul>
          <% end %>
          <form action="<%= #{singular}.persisted? ? "#{action_member}" : "#{action_index}" %>" method="post">
            <% if #{singular}.persisted? %><input type="hidden" name="_method" value="patch"><% end %>
          #{inputs}
            <p><input type="submit" value="Save"></p>
          </form>
        ERB
      end

      def layout_erb(name)
        <<~ERB
          <!DOCTYPE html>
          <html>
          <head><meta charset="utf-8"><title>#{name}</title></head>
          <body>
            <% if (defined?(@flash) && @flash) %><p class="notice"><%= h @flash[:notice] %></p><% end %>
            <%= yield %>
          </body>
          </html>
        ERB
      end

      def boot_erb(name)
        <<~RUBY
          # frozen_string_literal: true
          # Boot #{name}: require app files, build the Application, run the server.
          require "bada"
          Dir[File.join(__dir__, "app/models/*.rb")].sort.each { |f| require f }
          Dir[File.join(__dir__, "app/controllers/*.rb")].sort.each { |f| require f }
          require_relative "config/routes"

          app = Bada::Web::Application.new
          app.router = AppRoutes
          app.view_path(File.join(__dir__, "app/views"))
          # Controllers are resolved by convention (ArticlesController, etc.).
          Bada::Web::Server.new(app, port: 3000).start
        RUBY
      end

      def mkdir(dir)  = FileUtils.mkdir_p(dir)
      def write(path, content)
        mkdir(File.dirname(path))
        File.write(path, content)
        @out.puts "  create #{path}"
      end

      def pluralize(word)
        if word.end_with?("y") && !%w[a e i o u].include?(word[-2])
          "#{word[0..-2]}ies"
        elsif word.end_with?("s", "x", "z", "ch", "sh")
          "#{word}es"
        else
          "#{word}s"
        end
      end

      def camelize(str)
        str.to_s.split(/[_\s]/).map { |p| p[0].to_s.upcase + p[1..].to_s }.join
      end
    end
  end
end
