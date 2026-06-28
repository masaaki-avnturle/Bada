# frozen_string_literal: true

module Bada
  module Web
    # A complete, working demo application — a blog — that exercises every part
    # of Bada::Web (router, ORM on Ω::DATABASE, controller, ERB views + layout,
    # RESTful resources, flash). `Bada::Web.demo_app` returns a ready
    # Application; the CLI's `bada web` boots it with the HTTP server.
    module Demo
      # A migration, declared the Rails way.
      class CreatePosts < Migration
        def change
          create_table :posts do |t|
            t.string :title
            t.text   :body
            t.timestamps
          end
        end
      end

      class Post < Model
        attribute :title
        attribute :body
        validates :title, presence: true
        validates :title, length: { minimum: 2 }
      end

      class PostsController < Controller
        before_action :set_post, only: %i[show edit update destroy]

        def index = (@posts = Post.all)
        def show; end
        def new = (@post = Post.new)
        def edit; end

        def create
          @post = Post.new(post_params)
          if @post.save
            redirect_to post_path(@post), notice: "Post created"
          else
            render :new
          end
        end

        def update
          if @post.update(post_params)
            redirect_to post_path(@post), notice: "Post updated"
          else
            render :edit
          end
        end

        def destroy
          @post.destroy
          redirect_to posts_path, notice: "Post deleted"
        end

        private

        def set_post = (@post = Post.find(params["id"]))

        def post_params
          (params["post"] || {}).select { |k, _| %w[title body].include?(k) }
        end
      end

      LAYOUT = <<~ERB
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>Bada::Web Blog</title></head>
        <body>
          <header><a href="<%= posts_path %>">🔤 Bada::Web Blog</a></header>
          <% if defined?(@flash) && @flash %><p class="notice"><%= h @flash[:notice] %></p><% end %>
          <hr>
          <%= yield %>
          <hr>
          <footer>Powered by Bada::Web — Rails-equivalent MVC on Ω::DATABASE.</footer>
        </body>
        </html>
      ERB

      INDEX = <<~ERB
        <h1>Posts</h1>
        <ul>
        <% @posts.each do |post| %>
          <li>
            <a href="<%= post_path(post) %>"><%= h post.title %></a>
            &nbsp; <a href="<%= edit_post_path(post) %>">edit</a>
            <%= button_to "delete", post_path(post), method: :delete, data: { confirm: "Delete this post?" } %>
          </li>
        <% end %>
        </ul>
        <p><a href="<%= new_post_path %>">New post</a></p>
      ERB

      SHOW = <<~ERB
        <h1><%= h @post.title %></h1>
        <p><%= h @post.body %></p>
        <p>
          <a href="<%= edit_post_path(@post) %>">Edit</a> |
          <a href="<%= posts_path %>">Back</a>
        </p>
      ERB

      FORM = <<~ERB
        <% post = @post %>
        <% if post.errors.any? %>
          <ul class="errors">
          <% post.errors.each do |e| %><li><%= h e %></li><% end %>
          </ul>
        <% end %>
        <form action="<%= post.persisted? ? post_path(post) : posts_path %>" method="post">
          <% if post.persisted? %><input type="hidden" name="_method" value="patch"><% end %>
          <p>Title:<br><input type="text" name="post[title]" value="<%= h post.title %>"></p>
          <p>Body:<br><textarea name="post[body]"><%= h post.body %></textarea></p>
          <p><input type="submit" value="Save"></p>
        </form>
      ERB

      NEW  = "<h1>New Post</h1>\n#{FORM}<p><a href=\"<%= posts_path %>\">Back</a></p>\n"
      EDIT = "<h1>Edit Post</h1>\n#{FORM}<p><a href=\"<%= posts_path %>\">Back</a></p>\n"

      def self.build
        CreatePosts.new.migrate

        app = Application.new do
          routes do
            root "posts#index"
            resources :posts
          end
          controller "posts", PostsController
          layout LAYOUT
          template "posts/index", INDEX
          template "posts/show", SHOW
          template "posts/new", NEW
          template "posts/edit", EDIT
        end
        app
      end

      def self.seed!
        return unless Post.count.zero?

        Post.create(title: "Hello Bada::Web",
                    body: "A Rails-equivalent web system, in pure Ruby, on Ω::DATABASE.")
        Post.create(title: "TupleSpace as a database",
                    body: "Every row is also an Akashic manifold point.")
      end
    end

    # Build (and seed) the demo blog application.
    def self.demo_app(seed: true)
      app = Demo.build
      Demo.seed! if seed
      app
    end
  end
end
