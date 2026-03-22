"""
Sales & Operations Command Center
Interactive Streamlit Dashboard powered by SQLite.
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import os
import csv
from datetime import datetime

# ── Page Config ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="Sales Command Center",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>S</text></svg>",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design Tokens ────────────────────────────────────────────────────

COLORS = {
    "bg":         "#0f0f1a",
    "card":       "#1e1e2e",
    "card_hover": "#2a2a3d",
    "border":     "#2e2e42",
    "text":       "#e0e0e0",
    "muted":      "#8b8b9e",
    "accent":     "#6366f1",
    "accent_light": "#818cf8",
    "success":    "#22c55e",
    "warning":    "#f59e0b",
    "danger":     "#ef4444",
    "chart_1":    "#6366f1",
    "chart_2":    "#8b5cf6",
    "chart_3":    "#a78bfa",
    "chart_4":    "#c4b5fd",
    "chart_5":    "#818cf8",
}

PLOTLY_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, DM Sans, sans-serif", size=12, color=COLORS["muted"]),
    margin=dict(l=0, r=0, t=8, b=0),
    hoverlabel=dict(
        bgcolor=COLORS["card"],
        font_size=13,
        font_family="Inter, DM Sans, sans-serif",
        bordercolor=COLORS["border"],
    ),
    xaxis=dict(showgrid=False, zeroline=False),
    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", zeroline=False),
)

# ── Custom CSS ───────────────────────────────────────────────────────

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    *, html, body, [class*="st-"] {{
        font-family: 'Inter', 'DM Sans', -apple-system, sans-serif !important;
    }}

    .block-container {{
        padding: 1.5rem 2rem 2rem 2rem;
        max-width: 1400px;
    }}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {{
        background: {COLORS["card"]};
        border-right: 1px solid {COLORS["border"]};
    }}
    section[data-testid="stSidebar"] .stMarkdown p {{
        font-size: 13px;
        color: {COLORS["muted"]};
    }}

    /* ── KPI Cards ── */
    .kpi-card {{
        background: {COLORS["card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 12px;
        padding: 20px 24px;
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
    }}
    .kpi-card:hover {{
        background: {COLORS["card_hover"]};
        border-color: {COLORS["accent"]};
        transform: translateY(-1px);
    }}
    .kpi-card::before {{
        content: '';
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 3px;
        border-radius: 12px 0 0 12px;
    }}
    .kpi-card.accent::before {{ background: {COLORS["accent"]}; }}
    .kpi-card.success::before {{ background: {COLORS["success"]}; }}
    .kpi-card.warning::before {{ background: {COLORS["warning"]}; }}
    .kpi-card.purple::before {{ background: {COLORS["chart_2"]}; }}
    .kpi-label {{
        font-size: 12px;
        font-weight: 500;
        color: {COLORS["muted"]};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }}
    .kpi-value {{
        font-size: 28px;
        font-weight: 700;
        color: {COLORS["text"]};
        line-height: 1.1;
    }}
    .kpi-delta {{
        font-size: 13px;
        font-weight: 500;
        margin-top: 6px;
    }}
    .kpi-delta.up {{ color: {COLORS["success"]}; }}
    .kpi-delta.down {{ color: {COLORS["danger"]}; }}

    /* ── Chart Cards ── */
    .chart-card {{
        background: {COLORS["card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 12px;
        padding: 20px 24px 16px 24px;
        margin-bottom: 24px;
    }}
    .chart-title {{
        font-size: 14px;
        font-weight: 600;
        color: {COLORS["text"]};
        margin-bottom: 16px;
    }}

    /* ── Hide default Streamlit metric styling ── */
    div[data-testid="stMetric"] {{
        display: none;
    }}

    /* ── Section titles ── */
    h1 {{
        font-size: 24px !important;
        font-weight: 700 !important;
        color: {COLORS["text"]} !important;
        margin-bottom: 4px !important;
    }}
    h2, h3 {{
        font-size: 14px !important;
        font-weight: 600 !important;
        color: {COLORS["text"]} !important;
    }}

    /* ── Streamlit elements ── */
    .stDivider {{
        border-color: {COLORS["border"]} !important;
    }}

    /* ── Table styling ── */
    .dataframe {{
        font-size: 13px !important;
    }}

    /* ── Sidebar filter labels ── */
    .stMultiSelect label, .stDateInput label {{
        font-size: 12px !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        color: {COLORS["muted"]} !important;
    }}

    /* ── Status badges ── */
    .badge {{
        display: inline-block;
        padding: 2px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }}
    .badge-critical {{ background: rgba(239,68,68,0.15); color: #f87171; }}
    .badge-low {{ background: rgba(245,158,11,0.15); color: #fbbf24; }}
    .badge-ok {{ background: rgba(34,197,94,0.15); color: #4ade80; }}

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-track {{ background: {COLORS["bg"]}; }}
    ::-webkit-scrollbar-thumb {{ background: {COLORS["border"]}; border-radius: 3px; }}
</style>
""", unsafe_allow_html=True)

# ── Database Setup ───────────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "sales.db")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def init_db():
    if os.path.exists(DB_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS regions (
            region_id INTEGER PRIMARY KEY, region_name TEXT, country TEXT, city TEXT);
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY, first_name TEXT, last_name TEXT,
            email TEXT UNIQUE, region_id INTEGER, segment TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY, category_name TEXT, department TEXT);
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY, product_name TEXT, category_id INTEGER,
            unit_cost REAL, unit_price REAL, stock_qty INTEGER);
        CREATE TABLE IF NOT EXISTS employees (
            employee_id INTEGER PRIMARY KEY, full_name TEXT, role TEXT,
            region_id INTEGER, hire_date TEXT, quota REAL);
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY, customer_id INTEGER, employee_id INTEGER,
            order_date TEXT, status TEXT, channel TEXT);
        CREATE TABLE IF NOT EXISTS order_items (
            item_id INTEGER PRIMARY KEY, order_id INTEGER, product_id INTEGER,
            quantity INTEGER, unit_price REAL, discount REAL);
        CREATE TABLE IF NOT EXISTS returns (
            return_id INTEGER PRIMARY KEY, order_id INTEGER, item_id INTEGER,
            return_date TEXT, reason TEXT);
    """)
    tables = ["regions", "categories", "products", "employees",
              "customers", "orders", "order_items", "returns"]
    for table in tables:
        csv_path = os.path.join(DATA_DIR, f"{table}.csv")
        if not os.path.exists(csv_path):
            continue
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            placeholders = ",".join(["?"] * len(headers))
            for row in reader:
                conn.execute(
                    f"INSERT INTO {table} ({','.join(headers)}) VALUES ({placeholders})", row)
    conn.commit()
    conn.close()


@st.cache_resource
def get_connection():
    init_db()
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def q(sql):
    return pd.read_sql_query(sql, conn)


conn = get_connection()

# ── Helpers ──────────────────────────────────────────────────────────

def kpi_card(label, value, delta=None, delta_dir="up", style="accent"):
    delta_html = ""
    if delta is not None:
        arrow = "+" if delta_dir == "up" else ""
        delta_html = f'<div class="kpi-delta {delta_dir}">{arrow}{delta}</div>'
    return f"""
    <div class="kpi-card {style}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """


def chart_card(title, chart_fig, height=340):
    st.markdown(f'<div class="chart-card"><div class="chart-title">{title}</div></div>',
                unsafe_allow_html=True)
    chart_fig.update_layout(**PLOTLY_LAYOUT, height=height)
    st.plotly_chart(chart_fig, use_container_width=True, config={"displayModeBar": False})


def apply_chart_style(fig, height=340):
    fig.update_layout(**PLOTLY_LAYOUT, height=height)
    return fig

# ── Sidebar ──────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Filters")
    st.markdown("---")

    date_range = st.date_input(
        "Date Range",
        value=(datetime(2024, 1, 1), datetime(2025, 12, 31)),
        min_value=datetime(2023, 1, 1),
        max_value=datetime(2025, 12, 31),
    )
    if len(date_range) == 2:
        d_start, d_end = date_range
    else:
        d_start, d_end = datetime(2024, 1, 1), datetime(2025, 12, 31)

    st.markdown("")
    regions_list = q("SELECT DISTINCT region_name FROM regions ORDER BY 1")["region_name"].tolist()
    sel_regions = st.multiselect("Region", regions_list, default=regions_list)

    st.markdown("")
    channels = st.multiselect("Channel", ["Online", "In-Store", "Phone"],
                              default=["Online", "In-Store", "Phone"])

    st.markdown("---")
    st.markdown(
        f'<p style="font-size:11px;color:{COLORS["muted"]};">'
        'Sales Command Center v1.0<br>Data is synthetic</p>',
        unsafe_allow_html=True
    )

# Build filter clause
region_filter = "(" + ",".join(f"'{r}'" for r in sel_regions) + ")" if sel_regions else "('__none__')"
channel_filter = "(" + ",".join(f"'{c}'" for c in channels) + ")" if channels else "('__none__')"
date_clause = f"o.order_date BETWEEN '{d_start}' AND '{d_end}'"
base_filter = (f"{date_clause} AND o.status='Completed' "
               f"AND r.region_name IN {region_filter} AND o.channel IN {channel_filter}")

# ── Header ───────────────────────────────────────────────────────────

st.markdown(
    f"""
    <div style="margin-bottom: 24px;">
        <h1 style="margin:0 !important; padding:0 !important;">Sales Command Center</h1>
        <p style="color:{COLORS['muted']}; font-size:13px; margin-top:4px;">
            {d_start.strftime('%b %d, %Y')} &mdash; {d_end.strftime('%b %d, %Y')}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── KPI Row ──────────────────────────────────────────────────────────

kpi_data = q(f"""
    SELECT
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue,
        COUNT(DISTINCT o.order_id) AS orders,
        COUNT(DISTINCT o.customer_id) AS customers,
        AVG(oi.quantity * oi.unit_price * (1 - oi.discount)) AS avg_item_value
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    JOIN customers c ON c.customer_id = o.customer_id
    JOIN regions r ON r.region_id = c.region_id
    WHERE {base_filter}
""")

# Previous period for deltas
prev_days = (d_end - d_start).days
prev_start = d_start.replace(year=d_start.year - 1) if d_start.year > 2023 else d_start
prev_end = d_end.replace(year=d_end.year - 1) if d_end.year > 2023 else d_end
prev_clause = f"o.order_date BETWEEN '{prev_start}' AND '{prev_end}'"
prev_filter = (f"{prev_clause} AND o.status='Completed' "
               f"AND r.region_name IN {region_filter} AND o.channel IN {channel_filter}")

kpi_prev = q(f"""
    SELECT
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue,
        COUNT(DISTINCT o.order_id) AS orders,
        COUNT(DISTINCT o.customer_id) AS customers
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    JOIN customers c ON c.customer_id = o.customer_id
    JOIN regions r ON r.region_id = c.region_id
    WHERE {prev_filter}
""")

def calc_delta(curr, prev):
    if prev and prev > 0:
        pct = ((curr - prev) / prev) * 100
        direction = "up" if pct >= 0 else "down"
        return f"{pct:+.1f}% vs prior period", direction
    return None, "up"

rev = kpi_data['revenue'].iloc[0] or 0
ord_count = kpi_data['orders'].iloc[0] or 0
cust = kpi_data['customers'].iloc[0] or 0
aov = kpi_data['avg_item_value'].iloc[0] or 0

rev_delta, rev_dir = calc_delta(rev, kpi_prev['revenue'].iloc[0])
ord_delta, ord_dir = calc_delta(ord_count, kpi_prev['orders'].iloc[0])
cust_delta, cust_dir = calc_delta(cust, kpi_prev['customers'].iloc[0])

k1, k2, k3, k4 = st.columns(4, gap="medium")
with k1:
    st.markdown(kpi_card("Total Revenue", f"${rev:,.0f}", rev_delta, rev_dir, "accent"),
                unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("Orders", f"{ord_count:,}", ord_delta, ord_dir, "success"),
                unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("Customers", f"{cust:,}", cust_delta, cust_dir, "purple"),
                unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card("Avg Item Value", f"${aov:,.2f}", style="warning"),
                unsafe_allow_html=True)

st.markdown("<div style='height: 32px'></div>", unsafe_allow_html=True)

# ── Row 1: Revenue Trend + Revenue by Region ────────────────────────

r1c1, r1c2 = st.columns([3, 2], gap="medium")

with r1c1:
    st.markdown('<div class="chart-card"><div class="chart-title">Revenue Trend</div>',
                unsafe_allow_html=True)
    trend = q(f"""
        SELECT SUBSTR(o.order_date, 1, 7) AS month,
               SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN regions r ON r.region_id = c.region_id
        WHERE {base_filter}
        GROUP BY SUBSTR(o.order_date, 1, 7)
        ORDER BY month
    """)
    if not trend.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend["month"], y=trend["revenue"],
            mode="lines",
            line=dict(color=COLORS["accent"], width=2.5, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(99,102,241,0.08)",
            hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
        ))
        apply_chart_style(fig, 300)
        fig.update_yaxes(tickprefix="$", tickformat=",")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with r1c2:
    st.markdown('<div class="chart-card"><div class="chart-title">Revenue by Region</div>',
                unsafe_allow_html=True)
    by_region = q(f"""
        SELECT r.region_name,
               SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN regions r ON r.region_id = c.region_id
        WHERE {base_filter}
        GROUP BY r.region_name ORDER BY revenue ASC
    """)
    if not by_region.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=by_region["region_name"], x=by_region["revenue"],
            orientation="h",
            marker=dict(
                color=by_region["revenue"],
                colorscale=[[0, COLORS["chart_4"]], [1, COLORS["chart_1"]]],
                cornerradius=4,
            ),
            hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<extra></extra>",
        ))
        apply_chart_style(fig, 300)
        fig.update_xaxes(tickprefix="$", tickformat=",")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

# ── Row 2: Top Products + Category Breakdown ────────────────────────

r2c1, r2c2 = st.columns([3, 2], gap="medium")

with r2c1:
    st.markdown('<div class="chart-card"><div class="chart-title">Top 10 Products</div>',
                unsafe_allow_html=True)
    products = q(f"""
        SELECT p.product_name,
               SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue,
               SUM(oi.quantity * (oi.unit_price * (1 - oi.discount) - p.unit_cost)) AS profit
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON p.product_id = oi.product_id
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN regions r ON r.region_id = c.region_id
        WHERE {base_filter}
        GROUP BY p.product_name ORDER BY revenue DESC LIMIT 10
    """)
    if not products.empty:
        products = products.iloc[::-1]  # reverse for horizontal bar
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=products["product_name"], x=products["revenue"],
            name="Revenue", orientation="h",
            marker=dict(color=COLORS["accent"], cornerradius=4, opacity=0.85),
            hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.0f}<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            y=products["product_name"], x=products["profit"],
            name="Profit", orientation="h",
            marker=dict(color=COLORS["success"], cornerradius=4, opacity=0.7),
            hovertemplate="<b>%{y}</b><br>Profit: $%{x:,.0f}<extra></extra>",
        ))
        apply_chart_style(fig, 380)
        fig.update_layout(
            barmode="overlay",
            legend=dict(
                orientation="h", y=1.06, x=0,
                font=dict(size=11, color=COLORS["muted"]),
                bgcolor="rgba(0,0,0,0)",
            ),
        )
        fig.update_xaxes(tickprefix="$", tickformat=",")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with r2c2:
    st.markdown('<div class="chart-card"><div class="chart-title">Revenue by Category</div>',
                unsafe_allow_html=True)
    cats = q(f"""
        SELECT cat.category_name,
               SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON p.product_id = oi.product_id
        JOIN categories cat ON cat.category_id = p.category_id
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN regions r ON r.region_id = c.region_id
        WHERE {base_filter}
        GROUP BY cat.category_name ORDER BY revenue DESC
    """)
    if not cats.empty:
        fig = go.Figure(go.Treemap(
            labels=cats["category_name"],
            parents=[""] * len(cats),
            values=cats["revenue"],
            marker=dict(
                colors=cats["revenue"],
                colorscale=[[0, "#312e81"], [0.5, "#6366f1"], [1, "#a78bfa"]],
                cornerradius=6,
            ),
            textinfo="label+percent root",
            textfont=dict(size=13, color="white"),
            hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percentRoot:.1%}<extra></extra>",
        ))
        apply_chart_style(fig, 380)
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

# ── Row 3: Sales Rep Leaderboard + Channel & Segments ────────────────

r3c1, r3c2 = st.columns(2, gap="medium")

with r3c1:
    st.markdown('<div class="chart-card"><div class="chart-title">Sales Rep Leaderboard</div>',
                unsafe_allow_html=True)
    reps = q(f"""
        SELECT e.full_name, e.quota,
               COALESCE(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 0) AS revenue,
               COUNT(DISTINCT o.order_id) AS deals
        FROM employees e
        LEFT JOIN orders o ON o.employee_id = e.employee_id
            AND {date_clause} AND o.status='Completed' AND o.channel IN {channel_filter}
        LEFT JOIN order_items oi ON oi.order_id = o.order_id
        LEFT JOIN customers c ON c.customer_id = o.customer_id
        LEFT JOIN regions r ON r.region_id = c.region_id AND r.region_name IN {region_filter}
        GROUP BY e.employee_id, e.full_name, e.quota
        ORDER BY revenue DESC
    """)
    if not reps.empty:
        reps["attainment"] = (reps["revenue"] / reps["quota"] * 100).round(1)
        reps = reps.iloc[::-1]  # reverse for horizontal bar
        colors = [COLORS["success"] if a >= 100
                  else COLORS["warning"] if a >= 70
                  else COLORS["danger"]
                  for a in reps["attainment"]]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=reps["full_name"], x=reps["attainment"], orientation="h",
            marker=dict(color=colors, cornerradius=4, opacity=0.85),
            text=reps["attainment"].apply(lambda x: f"{x}%"),
            textposition="outside",
            textfont=dict(size=11, color=COLORS["muted"]),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Attainment: %{x:.1f}%<extra></extra>"
            ),
        ))
        fig.add_vline(x=100, line_dash="dot", line_color=COLORS["muted"], opacity=0.3)
        apply_chart_style(fig, 420)
        fig.update_layout(xaxis_title=dict(text="Quota Attainment %",
                          font=dict(size=11, color=COLORS["muted"])))
        fig.update_xaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with r3c2:
    # Channel Performance
    st.markdown('<div class="chart-card"><div class="chart-title">Channel Performance</div>',
                unsafe_allow_html=True)
    funnel = q(f"""
        SELECT o.channel,
               COUNT(*) AS total_orders,
               SUM(CASE WHEN o.status='Completed' THEN 1 ELSE 0 END) AS completed,
               SUM(CASE WHEN o.status='Cancelled' THEN 1 ELSE 0 END) AS cancelled
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN regions r ON r.region_id = c.region_id
        WHERE {date_clause} AND r.region_name IN {region_filter} AND o.channel IN {channel_filter}
        GROUP BY o.channel
    """)
    if not funnel.empty:
        funnel["conversion"] = (funnel["completed"] / funnel["total_orders"] * 100).round(1)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Completed", x=funnel["channel"], y=funnel["completed"],
            marker=dict(color=COLORS["accent"], cornerradius=4),
            hovertemplate="<b>%{x}</b><br>Completed: %{y:,}<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            name="Cancelled", x=funnel["channel"], y=funnel["cancelled"],
            marker=dict(color="rgba(239,68,68,0.6)", cornerradius=4),
            hovertemplate="<b>%{x}</b><br>Cancelled: %{y:,}<extra></extra>",
        ))
        apply_chart_style(fig, 190)
        fig.update_layout(
            barmode="stack",
            legend=dict(orientation="h", y=1.2, x=0,
                        font=dict(size=11, color=COLORS["muted"]),
                        bgcolor="rgba(0,0,0,0)"),
        )
        fig.update_yaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

    # Customer Segments donut
    st.markdown('<div class="chart-card"><div class="chart-title">Customer Segments</div>',
                unsafe_allow_html=True)
    seg = q(f"""
        SELECT c.segment,
               COUNT(DISTINCT c.customer_id) AS customers,
               SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN regions r ON r.region_id = c.region_id
        WHERE {base_filter}
        GROUP BY c.segment
    """)
    if not seg.empty:
        fig = go.Figure(go.Pie(
            labels=seg["segment"], values=seg["revenue"],
            hole=0.55,
            marker=dict(
                colors=[COLORS["chart_1"], COLORS["chart_2"], COLORS["chart_3"]],
                line=dict(color=COLORS["card"], width=2),
            ),
            textinfo="label+percent",
            textfont=dict(size=12, color=COLORS["text"]),
            hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
        ))
        apply_chart_style(fig, 200)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

# ── Row 4: Inventory Alerts + Return Analysis ───────────────────────

r4c1, r4c2 = st.columns(2, gap="medium")

with r4c1:
    st.markdown('<div class="chart-card"><div class="chart-title">Inventory Alerts</div>',
                unsafe_allow_html=True)
    inv = q("""
        SELECT p.product_name AS "Product",
               cat.category_name AS "Category",
               p.stock_qty AS "Stock",
               CASE WHEN p.stock_qty <= 10 THEN 'CRITICAL'
                    WHEN p.stock_qty <= 50 THEN 'LOW' ELSE 'OK' END AS "Status"
        FROM products p
        JOIN categories cat ON cat.category_id = p.category_id
        WHERE p.stock_qty <= 50
        ORDER BY p.stock_qty ASC
    """)
    if not inv.empty:
        def make_badge(status):
            css_class = {"CRITICAL": "badge-critical", "LOW": "badge-low", "OK": "badge-ok"}
            return f'<span class="badge {css_class.get(status, "")}">{status}</span>'

        table_rows = ""
        for _, row in inv.iterrows():
            stock_color = COLORS["danger"] if row["Stock"] <= 10 else COLORS["warning"]
            table_rows += f"""
            <tr>
                <td style="padding:8px 12px; border-bottom:1px solid {COLORS['border']}; font-size:13px;">{row['Product']}</td>
                <td style="padding:8px 12px; border-bottom:1px solid {COLORS['border']}; font-size:13px; color:{COLORS['muted']}">{row['Category']}</td>
                <td style="padding:8px 12px; border-bottom:1px solid {COLORS['border']}; font-size:13px; color:{stock_color}; font-weight:600;">{row['Stock']}</td>
                <td style="padding:8px 12px; border-bottom:1px solid {COLORS['border']};">{make_badge(row['Status'])}</td>
            </tr>
            """
        st.markdown(f"""
        <div style="max-height:340px; overflow-y:auto; border-radius:8px;">
        <table style="width:100%; border-collapse:collapse;">
            <thead>
                <tr style="position:sticky; top:0; background:{COLORS['card']}; z-index:1;">
                    <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:{COLORS['muted']}; text-transform:uppercase; letter-spacing:0.5px; border-bottom:1px solid {COLORS['border']};">Product</th>
                    <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:{COLORS['muted']}; text-transform:uppercase; letter-spacing:0.5px; border-bottom:1px solid {COLORS['border']};">Category</th>
                    <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:{COLORS['muted']}; text-transform:uppercase; letter-spacing:0.5px; border-bottom:1px solid {COLORS['border']};">Stock</th>
                    <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:{COLORS['muted']}; text-transform:uppercase; letter-spacing:0.5px; border-bottom:1px solid {COLORS['border']};">Status</th>
                </tr>
            </thead>
            <tbody>{table_rows}</tbody>
        </table>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f'<p style="color:{COLORS["success"]}; font-size:13px;">All products well stocked.</p>',
                    unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r4c2:
    st.markdown('<div class="chart-card"><div class="chart-title">Return Reasons</div>',
                unsafe_allow_html=True)
    returns = q(f"""
        SELECT ret.reason, COUNT(*) AS count
        FROM returns ret
        JOIN orders o ON o.order_id = ret.order_id
        JOIN order_items oi ON oi.item_id = ret.item_id
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN regions r ON r.region_id = c.region_id
        WHERE o.order_date BETWEEN '{d_start}' AND '{d_end}'
              AND r.region_name IN {region_filter}
        GROUP BY ret.reason ORDER BY count DESC
    """)
    if not returns.empty:
        color_map = {
            "Defective": COLORS["danger"],
            "Wrong Item": COLORS["warning"],
            "Changed Mind": COLORS["chart_1"],
            "Late Delivery": COLORS["chart_2"],
            "Other": COLORS["chart_4"],
        }
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=returns["reason"], y=returns["count"],
            marker=dict(
                color=[color_map.get(r, COLORS["chart_3"]) for r in returns["reason"]],
                cornerradius=4,
                opacity=0.85,
            ),
            hovertemplate="<b>%{x}</b><br>Count: %{y:,}<extra></extra>",
        ))
        apply_chart_style(fig, 340)
        fig.update_yaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ───────────────────────────────────────────────────────────

st.markdown(f"""
<div style="text-align:center; padding:32px 0 16px 0; border-top:1px solid {COLORS['border']}; margin-top:32px;">
    <p style="font-size:12px; color:{COLORS['muted']}; margin:0;">
        Built with SQL &middot; Python &middot; Streamlit
    </p>
</div>
""", unsafe_allow_html=True)
