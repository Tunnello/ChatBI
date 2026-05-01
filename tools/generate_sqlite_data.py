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
            ADDRESS TEXT,
            REGISTRATION_DATE TEXT,
            FIRST_PURCHASE_DATE TEXT,
            LAST_PURCHASE_DATE TEXT,
            TOTAL_PURCHASE_COUNT INTEGER DEFAULT 0,
            TOTAL_PURCHASE_AMOUNT REAL DEFAULT 0,
            LOYALTY_LEVEL TEXT,
            AVERAGE_ORDER_VALUE REAL
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
        """,
        """
        CREATE TABLE IF NOT EXISTS USER_INTERACTIONS (
            INTERACTION_ID INTEGER PRIMARY KEY,
            CUSTOMER_ID INTEGER,
            SESSION_ID TEXT,
            INTERACTION_TYPE TEXT,
            INTERACTION_DATE TEXT,
            PRODUCT_ID INTEGER,
            PAGE_URL TEXT,
            SEARCH_QUERY TEXT,
            ADDED_TO_CART INTEGER DEFAULT 0,
            PURCHASE_COMPLETED INTEGER DEFAULT 0,
            DURATION_SECONDS INTEGER,
            FOREIGN KEY (CUSTOMER_ID) REFERENCES CUSTOMER_DETAILS(CUSTOMER_ID),
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
def generate_sample_data(num_customers=10, num_orders=10, num_products=10, num_interactions=100):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # 插入 CUSTOMER_DETAILS 数据（先不包含购买行为字段，后面会更新）
    customer_registration_dates = {}
    for i in range(1, num_customers + 1):
        registration_date = fake.date_between(start_date='-2y', end_date='today')
        customer_registration_dates[i] = registration_date
        cursor.execute(
            "INSERT INTO CUSTOMER_DETAILS (CUSTOMER_ID, FIRST_NAME, LAST_NAME, EMAIL, PHONE, ADDRESS, REGISTRATION_DATE) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (i, fake.first_name(), fake.last_name(), fake.email(), fake.phone_number(), fake.address(), registration_date.isoformat())
        )

    # 插入 PRODUCTS 数据
    categories = ["Electronics", "Accessories", "Home Appliances"]
    for i in range(1, num_products + 1):
        cursor.execute(
            "INSERT INTO PRODUCTS (PRODUCT_ID, PRODUCT_NAME, CATEGORY, PRICE) VALUES (?, ?, ?, ?)",
            (i, fake.word().capitalize(), random.choice(categories), round(random.uniform(10, 1000), 2))
        )

    # 跟踪每个客户的订单信息，用于后续更新购买行为字段
    customer_orders = {i: [] for i in range(1, num_customers + 1)}
    
    # 插入 ORDER_DETAILS 和 TRANSACTIONS 数据
    for i in range(1, num_orders + 1):
        customer_id = random.randint(1, num_customers)
        # 确保订单日期在注册日期之后
        registration_date = customer_registration_dates[customer_id]
        order_date = fake.date_between(start_date=registration_date, end_date='today')
        total_amount = round(random.uniform(50, 500), 2)
        
        customer_orders[customer_id].append({
            'order_date': order_date,
            'total_amount': total_amount
        })

        cursor.execute(
            "INSERT INTO ORDER_DETAILS (ORDER_ID, CUSTOMER_ID, ORDER_DATE, TOTAL_AMOUNT) VALUES (?, ?, ?, ?)",
            (i, customer_id, order_date.isoformat(), total_amount)
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

    # 更新 CUSTOMER_DETAILS 的购买行为字段
    loyalty_levels = ['Bronze', 'Silver', 'Gold', 'Platinum']
    for customer_id, orders in customer_orders.items():
        if orders:
            # 按日期排序
            orders.sort(key=lambda x: x['order_date'])
            first_purchase_date = orders[0]['order_date']
            last_purchase_date = orders[-1]['order_date']
            total_purchase_count = len(orders)
            total_purchase_amount = sum(order['total_amount'] for order in orders)
            average_order_value = total_purchase_amount / total_purchase_count if total_purchase_count > 0 else 0
            
            # 根据总购买金额确定忠诚度等级
            if total_purchase_amount >= 5000:
                loyalty_level = 'Platinum'
            elif total_purchase_amount >= 2000:
                loyalty_level = 'Gold'
            elif total_purchase_amount >= 500:
                loyalty_level = 'Silver'
            else:
                loyalty_level = 'Bronze'
            
            cursor.execute(
                """UPDATE CUSTOMER_DETAILS 
                   SET FIRST_PURCHASE_DATE = ?, 
                       LAST_PURCHASE_DATE = ?, 
                       TOTAL_PURCHASE_COUNT = ?, 
                       TOTAL_PURCHASE_AMOUNT = ?, 
                       LOYALTY_LEVEL = ?, 
                       AVERAGE_ORDER_VALUE = ?
                   WHERE CUSTOMER_ID = ?""",
                (first_purchase_date.isoformat(), 
                 last_purchase_date.isoformat(), 
                 total_purchase_count, 
                 total_purchase_amount, 
                 loyalty_level, 
                 round(average_order_value, 2), 
                 customer_id)
            )

    # 生成用户交互数据
    interaction_types = ['click', 'search', 'view_product', 'add_to_cart', 'remove_from_cart', 'checkout_start', 'checkout_complete', 'page_view']
    pages = ['/home', '/products', '/product-detail', '/cart', '/checkout', '/search-results']
    
    for i in range(1, num_interactions + 1):
        customer_id = random.choice([None, random.randint(1, num_customers)])  # 有些交互可能是匿名用户
        session_id = fake.uuid4()
        interaction_type = random.choice(interaction_types)
        interaction_date = fake.date_time_between(start_date='-30d', end_date='now').isoformat()
        product_id = random.choice([None, random.randint(1, num_products)]) if interaction_type in ['view_product', 'add_to_cart', 'remove_from_cart'] else None
        page_url = random.choice(pages)
        search_query = fake.word() if interaction_type == 'search' else None
        added_to_cart = 1 if interaction_type == 'add_to_cart' else 0
        purchase_completed = 1 if interaction_type == 'checkout_complete' else 0
        duration_seconds = random.randint(5, 300) if interaction_type in ['view_product', 'page_view'] else None

        cursor.execute(
            """INSERT INTO USER_INTERACTIONS 
               (INTERACTION_ID, CUSTOMER_ID, SESSION_ID, INTERACTION_TYPE, INTERACTION_DATE, 
                PRODUCT_ID, PAGE_URL, SEARCH_QUERY, ADDED_TO_CART, PURCHASE_COMPLETED, DURATION_SECONDS) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (None, customer_id, session_id, interaction_type, interaction_date, 
             product_id, page_url, search_query, added_to_cart, purchase_completed, duration_seconds)
        )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    generate_sample_data(num_customers=20, num_orders=30, num_products=20, num_interactions=200)
    print("Database and sample data created successfully!")
