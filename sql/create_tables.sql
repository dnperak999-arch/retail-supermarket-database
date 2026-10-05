CREATE TABLE Role (
    role_id INTEGER PRIMARY KEY,
    role_name TEXT NOT NULL
);

CREATE TABLE User (
    user_id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT,
    role_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('Active', 'Inactive')),
    FOREIGN KEY (role_id) REFERENCES Role(role_id)
);

CREATE TABLE Customer (
    customer_id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    address TEXT
);

CREATE TABLE Supplier (
    supplier_id INTEGER PRIMARY KEY,
    supplier_name TEXT NOT NULL,
    contact_name TEXT,
    phone TEXT,
    email TEXT
);

CREATE TABLE Category (
    category_id INTEGER PRIMARY KEY,
    category_name TEXT NOT NULL
);

CREATE TABLE Product (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    barcode TEXT UNIQUE,
    description TEXT,
    FOREIGN KEY (category_id) REFERENCES Category(category_id),
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id)
);

CREATE TABLE Inventory (
    inventory_id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL UNIQUE,
    quantity_in_stock INTEGER NOT NULL CHECK (quantity_in_stock >= 0),
    reorder_level INTEGER NOT NULL CHECK (reorder_level >= 0),
    last_updated TEXT,
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

CREATE TABLE CustomerOrder (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    order_date TEXT,
    total_amount REAL NOT NULL CHECK (total_amount >= 0),
    order_status TEXT NOT NULL CHECK (order_status IN ('Pending', 'Completed')),
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id),
    FOREIGN KEY (user_id) REFERENCES User(user_id)
);

CREATE TABLE OrderItem (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    item_price REAL NOT NULL CHECK (item_price >= 0),
    FOREIGN KEY (order_id) REFERENCES CustomerOrder(order_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id),
    UNIQUE (order_id, product_id)
);

CREATE TABLE Payment (
    payment_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    payment_date TEXT,
    payment_method TEXT NOT NULL CHECK (payment_method IN ('Card', 'Cash')),
    payment_status TEXT NOT NULL CHECK (payment_status IN ('Paid', 'Pending')),
    amount REAL NOT NULL CHECK (amount >= 0),
    FOREIGN KEY (order_id) REFERENCES CustomerOrder(order_id)
);
