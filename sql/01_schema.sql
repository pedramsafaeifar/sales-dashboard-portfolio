-- ============================================
-- Sales & Operations Command Center - Schema
-- ============================================

CREATE TABLE IF NOT EXISTS regions (
    region_id   SERIAL PRIMARY KEY,
    region_name VARCHAR(50) NOT NULL,
    country     VARCHAR(50) NOT NULL,
    city        VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id   SERIAL PRIMARY KEY,
    first_name    VARCHAR(50) NOT NULL,
    last_name     VARCHAR(50) NOT NULL,
    email         VARCHAR(150) UNIQUE NOT NULL,
    region_id     INT REFERENCES regions(region_id),
    segment       VARCHAR(20) NOT NULL CHECK (segment IN ('Consumer','Corporate','Enterprise')),
    created_at    DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
    category_id   SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    department    VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    product_id    SERIAL PRIMARY KEY,
    product_name  VARCHAR(200) NOT NULL,
    category_id   INT REFERENCES categories(category_id),
    unit_cost     NUMERIC(10,2) NOT NULL,
    unit_price    NUMERIC(10,2) NOT NULL,
    stock_qty     INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS employees (
    employee_id   SERIAL PRIMARY KEY,
    full_name     VARCHAR(100) NOT NULL,
    role          VARCHAR(50) NOT NULL,
    region_id     INT REFERENCES regions(region_id),
    hire_date     DATE NOT NULL,
    quota         NUMERIC(12,2) NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS orders (
    order_id      SERIAL PRIMARY KEY,
    customer_id   INT REFERENCES customers(customer_id),
    employee_id   INT REFERENCES employees(employee_id),
    order_date    DATE NOT NULL,
    status        VARCHAR(20) NOT NULL CHECK (status IN ('Completed','Pending','Cancelled')),
    channel       VARCHAR(20) NOT NULL CHECK (channel IN ('Online','In-Store','Phone'))
);

CREATE TABLE IF NOT EXISTS order_items (
    item_id       SERIAL PRIMARY KEY,
    order_id      INT REFERENCES orders(order_id),
    product_id    INT REFERENCES products(product_id),
    quantity      INT NOT NULL,
    unit_price    NUMERIC(10,2) NOT NULL,
    discount      NUMERIC(4,2) NOT NULL DEFAULT 0.00
);

CREATE TABLE IF NOT EXISTS returns (
    return_id     SERIAL PRIMARY KEY,
    order_id      INT REFERENCES orders(order_id),
    item_id       INT REFERENCES order_items(item_id),
    return_date   DATE NOT NULL,
    reason        VARCHAR(50) NOT NULL CHECK (reason IN ('Defective','Wrong Item','Changed Mind','Late Delivery','Other'))
);
