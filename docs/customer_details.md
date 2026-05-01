**Table 1: STREAM_HACKATHON.STREAMLIT.CUSTOMER_DETAILS** (Stores customer information)

This table contains the personal information of customers who have made purchases on the platform, including purchase behavior analytics.

- CUSTOMER_ID: Number (38,0) [Primary Key, Not Null] - Unique identifier for customers
- FIRST_NAME: Varchar (255) - First name of the customer
- LAST_NAME: Varchar (255) - Last name of the customer
- EMAIL: Varchar (255) - Email address of the customer
- PHONE: Varchar (20) - Phone number of the customer
- ADDRESS: Varchar (255) - Physical address of the customer
- REGISTRATION_DATE: Date - Date when the customer registered on the platform
- FIRST_PURCHASE_DATE: Date - Date of the customer's first purchase
- LAST_PURCHASE_DATE: Date - Date of the customer's most recent purchase
- TOTAL_PURCHASE_COUNT: Integer - Total number of orders placed by the customer
- TOTAL_PURCHASE_AMOUNT: Number (10,2) - Total amount spent by the customer across all orders
- LOYALTY_LEVEL: Varchar (50) - Customer loyalty tier (e.g., Bronze, Silver, Gold, Platinum)
- AVERAGE_ORDER_VALUE: Number (10,2) - Average value of orders placed by the customer