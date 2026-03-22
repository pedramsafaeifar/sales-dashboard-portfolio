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
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem 1.2rem;
        border-radius: 12px;
        color: white;
    }
    div[data-testid="stMetric"] label { color: rgba(255,255,255,0.8) !important; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: white !important; }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] svg { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Database Setup ───────────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "sales.db")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def init_db():
    """Create SQLite DB from CSV files if it doesn't exist."""
    if os.path.exists(DB_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    schema_path = os.path.join(os.path.dirname(__file__), "sql", "01_schema.sql")
    # SQLite-compatible schema (strip Postgres-specific syntax)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS regions (
            region_id INTEGER PRIMARY KEY, region_name TEXT, country TEXT, city TEXT
        );
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY, first_name TEXT, last_name TEXT,
            email TEXT UNIQUE, region_id INTEGER, segment TEXT, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY, category_name TEXT, department TEXT
        );
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY, product_name TEXT, category_id INTEGER,
            unit_cost REAL, unit_price REAL, stock_qty INTEGER
        );
        CREATE TABLE IF NOT EXISTS employees (
            employee_id INTEGER PRIMARY KEY, full_name TEXT, role TEXT,
            region_id INTEGER, hire_date TEXT, quota REAL
        );
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY, customer_id INTEGER, employee_id INTEGER,
            order_date TEXT, status TEXT, channel TEXT
        );
        CREATE TABLE IF NOT EXISTS order_items (
            item_id INTEGER PRIMARY KEY, order_id INTEGER, product_id INTEGER,
            quantity INTEGER, unit_price REAL, discount REAL
        );
        CREATE TABLE IF NOT EXISTS returns (
            return_id INTEGER PRIMARY KEY, order_id INTEGER, item_id INTEGER,
            return_date TEXT, reason TEXT
        );
    """)
    tables = ["regions", "categories", "products", "employees", "customers", "orders", "order_items", "returns"]
    for table in tables:
        csv_path = os.path.join(DATA_DIR, f"{table}.csv")
        if not os.path.exists(csv_path):
            continue
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            placeholders = ",".join(["?"] * len(headers))
            for row in reader:
                conn.execute(f"INSERT INTO {table} ({','.join(headers)}) VALUES ({placeholders})", row)
    conn.commit()
    conn.close()


@st.cache_resource
def get_connection():
    init_db()
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def query(sql, conn):
    return pd.read_sql_query(sql, conn)


# ── Init ─────────────────────────────────────────────────────────────

conn = get_connection()

# ── Sidebar Filters ──────────────────────────────────────────────────

st.sidebar.title("🎛️ Filters")

date_range = st.sidebar.date_input(
    "Date Range",
    value=(datetime(2024, 1, 1), datetime(2025, 12, 31)),
    min_value=datetime(2023, 1, 1),
    max_value=datetime(2025, 12, 31),
)
if len(date_range) == 2:
    d_start, d_end = date_range
else:
    d_start, d_end = datetime(2024, 1, 1), datetime(2025, 12, 31)

regions_list = query("SELECT DISTINCT region_name FROM regions ORDER BY 1", conn)["region_name"].tolist()
sel_regions = st.sidebar.multiselect("Region", regions_list, default=regions_list)

channels = st.sidebar.multiselect("Channel", ["Online", "In-Store", "Phone"], default=["Online", "In-Store", "Phone"])

# Build filter clause
region_filter = "(" + ",".join(f"'{r}'" for r in sel_regions) + ")" if sel_regions else "('__none__')"
channel_filter = "(" + ",".join(f"'{c}'" for c in channels) + ")" if channels else "('__none__')"
date_clause = f"o.order_date BETWEEN '{d_start}' AND '{d_end}'"
base_filter = f"{date_clause} AND o.status='Completed' AND r.region_name IN {region_filter} AND o.channel IN {channel_filter}"

# ── Header ───────────────────────────────────────────────────────────

st.title("📊 Sales & Operations Command Center")
st.caption(f"Data from {d_start.strftime('%b %d, %Y')} to {d_end.strftime('%b %d, %Y')}")

# ── KPI Cards ────────────────────────────────────────────────────────

kpi = query(f"""
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
""", conn)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${kpi['revenue'].iloc[0]:,.0f}")
col2.metric("Total Orders", f"{kpi['orders'].iloc[0]:,}")
col3.metric("Unique Customers", f"{kpi['customers'].iloc[0]:,}")
col4.metric("Avg Item Value", f"${kpi['avg_item_value'].iloc[0]:,.2f}")

st.divider()

# ── Row 1: Revenue Trend & Sales by Region ───────────────────────────

r1c1, r1c2 = st.columns([3, 2])

with r1c1:
    st.subheader("Revenue Trend")
    trend = query(f"""
        SELECT
            SUBSTR(o.order_date, 1, 7) AS month,
            SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN regions r ON r.region_id = c.region_id
        WHERE {base_filter}
        GROUP BY SUBSTR(o.order_date, 1, 7)
        ORDER BY month
    """, conn)
    if not trend.empty:
        fig = px.area(trend, x="month", y="revenue",
                      color_discrete_sequence=["#667eea"],
                      labels={"month": "", "revenue": "Revenue ($)"})
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=320,
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.1)")
        st.plotly_chart(fig, use_container_width=True)

with r1c2:
    st.subheader("Revenue by Region")
    by_region = query(f"""
        SELECT r.region_name, SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN regions r ON r.region_id = c.region_id
        WHERE {base_filter}
        GROUP BY r.region_name ORDER BY revenue DESC
    """, conn)
    if not by_region.empty:
        fig = px.bar(by_region, x="revenue", y="region_name", orientation="h",
                     color="revenue", color_continuous_scale="Purples",
                     labels={"region_name": "", "revenue": "Revenue ($)"})
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=320,
                          showlegend=False, coloraxis_showscale=False,
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True)

# ── Row 2: Product Performance & Category Mix ───────────────────────

r2c1, r2c2 = st.columns([3, 2])

with r2c1:
    st.subheader("Top 10 Products by Revenue")
    products = query(f"""
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
    """, conn)
    if not products.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(y=products["product_name"], x=products["revenue"],
                             name="Revenue", orientation="h", marker_color="#667eea"))
        fig.add_trace(go.Bar(y=products["product_name"], x=products["profit"],
                             name="Profit", orientation="h", marker_color="#f093fb"))
        fig.update_layout(barmode="overlay", margin=dict(l=0, r=0, t=10, b=0), height=380,
                          legend=dict(orientation="h", y=1.02, x=0),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True)

with r2c2:
    st.subheader("Revenue by Category")
    cats = query(f"""
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
    """, conn)
    if not cats.empty:
        fig = px.treemap(cats, path=["category_name"], values="revenue",
                         color="revenue", color_continuous_scale="Purples")
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=380,
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

# ── Row 3: Employee Leaderboard & Channel Performance ────────────────

r3c1, r3c2 = st.columns(2)

with r3c1:
    st.subheader("Sales Rep Leaderboard")
    reps = query(f"""
        SELECT e.full_name,
               e.quota,
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
    """, conn)
    if not reps.empty:
        reps["attainment"] = (reps["revenue"] / reps["quota"] * 100).round(1)
        fig = go.Figure()
        colors = ["#22c55e" if a >= 100 else "#eab308" if a >= 70 else "#ef4444"
                  for a in reps["attainment"]]
        fig.add_trace(go.Bar(
            y=reps["full_name"], x=reps["attainment"], orientation="h",
            marker_color=colors,
            text=reps["attainment"].apply(lambda x: f"{x}%"),
            textposition="outside",
        ))
        fig.add_vline(x=100, line_dash="dash", line_color="white", opacity=0.5)
        fig.update_layout(margin=dict(l=0, r=40, t=10, b=0), height=420,
                          xaxis_title="Quota Attainment %",
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True)

with r3c2:
    st.subheader("Channel Performance")
    funnel = query(f"""
        SELECT
            o.channel,
            COUNT(*) AS total_orders,
            SUM(CASE WHEN o.status = 'Completed' THEN 1 ELSE 0 END) AS completed,
            SUM(CASE WHEN o.status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled,
            SUM(CASE WHEN o.status = 'Completed' THEN oi.quantity * oi.unit_price * (1 - oi.discount) ELSE 0 END) AS revenue
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN regions r ON r.region_id = c.region_id
        WHERE {date_clause} AND r.region_name IN {region_filter} AND o.channel IN {channel_filter}
        GROUP BY o.channel
    """, conn)
    if not funnel.empty:
        funnel["conversion"] = (funnel["completed"] / funnel["total_orders"] * 100).round(1)
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Completed", x=funnel["channel"], y=funnel["completed"], marker_color="#667eea"))
        fig.add_trace(go.Bar(name="Cancelled", x=funnel["channel"], y=funnel["cancelled"], marker_color="#ef4444"))
        fig.update_layout(barmode="stack", margin=dict(l=0, r=0, t=10, b=0), height=200,
                          legend=dict(orientation="h", y=1.15, x=0),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Customer Segments")
    seg = query(f"""
        SELECT c.segment,
               COUNT(DISTINCT c.customer_id) AS customers,
               SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN regions r ON r.region_id = c.region_id
        WHERE {base_filter}
        GROUP BY c.segment
    """, conn)
    if not seg.empty:
        fig = px.pie(seg, names="segment", values="revenue",
                     color_discrete_sequence=["#667eea", "#f093fb", "#a78bfa"],
                     hole=0.45)
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=200)
        st.plotly_chart(fig, use_container_width=True)

# ── Row 4: Inventory & Returns ───────────────────────────────────────

r4c1, r4c2 = st.columns(2)

with r4c1:
    st.subheader("Inventory Alerts")
    inv = query("""
        SELECT p.product_name, cat.category_name, p.stock_qty,
               CASE WHEN p.stock_qty <= 10 THEN 'CRITICAL'
                    WHEN p.stock_qty <= 50 THEN 'LOW' ELSE 'OK' END AS status
        FROM products p
        JOIN categories cat ON cat.category_id = p.category_id
        WHERE p.stock_qty <= 50
        ORDER BY p.stock_qty ASC
    """, conn)
    if not inv.empty:
        def highlight_status(row):
            if row["status"] == "CRITICAL":
                return ["background-color: rgba(239,68,68,0.2)"] * len(row)
            elif row["status"] == "LOW":
                return ["background-color: rgba(234,179,8,0.2)"] * len(row)
            return [""] * len(row)
        st.dataframe(inv.style.apply(highlight_status, axis=1), use_container_width=True, height=350)
    else:
        st.success("All products well stocked!")

with r4c2:
    st.subheader("Return Reasons")
    returns = query(f"""
        SELECT ret.reason, COUNT(*) AS count
        FROM returns ret
        JOIN orders o ON o.order_id = ret.order_id
        JOIN order_items oi ON oi.item_id = ret.item_id
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN regions r ON r.region_id = c.region_id
        WHERE o.order_date BETWEEN '{d_start}' AND '{d_end}'
              AND r.region_name IN {region_filter}
        GROUP BY ret.reason ORDER BY count DESC
    """, conn)
    if not returns.empty:
        fig = px.bar(returns, x="reason", y="count",
                     color="reason",
                     color_discrete_sequence=["#ef4444","#f97316","#eab308","#667eea","#a78bfa"])
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=350,
                          showlegend=False,
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True)

# ── Footer ───────────────────────────────────────────────────────────

st.divider()
st.caption("Built with SQL + Python + Streamlit · Data is synthetic · [View SQL Queries on GitHub](#)")
