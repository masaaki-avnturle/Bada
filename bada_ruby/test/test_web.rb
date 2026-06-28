# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

# End-to-end tests for Bada::Web — the Rails-equivalent MVC framework. Requests
# are dispatched straight through the Application (no socket needed), exercising
# router -> controller -> ORM (Ω::DATABASE) -> ERB view + layout.
class TestWebRouter < Minitest::Test
  def setup
    @router = Bada::Web::Router.new do
      root "posts#index"
      get "/about", to: "pages#about"
      resources :posts
    end
  end

  def test_root_and_static
    assert_equal({ controller: "posts", action: "index", params: {} },
                 @router.recognize("GET", "/"))
    assert_equal "pages", @router.recognize("GET", "/about")[:controller]
  end

  def test_restful_resources
    assert_equal "index",  @router.recognize("GET", "/posts")[:action]
    assert_equal "new",    @router.recognize("GET", "/posts/new")[:action]
    assert_equal "create", @router.recognize("POST", "/posts")[:action]

    show = @router.recognize("GET", "/posts/7")
    assert_equal "show", show[:action]
    assert_equal "7", show[:params]["id"]

    assert_equal "edit",    @router.recognize("GET", "/posts/7/edit")[:action]
    assert_equal "update",  @router.recognize("PATCH", "/posts/7")[:action]
    assert_equal "update",  @router.recognize("PUT", "/posts/7")[:action]
    assert_equal "destroy", @router.recognize("DELETE", "/posts/7")[:action]
    assert_nil @router.recognize("GET", "/nope")
  end

  def test_named_path_helpers
    assert_equal "/posts", @router.path_for("posts")
    assert_equal "/posts/new", @router.path_for("new_post")
    assert_equal "/posts/3", @router.path_for("post", 3)
    assert_equal "/posts/3/edit", @router.path_for("edit_post", 3)
  end
end

class TestWebModel < Minitest::Test
  class Widget < Bada::Web::Model
    attribute :name
    validates :name, presence: true
  end

  def setup
    Widget.destroy_all
  end

  def test_create_find_where_count
    w = Widget.create(name: "alpha")
    assert w.persisted?
    assert_equal 1, w.id
    assert_equal 1, Widget.count
    assert_equal "alpha", Widget.find(1).name
    assert_equal [w], Widget.where(name: "alpha")
    assert_empty Widget.where(name: "missing")
  end

  def test_validation_blocks_save
    w = Widget.new(name: "")
    refute w.save
    refute w.valid?
    assert_equal 0, Widget.count
    refute_empty w.errors
  end

  def test_update_and_destroy
    w = Widget.create(name: "beta")
    w.update(name: "gamma")
    assert_equal "gamma", Widget.find(w.id).name
    w.destroy
    assert_equal 0, Widget.count
  end

  def test_rows_mirrored_into_akashic_tuplespace
    Widget.create(name: "needle in akashic")
    hit = Bada::Web::Model.akashic.scan("needle")
    refute_empty hit, "row should be written into Ω::DATABASE"
  end
end

class TestWebApplication < Minitest::Test
  def setup
    Bada::Web::Demo::Post.destroy_all
    @app = Bada::Web.demo_app(seed: false)
  end

  def test_index_renders_with_layout
    res = @app.get("/")
    assert_equal 200, res.status
    assert_includes res.body, "<title>Bada::Web Blog</title>" # layout applied
    assert_includes res.body, "Posts"
  end

  def test_full_crud_cycle
    # CREATE via POST with nested params + redirect
    res = @app.post("/posts",
                    headers: { "Content-Type" => "application/x-www-form-urlencoded" },
                    body: "post[title]=First&post[body]=Hello")
    assert_equal 302, res.status
    assert_equal "/posts/1", res["Location"]
    assert_equal 1, Bada::Web::Demo::Post.count

    # SHOW
    show = @app.get("/posts/1")
    assert_equal 200, show.status
    assert_includes show.body, "First"
    assert_includes show.body, "Hello"

    # UPDATE via PATCH (form _method override)
    upd = @app.post("/posts/1",
                    headers: { "Content-Type" => "application/x-www-form-urlencoded" },
                    body: "_method=patch&post[title]=Renamed")
    assert_equal 302, upd.status
    assert_equal "Renamed", Bada::Web::Demo::Post.find(1).title

    # DESTROY via DELETE
    del = @app.delete("/posts/1")
    assert_equal 302, del.status
    assert_equal 0, Bada::Web::Demo::Post.count
  end

  def test_validation_failure_rerenders_new
    res = @app.post("/posts",
                    headers: { "Content-Type" => "application/x-www-form-urlencoded" },
                    body: "post[title]=&post[body]=x")
    assert_equal 200, res.status                 # re-rendered, not redirected
    assert_includes res.body, "be blank"          # error shown (HTML-escaped)
    assert_equal 0, Bada::Web::Demo::Post.count
  end

  def test_404_for_unknown_route
    assert_equal 404, @app.get("/nope").status
  end

  def test_missing_record_is_404
    assert_equal 404, @app.get("/posts/999").status
  end

  def test_json_rendering
    klass = Class.new(Bada::Web::Controller) do
      def show = render(json: { ok: true, id: params["id"] })
    end
    app = Bada::Web::Application.new do
      routes { get "/api/:id", to: "api#show" }
      controller "api", klass
    end
    res = app.get("/api/42")
    assert_includes res["Content-Type"], "application/json"
    require "json"
    assert_equal({ "ok" => true, "id" => "42" }, JSON.parse(res.body))
  end
end

class TestWebQueryParser < Minitest::Test
  def test_nested_and_array_params
    parsed = Bada::Web.parse_query("post[title]=Hi&post[body]=Yo&tags[]=a&tags[]=b")
    assert_equal({ "title" => "Hi", "body" => "Yo" }, parsed["post"])
    assert_equal %w[a b], parsed["tags"]
  end
end

class TestWebGenerator < Minitest::Test
  def test_scaffold_writes_expected_files
    require "tmpdir"
    Dir.mktmpdir do |dir|
      out = StringIO.new
      gen = Bada::Web::Generator.new(dir, out: out)
      gen.new_app("blog")
      base = File.join(dir, "blog")
      gen.generate_scaffold("Post", %w[title body], base: base)

      assert File.exist?(File.join(base, "app/models/post.rb"))
      assert File.exist?(File.join(base, "app/controllers/posts_controller.rb"))
      assert File.exist?(File.join(base, "app/views/posts/index.html.erb"))
      assert File.exist?(File.join(base, "db/migrate/00000000000000_create_posts.rb"))
      assert_includes File.read(File.join(base, "config/routes.rb")), "resources :posts"
    end
  end
end
