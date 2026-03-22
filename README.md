# Sales & Operations Command Center

A full-stack SQL analytics dashboard that simulates a real-world e-commerce business intelligence tool. Built to demonstrate end-to-end data engineering — from schema design and data generation to complex analytical queries and interactive visualization.

**[Live Demo](#)** · Replace with your Streamlit Cloud URL after deployment

![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square&logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-SQLite-003b57?style=flat-square&logo=sqlite&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-ff4b4b?style=flat-square&logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.18+-3f4f75?style=flat-square&logo=plotly&logoColor=white)

---

## What This Project Does

This dashboard answers the questions a sales manager, operations lead, or CEO asks every morning:

- **How is revenue trending?** — Monthly revenue with period-over-period comparison
- **Which regions are performing?** — Revenue breakdown across 12 cities in the US and Canada
- **What's selling and what's profitable?** — Top products by revenue with profit margin overlay
- **Are reps hitting quota?** — Leaderboard with color-coded attainment (green/yellow/red)
- **Which channels convert best?** — Online vs In-Store vs Phone completion rates
- **What's our customer mix?** — Revenue split by Consumer, Corporate, and Enterprise segments
- **Do we have stock problems?** — Real-time inventory alerts with critical/low status badges
- **Why are customers returning products?** — Return reason analysis by category

Everything is filterable by **date range**, **region**, and **sales channel** via the sidebar.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Streamlit App                     │
│              (app.py — dashboard UI)                 │
├─────────────────────────────────────────────────────┤
│                   SQLite Database                    │
│              (data/sales.db — query layer)           │
├─────────────────────────────────────────────────────┤
│                   CSV Data Layer                     │
│          (data/*.csv — generated records)            │
├─────────────────────────────────────────────────────┤
│               Data Generator Script                  │
│     (generate_data.py — synthetic data engine)       │
└─────────────────────────────────────────────────────┘
```

### Database Schema

8 normalized tables with proper foreign key relationships:

```
regions ──┬── customers ──── orders ──── order_items ──── products ──── categories
          │                   │              │
          └── employees ──────┘              └──── returns
```

- **regions** — 12 cities across 6 regions
- **customers** — 800 customers with segments (Consumer/Corporate/Enterprise)
- **products** — 41 products across 10 categories with cost and price data
- **employees** — 15 sales reps with quotas
- **orders** — 5,000 orders over 3 years (2023–2025), weighted toward recent dates
- **order_items** — 11,000+ line items with quantity, price, and discount
- **returns** — ~750 returns with 5 reason categories

## SQL Techniques Demonstrated

The `sql/` folder contains production-grade analytical queries showcasing:

| Technique | Where It's Used |
|---|---|
| Window functions (`LAG`, `NTILE`) | MoM growth calculation, RFM scoring |
| Common Table Expressions (CTEs) | Cohort retention, RFM segmentation |
| Self-joins | Cohort analysis — first purchase vs repeat activity |
| Conditional aggregation (`CASE`) | Funnel conversion, inventory status |
| Date arithmetic | Rolling 30-day sales, cohort month offsets |
| FILTER clause | Channel conversion rates |
| Subqueries with LEFT JOIN | Inventory days-of-stock, employee revenue |
| NULLIF for safe division | Margin %, quota attainment, averages |
| NTILE bucketing | RFM recency/frequency/monetary quartiles |

## Dashboard Design

The UI follows professional dashboard design principles:

- **Dark theme** — `#0f0f1a` base with `#1e1e2e` card surfaces, easy on the eyes
- **KPI cards** — Large hero numbers with color-coded left borders and period-over-period deltas
- **Consistent palette** — Indigo/purple color scale across all charts, semantic colors only for alerts (red = critical, amber = low, green = on-target)
- **Clean charts** — No 3D effects, no chart chrome, rounded bar corners, spline-smoothed lines, muted gridlines
- **Custom inventory table** — Sticky headers, scrollable body, pill-shaped status badges
- **Typography** — Inter font, strict size hierarchy (12px labels → 28px hero metrics), uppercase muted section labels
- **Interactive filters** — Sidebar date range, region, and channel selectors that update every panel in real time

## Getting Started

### Prerequisites

- Python 3.10+

### Installation

```bash
git clone https://github.com/pedramsafaeifar/sales-dashboard-portfolio.git
cd sales-dashboard-portfolio
pip install -r requirements.txt
```

### Generate Data (optional — CSVs are included)

```bash
python generate_data.py
```

This creates 8 CSV files in `data/` with realistic synthetic data using controlled randomness (seeded for reproducibility).

### Run the Dashboard

```bash
streamlit run app.py
```

The app automatically builds the SQLite database from the CSV files on first run. Open `http://localhost:8501` in your browser.

## Deployment

To get a free public URL for your portfolio:

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo, set `app.py` as the main file
4. Deploy — you'll get a permanent shareable link

## Project Structure

```
sales-dashboard-portfolio/
├── app.py                  # Streamlit dashboard application
├── generate_data.py        # Synthetic data generator
├── requirements.txt        # Python dependencies
├── .gitignore
├── .streamlit/
│   └── config.toml         # Dark theme configuration
├── sql/
│   ├── 01_schema.sql       # PostgreSQL-compatible schema
│   └── 02_analytics.sql    # 9 analytical queries
└── data/
    ├── regions.csv          # 12 rows
    ├── categories.csv       # 10 rows
    ├── products.csv         # 41 rows
    ├── employees.csv        # 15 rows
    ├── customers.csv        # 800 rows
    ├── orders.csv           # 5,000 rows
    ├── order_items.csv      # 11,232 rows
    └── returns.csv          # 748 rows
```

## Built With

- **SQL** — Schema design, complex analytical queries (CTEs, window functions, RFM analysis)
- **Python** — Data generation with controlled distributions
- **Streamlit** — Dashboard framework with interactive widgets
- **Plotly** — Charts and visualizations
- **SQLite** — Embedded database (PostgreSQL schema also included)
