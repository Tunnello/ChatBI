import sqlite3
import random
from faker import Faker
import os
current_file_dir = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH         = os.path.join(current_file_dir, "example.db")  # 替换为你的数据库文件路径
# SQLite 数据库文件路径
database_path = DATABASE_PATH

# 初始化 Faker 库，用于生成随机数据
fake = Faker()

# 创建表的 SQL 语句
def create_tables():
    queries = [
        """
        CREATE TABLE IF NOT EXISTS CUSTOMER_DETAILS (
            CUSTOMER_ID INTEGER PRIMARY KEY,
            FIRST_NAME TEXT,
            LAST_NAME TEXT,
            EMAIL TEXT,
            PHONE TEXT,
            ADDRESS TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS ORDER_DETAILS (
            ORDER_ID INTEGER PRIMARY KEY,
            CUSTOMER_ID INTEGER,
            ORDER_DATE TEXT,
            TOTAL_AMOUNT REAL,
            FOREIGN KEY (CUSTOMER_ID) REFERENCES CUSTOMER_DETAILS(CUSTOMER_ID)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS PAYMENTS (
            PAYMENT_ID INTEGER PRIMARY KEY,
            ORDER_ID INTEGER,
            PAYMENT_DATE TEXT,
            AMOUNT REAL,
            FOREIGN KEY (ORDER_ID) REFERENCES ORDER_DETAILS(ORDER_ID)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS PRODUCTS (
            PRODUCT_ID INTEGER PRIMARY KEY,
            PRODUCT_NAME TEXT,
            CATEGORY TEXT,
            PRICE REAL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS TRANSACTIONS (
            TRANSACTION_ID INTEGER PRIMARY KEY,
            ORDER_ID INTEGER,
            PRODUCT_ID INTEGER,
            QUANTITY INTEGER,
            PRICE REAL,
            FOREIGN KEY (ORDER_ID) REFERENCES ORDER_DETAILS(ORDER_ID),
            FOREIGN KEY (PRODUCT_ID) REFERENCES PRODUCTS(PRODUCT_ID)
        );
        """
    ]

    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    for query in queries:
        cursor.execute(query)
    conn.commit()
    conn.close()

# 生成示例数据
def generate_sample_data(num_customers=10, num_orders=10, num_products=10):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # 插入 CUSTOMER_DETAILS 数据
    for i in range(1, num_customers + 1):
        cursor.execute(
            "INSERT INTO CUSTOMER_DETAILS (CUSTOMER_ID, FIRST_NAME, LAST_NAME, EMAIL, PHONE, ADDRESS) VALUES (?, ?, ?, ?, ?, ?)",
            (i, fake.first_name(), fake.last_name(), fake.email(), fake.phone_number(), fake.address())
        )

    # 插入 PRODUCTS 数据
    categories = ["Electronics", "Accessories", "Home Appliances"]
    for i in range(1, num_products + 1):
        cursor.execute(
            "INSERT INTO PRODUCTS (PRODUCT_ID, PRODUCT_NAME, CATEGORY, PRICE) VALUES (?, ?, ?, ?)",
            (i, fake.word().capitalize(), random.choice(categories), round(random.uniform(10, 1000), 2))
        )

    # 插入 ORDER_DETAILS 和 TRANSACTIONS 数据
    for i in range(1, num_orders + 1):
        customer_id = random.randint(1, num_customers)
        order_date = fake.date_this_year().isoformat()
        total_amount = round(random.uniform(50, 500), 2)

        cursor.execute(
            "INSERT INTO ORDER_DETAILS (ORDER_ID, CUSTOMER_ID, ORDER_DATE, TOTAL_AMOUNT) VALUES (?, ?, ?, ?)",
            (i, customer_id, order_date, total_amount)
        )

        # 插入 TRANSACTIONS 数据
        num_items = random.randint(1, 5)
        for _ in range(num_items):
            product_id = random.randint(1, num_products)
            quantity = random.randint(1, 10)
            price = round(random.uniform(10, 100), 2)

            cursor.execute(
                "INSERT INTO TRANSACTIONS (TRANSACTION_ID, ORDER_ID, PRODUCT_ID, QUANTITY, PRICE) VALUES (?, ?, ?, ?, ?)",
                (None, i, product_id, quantity, price)
            )

    # 插入 PAYMENTS 数据
    for i in range(1, num_orders + 1):
        payment_date = fake.date_this_year().isoformat()
        amount = round(random.uniform(50, 500), 2)

        cursor.execute(
            "INSERT INTO PAYMENTS (PAYMENT_ID, ORDER_ID, PAYMENT_DATE, AMOUNT) VALUES (?, ?, ?, ?)",
            (None, i, payment_date, amount)
        )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    generate_sample_data(num_customers=10, num_orders=10, num_products=10)
    print("Database and sample data created successfully!")
