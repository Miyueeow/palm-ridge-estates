# Palm Ridge Estates — Interactive Subdivision Map & Sales Analytics

A fictional real-estate subdivision, sited on real GPS coordinates near Lipa City, Batangas, built as a portfolio project combining **data analysis** and **AI-ready automation**.

The dataset is synthetic (no real property or buyer data is used), but the coordinates, lot layout, and sales dynamics are modeled to be realistic.

## What's in here

| Piece | What it shows |
|---|---|
| **Interactive lot map** (`docs/index.html`) | A subdivision plat-style map — lots rendered as colored plots by status (available / reserved / sold), with filters and a natural-language lot finder. Built with Leaflet.js. |
| **Sales analytics dashboard** (`docs/analytics.html`) | Sales velocity, a 3-month forecast, time-to-close metrics, an agent leaderboard, and phase inventory burn-down. Built with Chart.js on top of a pandas pipeline. |
| **Data pipeline** (`scripts/`) | Python scripts that generate the fictional dataset, compute the analytics, and build the static dashboards. |

## Project structure

```
palm-ridge-estates/
├── data/                    # generated CSVs + JSON (gitignored contents optional — see note below)
│   ├── lots.csv
│   ├── amenities.csv
│   ├── sales_log.csv
│   ├── lots.json
│   └── analytics.json
├── templates/               # HTML templates with data placeholders
│   ├── index_template.html
│   └── analytics_template.html
├── docs/                    # BUILT, self-contained dashboards (open these in a browser)
│   ├── index.html
│   └── analytics.html
├── scripts/
│   ├── generate_data.py     # step 1: generate the fictional dataset
│   ├── analyze.py           # step 2: compute sales analytics + forecast
│   └── build_dashboards.py  # step 3: inject data into the HTML templates
├── requirements.txt
├── .gitignore
└── README.md
```

> Note: `docs/` is used deliberately so this can be published for free with **GitHub Pages** (Settings → Pages → deploy from `docs/` folder) with zero extra setup.

## Setup

```bash
# 1. Clone and enter the project
git clone <your-repo-url>
cd palm-ridge-estates

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
```

## Running the pipeline

Run these in order — each step depends on the previous one's output:

```bash
python scripts/generate_data.py     # -> data/lots.csv, sales_log.csv, amenities.csv, lots.json
python scripts/analyze.py           # -> data/analytics.json
python scripts/build_dashboards.py  # -> docs/index.html, docs/analytics.html
```

Then just open `docs/index.html` or `docs/analytics.html` directly in a browser. Both are fully self-contained (data is embedded) — no local server required.

## Data model

**`lots.csv`** — one row per lot: `lot_id`, `block`, `phase`, `lat`, `lng`, `area_sqm`, `price_php`, `price_per_sqm`, `status`, `lot_type`, `bedrooms`, `distance_to_entrance_m`, `date_listed`, `date_reserved`, `date_sold`

**`sales_log.csv`** — event log: `lot_id`, `event` (listed / reserved / sold), `event_date`, `agent`

**`amenities.csv`** — subdivision POIs: `name`, `type`, `lat`, `lng`

## Roadmap / ideas for extending this

- Swap the rule-based "lot finder" in the map for a real Claude API call (natural language → ranked lot matches)
- Turn `analyze.py` into a scheduled job (cron / n8n) that regenerates `analytics.json` weekly and posts a digest to Slack/email
- Replace the linear-trend forecast with a proper time-series model (e.g. Prophet) once there's more historical data
- Add a `sales_log` ingestion step that could pull from a real CRM export

## License / disclaimer

All data in this repository is synthetic and generated for demonstration purposes. "Palm Ridge Estates" is not a real property.
