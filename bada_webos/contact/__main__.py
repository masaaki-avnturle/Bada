"""python3 -m contact [outdir] — generate the Contact Machine blueprint."""

import sys

from .app import ContactApp

outdir = sys.argv[1] if len(sys.argv) > 1 else "generated/contact"
app = ContactApp().generate()
print(app.report, end="")
for kind, path in app.save(outdir).items():
    print(f"wrote {kind}: {path}")
