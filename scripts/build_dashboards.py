"""
Injects the generated data (data/lots.json, data/analytics.json) into the
docs/index.html and docs/analytics.html templates, so the dashboards are
fully self-contained static files (no server, no fetch calls needed).

Also injects the Lot Finder API URL (from config.json) into index.html,
so the "Ask the Lot Finder" feature calls your deployed Vercel proxy.

Run this after generate_data.py and analyze.py.
"""

import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(SCRIPT_DIR, "..")
DATA_DIR = os.path.join(ROOT_DIR, "data")
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")

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


def inject_text(file_path, placeholder, value):
    with open(file_path) as f:
        html = f.read()
    if placeholder not in html:
        # already injected or not present — skip quietly
        return
    html = html.replace(placeholder, value)
    with open(file_path, "w") as f:
        f.write(html)
    print(f"Set {placeholder} -> {value} in {file_path}")


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

    # Inject the Lot Finder API URL from config.json, if present
    # (encoding="utf-8-sig" tolerates a BOM, which Windows tools like
    # PowerShell's Out-File -Encoding utf8 often add)
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8-sig") as f:
            config = json.load(f)
        api_url = config.get("lot_finder_api_url", "")
        if api_url:
            inject_text(
                file_path=os.path.join(DOCS_DIR, "index.html"),
                placeholder="__LOT_FINDER_API_URL__",
                value=api_url,
            )
        else:
            print("config.json found but 'lot_finder_api_url' is empty — lot finder will not work until you set it.")
    else:
        print(f"No config.json found at {CONFIG_PATH} — skipping API URL injection. "
              f"Copy config.example.json to config.json and set your Vercel URL.")