"""Rails → Web-OS design bridge.

The brief: take the source a Rails scaffold would generate and re-cast it into
an operating-system frame built from HTML template features.  The mapping the
user asked for is implemented literally:

    Rails design   ->  OS design          (a scaffold resource -> an OS app)
    function       ->  object             (a controller action -> an object method)
    View (ERB)     ->  Window template    (index/show/new  -> HTML windows)
    Route          ->  OS menu entry
    hardware       ->  software driver    (each resource gets a soft-driver stub)

The output is an :class:`OSApp`: an object schema (from the Model), a set of
HTML window templates (from the Views), method names (from the Controller),
and menu routes — ready to be opened as windows on w9wm.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape

# A standard Rails RESTful controller exposes these 7 actions.
REST_ACTIONS = ("index", "show", "new", "create", "edit", "update", "destroy")


@dataclass
class RailsField:
    name: str
    type: str = "string"     # string, integer, boolean, text, references...


@dataclass
class RailsResource:
    name: str                            # singular, e.g. "article"
    fields: list[RailsField] = field(default_factory=list)
    actions: tuple = REST_ACTIONS

    @property
    def plural(self) -> str:
        return self.name + ("es" if self.name.endswith("s") else "s")


@dataclass
class OSApp:
    name: str
    object_schema: dict                  # function -> object: the model as data
    methods: list                        # function -> object: action -> method
    windows: dict                        # view -> window template (html)
    routes: list                         # route -> menu entry
    driver: str                          # hardware -> software driver stub


class RailsToOS:
    """Transpile a Rails scaffold resource into an OS application."""

    def transpile(self, res: RailsResource) -> OSApp:
        schema = {f.name: f.type for f in res.fields}
        methods = [f"{res.name}.{a}()" for a in res.actions]
        windows = {
            "index": self._index_template(res),
            "show": self._show_template(res),
            "new": self._form_template(res),
        }
        routes = [f"/{res.plural}"] + [
            f"/{res.plural}/{a}" for a in res.actions if a not in
            ("index", "create", "update", "destroy")]
        driver = self._soft_driver(res)
        return OSApp(name=res.plural, object_schema=schema, methods=methods,
                     windows=windows, routes=routes, driver=driver)

    # -- view -> window HTML templates -------------------------------------
    def _index_template(self, res: RailsResource) -> str:
        cols = "".join(f"<th>{escape(f.name)}</th>" for f in res.fields)
        row = "".join(f"<td>{{{{{f.name}}}}}</td>" for f in res.fields)
        return (f'<section class="os-window" data-app="{res.plural}">'
                f'<h2>{escape(res.plural.title())}</h2>'
                f'<table class="os-table"><tr>{cols}<th>actions</th></tr>'
                f'<tr>{row}<td>show | edit | destroy</td></tr></table>'
                f'<a class="os-btn" href="/{res.plural}/new">+ new</a>'
                f'</section>')

    def _show_template(self, res: RailsResource) -> str:
        rows = "".join(
            f'<dt>{escape(f.name)}</dt><dd>{{{{{f.name}}}}}</dd>'
            for f in res.fields)
        return (f'<section class="os-window" data-app="{res.plural}">'
                f'<h2>{escape(res.name.title())}</h2>'
                f'<dl class="os-detail">{rows}</dl></section>')

    def _form_template(self, res: RailsResource) -> str:
        inputs = "".join(
            f'<label>{escape(f.name)}'
            f'<input type="{self._html_input(f.type)}" name="{f.name}"></label>'
            for f in res.fields)
        return (f'<section class="os-window" data-app="{res.plural}">'
                f'<h2>New {escape(res.name.title())}</h2>'
                f'<form class="os-form" method="post" action="/{res.plural}">'
                f'{inputs}<button class="os-btn">create</button>'
                f'</form></section>')

    @staticmethod
    def _html_input(rails_type: str) -> str:
        return {"integer": "number", "boolean": "checkbox",
                "text": "text", "string": "text"}.get(rails_type, "text")

    # -- hardware -> software driver stub ----------------------------------
    @staticmethod
    def _soft_driver(res: RailsResource) -> str:
        # The physical device the resource stands for is virtualised as a
        # software driver object the OS can bind without real hardware.
        return f"soft_driver({res.name}) bound -> /dev/soft/{res.plural}"
