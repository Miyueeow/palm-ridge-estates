"""
Analytics & forecasting layer for Palm Ridge Estates.
Reads lots.csv + sales_log.csv, computes:
  - Monthly sales velocity & revenue (actuals)
  - 3-month forward forecast (linear trend on lots sold/month)
  - Time-to-close metrics (listed -> reserved -> sold), overall and by phase
  - Agent performance leaderboard
  - Phase-level inventory burn-down

Outputs a single analytics.json consumed by the dashboard HTML.
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")

lots = pd.read_csv(os.path.join(DATA_DIR, "lots.csv"), parse_dates=["date_listed", "date_reserved", "date_sold"])
sales_log = pd.read_csv(os.path.join(DATA_DIR, "sales_log.csv"), parse_dates=["event_date"])

TODAY = pd.Timestamp("2026-07-04")

# ---------------------------------------------------------------
# 1. Monthly sales velocity & revenue (actuals) from 'sold' events
# ---------------------------------------------------------------
sold_events = sales_log[sales_log["event"] == "sold"].copy()
sold_events = sold_events.merge(lots[["lot_id", "price_php", "phase"]], on="lot_id")
sold_events["month"] = sold_events["event_date"].dt.to_period("M").astype(str)

monthly = sold_events.groupby("month").agg(
    lots_sold=("lot_id", "count"),
    revenue=("price_php", "sum")
).reset_index().sort_values("month")

# Fill any gap months with zero within the observed range for a clean time series
if len(monthly) > 0:
    full_range = pd.period_range(monthly["month"].min(), monthly["month"].max(), freq="M").astype(str)
    monthly = monthly.set_index("month").reindex(full_range, fill_value=0).rename_axis("month").reset_index()

# ---------------------------------------------------------------
# 2. Forecast next 3 months (simple linear trend on lots_sold/month)
# ---------------------------------------------------------------
forecast = []
if len(monthly) >= 3:
    x = np.arange(len(monthly))
    y_count = monthly["lots_sold"].values
    y_rev = monthly["revenue"].values

    # linear fit, floor at 0 (can't sell negative lots)
    count_coef = np.polyfit(x, y_count, 1)
    rev_coef = np.polyfit(x, y_rev, 1)

    last_period = pd.Period(monthly["month"].iloc[-1], freq="M")
    for i in range(1, 4):
        future_x = len(monthly) - 1 + i
        pred_count = max(0, round(np.polyval(count_coef, future_x)))
        pred_rev = max(0, round(np.polyval(rev_coef, future_x)))
        future_month = (last_period + i).strftime("%Y-%m")
        forecast.append({"month": future_month, "lots_sold": int(pred_count), "revenue": int(pred_rev)})
else:
    forecast = []

# ---------------------------------------------------------------
# 3. Time-to-close metrics
# ---------------------------------------------------------------
closed = lots.dropna(subset=["date_listed"]).copy()
closed["days_listed_to_reserved"] = (closed["date_reserved"] - closed["date_listed"]).dt.days
closed["days_reserved_to_sold"] = (closed["date_sold"] - closed["date_reserved"]).dt.days
closed["days_listed_to_sold"] = (closed["date_sold"] - closed["date_listed"]).dt.days

overall_ttc = {
    "avg_days_listed_to_reserved": round(closed["days_listed_to_reserved"].mean(skipna=True), 1),
    "avg_days_reserved_to_sold": round(closed["days_reserved_to_sold"].mean(skipna=True), 1),
    "avg_days_listed_to_sold": round(closed["days_listed_to_sold"].mean(skipna=True), 1),
}

by_phase_ttc = (
    closed.groupby("phase")["days_listed_to_sold"]
    .mean()
    .round(1)
    .dropna()
    .to_dict()
)

# ---------------------------------------------------------------
# 4. Agent leaderboard
# ---------------------------------------------------------------
agent_sold = sold_events.groupby("agent").agg(
    lots_sold=("lot_id", "count"),
    revenue=("price_php", "sum")
).reset_index()

# average close time per agent (listed -> sold), via merge back to closed lots
agent_close = sales_log[sales_log["event"] == "listed"][["lot_id", "agent"]].merge(
    closed[["lot_id", "days_listed_to_sold"]], on="lot_id"
).dropna()
agent_avg_days = agent_close.groupby("agent")["days_listed_to_sold"].mean().round(1)

agent_leaderboard = []
for _, row in agent_sold.sort_values("revenue", ascending=False).iterrows():
    agent_leaderboard.append({
        "agent": row["agent"],
        "lots_sold": int(row["lots_sold"]),
        "revenue": int(row["revenue"]),
        "avg_days_to_close": float(agent_avg_days.get(row["agent"], 0))
    })

# ---------------------------------------------------------------
# 5. Phase inventory burn-down
# ---------------------------------------------------------------
phase_summary = []
for phase in sorted(lots["phase"].unique()):
    p = lots[lots["phase"] == phase]
    total = len(p)
    sold_n = (p["status"] == "sold").sum()
    reserved_n = (p["status"] == "reserved").sum()
    available_n = (p["status"] == "available").sum()
    phase_summary.append({
        "phase": int(phase),
        "total": int(total),
        "sold": int(sold_n),
        "reserved": int(reserved_n),
        "available": int(available_n),
        "pct_sold": round(sold_n / total * 100, 1)
    })

# ---------------------------------------------------------------
# 6. Headline KPIs
# ---------------------------------------------------------------
total_lots = len(lots)
total_sold = (lots["status"] == "sold").sum()
total_revenue = lots.loc[lots["status"] == "sold", "price_php"].sum()
remaining_inventory_value = lots.loc[lots["status"] == "available", "price_php"].sum()
avg_monthly_velocity = round(monthly["lots_sold"].mean(), 1) if len(monthly) else 0

kpis = {
    "total_lots": int(total_lots),
    "total_sold": int(total_sold),
    "pct_sold": round(total_sold / total_lots * 100, 1),
    "total_revenue": int(total_revenue),
    "remaining_inventory_value": int(remaining_inventory_value),
    "avg_monthly_velocity": avg_monthly_velocity,
}

# ---------------------------------------------------------------
# Assemble output
# ---------------------------------------------------------------
output = {
    "kpis": kpis,
    "monthly_actuals": monthly.to_dict(orient="records"),
    "forecast": forecast,
    "time_to_close": {
        "overall": overall_ttc,
        "by_phase": {str(k): v for k, v in by_phase_ttc.items()}
    },
    "agent_leaderboard": agent_leaderboard,
    "phase_summary": phase_summary,
}

with open(os.path.join(DATA_DIR, "analytics.json"), "w") as f:
    json.dump(output, f, indent=2, default=str)

print("KPIs:", kpis)
print("\nMonthly actuals (last 5):")
print(monthly.tail())
print("\nForecast (next 3 months):", forecast)
print("\nTime to close (overall):", overall_ttc)
print("\nAgent leaderboard:")
for a in agent_leaderboard:
    print(" ", a)
