"""
Generate realistic synthetic data for the Sales & Operations Dashboard.
Outputs CSV files ready for import into any SQL database.
"""

import csv
import random
import os
from datetime import date, timedelta

random.seed(42)
OUT = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUT, exist_ok=True)

# ── Helpers ──────────────────────────────────────────────────────────

def write_csv(filename, headers, rows):
    path = os.path.join(OUT, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    print(f"  {filename}: {len(rows)} rows")


def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


# ── Config ───────────────────────────────────────────────────────────

START_DATE = date(2023, 1, 1)
END_DATE   = date(2025, 12, 31)

FIRST_NAMES = [
    "James","Mary","Robert","Linda","John","Barbara","Michael","Susan",
    "David","Jessica","William","Sarah","Richard","Karen","Joseph","Lisa",
    "Thomas","Nancy","Daniel","Betty","Matthew","Emily","Anthony","Olivia",
    "Mark","Amanda","Andrew","Melissa","Joshua","Stephanie","Kevin","Laura",
    "Brian","Rebecca","George","Sharon","Edward","Cynthia","Ronald","Kathleen",
    "Timothy","Amy","Jason","Angela","Jeffrey","Brenda","Ryan","Anna",
    "Jacob","Samantha","Gary","Katherine","Nicholas","Christine","Eric","Deborah",
    "Jonathan","Rachel","Stephen","Carolyn","Larry","Janet","Justin","Catherine",
    "Scott","Maria","Brandon","Heather","Benjamin","Diane","Samuel","Ruth",
]

LAST_NAMES = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
    "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson",
    "Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson",
    "White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson","Walker",
    "Young","Allen","King","Wright","Scott","Torres","Nguyen","Hill",
    "Flores","Green","Adams","Nelson","Baker","Hall","Rivera","Campbell",
    "Mitchell","Carter","Roberts","Gomez","Phillips","Evans","Turner","Diaz",
]

REGIONS = [
    ("Northeast", "USA", "New York"),
    ("Northeast", "USA", "Boston"),
    ("Southeast", "USA", "Miami"),
    ("Southeast", "USA", "Atlanta"),
    ("Midwest",   "USA", "Chicago"),
    ("Midwest",   "USA", "Detroit"),
    ("West",      "USA", "Los Angeles"),
    ("West",      "USA", "Seattle"),
    ("South",     "USA", "Dallas"),
    ("South",     "USA", "Houston"),
    ("Canada",    "Canada", "Toronto"),
    ("Canada",    "Canada", "Vancouver"),
]

CATEGORIES = [
    ("Laptops",          "Electronics"),
    ("Phones",           "Electronics"),
    ("Accessories",      "Electronics"),
    ("Office Furniture", "Office"),
    ("Office Supplies",  "Office"),
    ("Printers",         "Office"),
    ("Software",         "Technology"),
    ("Networking",       "Technology"),
    ("Storage",          "Technology"),
    ("Monitors",         "Electronics"),
]

PRODUCTS = {
    "Laptops":          [("ProBook 450 G10","899.99","549.00"), ("ThinkPad X1 Carbon","1349.99","820.00"), ("MacBook Air M3","1199.00","780.00"), ("Dell XPS 15","1299.99","790.00"), ("Surface Laptop 5","999.99","610.00")],
    "Phones":           [("iPhone 15 Pro","999.00","680.00"), ("Galaxy S24","849.99","520.00"), ("Pixel 8","699.00","420.00"), ("OnePlus 12","799.99","460.00")],
    "Accessories":      [("USB-C Hub","49.99","18.00"), ("Wireless Mouse","29.99","9.50"), ("Mechanical Keyboard","89.99","32.00"), ("Webcam HD","69.99","24.00"), ("Laptop Stand","39.99","14.00"), ("Headset Pro","129.99","52.00")],
    "Office Furniture": [("Standing Desk","599.99","280.00"), ("Ergonomic Chair","449.99","195.00"), ("Filing Cabinet","189.99","75.00"), ("Bookshelf","159.99","62.00")],
    "Office Supplies":  [("Paper Ream (10pk)","49.99","22.00"), ("Pen Set","12.99","3.50"), ("Stapler","9.99","2.80"), ("Binder Pack","19.99","6.50"), ("Whiteboard","79.99","30.00")],
    "Printers":         [("LaserJet Pro","349.99","165.00"), ("InkJet All-in-One","199.99","88.00"), ("Label Printer","129.99","55.00")],
    "Software":         [("Office 365 License","149.99","20.00"), ("Antivirus Suite","59.99","8.00"), ("Project Mgmt Tool","99.99","12.00"), ("Adobe Creative Cloud","599.99","80.00")],
    "Networking":       [("WiFi 6 Router","179.99","72.00"), ("Ethernet Switch 24p","249.99","105.00"), ("Network Cable Box","34.99","12.00")],
    "Storage":          [("1TB SSD","89.99","38.00"), ("4TB External HDD","109.99","48.00"), ("NAS 2-Bay","299.99","140.00"), ("USB Flash 64GB","14.99","4.50")],
    "Monitors":         [("27\" 4K Monitor","399.99","185.00"), ("34\" Ultrawide","549.99","260.00"), ("24\" FHD Monitor","199.99","90.00")],
}

SALES_REPS = [
    "Alex Turner","Jordan Blake","Morgan Hayes","Casey Rivera","Taylor Kim",
    "Riley Chen","Quinn Foster","Avery Patel","Jamie Reeves","Drew Sullivan",
    "Sam Nakamura","Chris Bergström","Pat Moreno","Logan Okafor","Skyler Dunn",
]

# ── Generate ─────────────────────────────────────────────────────────

print("Generating data...")

# Regions
regions = [(i+1, r, c, city) for i, (r, c, city) in enumerate(REGIONS)]
write_csv("regions.csv", ["region_id","region_name","country","city"], regions)

# Categories
categories = [(i+1, name, dept) for i, (name, dept) in enumerate(CATEGORIES)]
write_csv("categories.csv", ["category_id","category_name","department"], categories)

# Products
product_rows = []
pid = 1
cat_map = {name: i+1 for i, (name, _) in enumerate(CATEGORIES)}
for cat_name, items in PRODUCTS.items():
    for pname, price, cost in items:
        stock = random.randint(5, 300)
        product_rows.append((pid, pname, cat_map[cat_name], cost, price, stock))
        pid += 1
write_csv("products.csv", ["product_id","product_name","category_id","unit_cost","unit_price","stock_qty"], product_rows)

# Employees
emp_rows = []
for i, name in enumerate(SALES_REPS):
    rid = random.choice([r[0] for r in regions])
    hdate = random_date(date(2019,1,1), date(2023,6,1))
    quota = random.choice([150000, 200000, 250000, 300000, 350000])
    emp_rows.append((i+1, name, "Sales Rep", rid, hdate.isoformat(), quota))
write_csv("employees.csv", ["employee_id","full_name","role","region_id","hire_date","quota"], emp_rows)

# Customers
NUM_CUSTOMERS = 800
cust_rows = []
emails_seen = set()
for i in range(NUM_CUSTOMERS):
    fn = random.choice(FIRST_NAMES)
    ln = random.choice(LAST_NAMES)
    suffix = random.randint(1, 9999)
    email = f"{fn.lower()}.{ln.lower()}{suffix}@example.com"
    while email in emails_seen:
        suffix = random.randint(1, 9999)
        email = f"{fn.lower()}.{ln.lower()}{suffix}@example.com"
    emails_seen.add(email)
    rid = random.choice([r[0] for r in regions])
    seg = random.choices(["Consumer","Corporate","Enterprise"], weights=[50,35,15])[0]
    created = random_date(date(2020,1,1), date(2025,6,1))
    cust_rows.append((i+1, fn, ln, email, rid, seg, created.isoformat()))
write_csv("customers.csv", ["customer_id","first_name","last_name","email","region_id","segment","created_at"], cust_rows)

# Orders & Order Items
NUM_ORDERS = 5000
order_rows = []
item_rows = []
item_id = 1

# Weight orders toward more recent dates for realism
for oid in range(1, NUM_ORDERS + 1):
    cid = random.randint(1, NUM_CUSTOMERS)
    eid = random.randint(1, len(SALES_REPS))
    # bias toward recent dates
    days_ago = int(random.triangular(0, (END_DATE - START_DATE).days, 30))
    odate = END_DATE - timedelta(days=days_ago)
    if odate < START_DATE:
        odate = START_DATE
    status = random.choices(["Completed","Pending","Cancelled"], weights=[78,15,7])[0]
    channel = random.choices(["Online","In-Store","Phone"], weights=[60,30,10])[0]
    order_rows.append((oid, cid, eid, odate.isoformat(), status, channel))

    # 1-5 line items per order
    num_items = random.choices([1,2,3,4,5], weights=[30,35,20,10,5])[0]
    chosen_products = random.sample(product_rows, min(num_items, len(product_rows)))
    for prod in chosen_products:
        p_id, _, _, _, price, _ = prod
        qty = random.choices([1,2,3,5,10], weights=[40,30,15,10,5])[0]
        disc = random.choices([0.00, 0.05, 0.10, 0.15, 0.20], weights=[50,20,15,10,5])[0]
        item_rows.append((item_id, oid, p_id, qty, price, f"{disc:.2f}"))
        item_id += 1

write_csv("orders.csv", ["order_id","customer_id","employee_id","order_date","status","channel"], order_rows)
write_csv("order_items.csv", ["item_id","order_id","product_id","quantity","unit_price","discount"], item_rows)

# Returns (~8% of completed order items)
return_rows = []
ret_id = 1
completed_items = [
    (it, o) for it in item_rows for o in order_rows
    if o[0] == it[1] and o[3] >= START_DATE.isoformat() and o[4] == "Completed"
]
# flatten - match items to their orders
completed_map = {}
for o in order_rows:
    if o[4] == "Completed":
        completed_map[o[0]] = o
for it in item_rows:
    if it[1] in completed_map and random.random() < 0.08:
        o = completed_map[it[1]]
        odate = date.fromisoformat(o[3])
        rdate = odate + timedelta(days=random.randint(1, 30))
        if rdate > END_DATE:
            rdate = END_DATE
        reason = random.choice(["Defective","Wrong Item","Changed Mind","Late Delivery","Other"])
        return_rows.append((ret_id, o[0], it[0], rdate.isoformat(), reason))
        ret_id += 1

write_csv("returns.csv", ["return_id","order_id","item_id","return_date","reason"], return_rows)

print(f"\nDone! All CSV files saved to {OUT}/")
