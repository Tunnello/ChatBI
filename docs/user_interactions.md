**Table 6: STREAM_HACKATHON.STREAMLIT.USER_INTERACTIONS** (Stores user interaction data)

This table contains information about user interactions with the website, including clicks, searches, cart additions, and other behavioral events. This data is used for user interaction analysis to identify conversion barriers and UX optimization opportunities.

- INTERACTION_ID: Number (38,0) [Primary Key, Not Null] - Unique identifier for each interaction event
- CUSTOMER_ID: Number (38,0) [Foreign Key - CUSTOMER_DETAILS(CUSTOMER_ID)] - Customer who performed the interaction (nullable for anonymous users)
- SESSION_ID: Varchar (255) - Unique identifier for the user session
- INTERACTION_TYPE: Varchar (50) - Type of interaction (e.g., 'click', 'search', 'view_product', 'add_to_cart', 'remove_from_cart', 'checkout_start', 'checkout_complete', 'page_view')
- INTERACTION_DATE: Timestamp - Date and time when the interaction occurred
- PRODUCT_ID: Number (38,0) [Foreign Key - PRODUCTS(PRODUCT_ID)] - Product involved in the interaction (nullable)
- PAGE_URL: Varchar (500) - URL of the page where the interaction occurred
- SEARCH_QUERY: Text - Search query text if the interaction type is 'search'
- ADDED_TO_CART: Boolean - Whether the product was added to cart in this interaction
- PURCHASE_COMPLETED: Boolean - Whether a purchase was completed in this session
- DURATION_SECONDS: Integer - Duration of the interaction or time spent on the page (in seconds)

