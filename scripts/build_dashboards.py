"""
Injects the generated data (data/lots.json, data/analytics.json) into the
docs/index.html and docs/analytics.html templates, so the dashboards are
fully self-contained static files (no server, no fetch calls needed).

Run this after generate_data.py and analyze.py.
"""

import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(SCRIPT_DIR, "..")
DATA_DIR = os.path.join(ROOT_DIR, "data")
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")

os.makedirs(DOCS_DIR, exist_ok=True)


def inject(template_path, placeholder, json_path, output_path):
    with open(json_path) as f:
        data = json.load(f)
    compact_json = json.dumps(data, separators=(",", ":"))

    with open(template_path) as f:
        html = f.read()

    if placeholder not in html:
        raise ValueError(f"Placeholder {placeholder} not found in {template_path}")

    html = html.replace(placeholder, compact_json)

    with open(output_path, "w") as f:
        f.write(html)

    print(f"Built {output_path} ({len(html):,} bytes)")


if __name__ == "__main__":
    inject(
        template_path=os.path.join(TEMPLATES_DIR, "index_template.html"),
        placeholder="__DATA_PLACEHOLDER__",
        json_path=os.path.join(DATA_DIR, "lots.json"),
        output_path=os.path.join(DOCS_DIR, "index.html"),
    )
    inject(
        template_path=os.path.join(TEMPLATES_DIR, "analytics_template.html"),
        placeholder="__ANALYTICS_PLACEHOLDER__",
        json_path=os.path.join(DATA_DIR, "analytics.json"),
        output_path=os.path.join(DOCS_DIR, "analytics.html"),
    )
