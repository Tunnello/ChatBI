# 用户分析功能说明

本文档说明新增的两个用户分析功能及其数据库结构。

## 1. Purchase Behavior Analysis (购买行为分析)

### 功能描述
通过分析客户购买数据，识别：
- 热销产品 (Top-selling products)
- 购买频率 (Frequency of purchases)
- 客户忠诚度指标 (Customer loyalty indicators)

### 数据库扩展

#### CUSTOMER_DETAILS 表新增字段

在 `CUSTOMER_DETAILS` 表中添加了以下字段来支持购买行为分析：

- **REGISTRATION_DATE**: 客户注册日期
- **FIRST_PURCHASE_DATE**: 首次购买日期
- **LAST_PURCHASE_DATE**: 最后购买日期
- **TOTAL_PURCHASE_COUNT**: 总购买次数
- **TOTAL_PURCHASE_AMOUNT**: 总购买金额
- **LOYALTY_LEVEL**: 忠诚度等级 (Bronze, Silver, Gold, Platinum)
- **AVERAGE_ORDER_VALUE**: 平均订单价值

### 分析示例查询

#### 1. 识别高价值客户
```sql
SELECT CUSTOMER_ID, FIRST_NAME, LAST_NAME, 
       TOTAL_PURCHASE_AMOUNT, LOYALTY_LEVEL, 
       TOTAL_PURCHASE_COUNT, AVERAGE_ORDER_VALUE
FROM CUSTOMER_DETAILS
WHERE LOYALTY_LEVEL IN ('Gold', 'Platinum')
ORDER BY TOTAL_PURCHASE_AMOUNT DESC;
```

#### 2. 分析购买频率
```sql
SELECT 
    LOYALTY_LEVEL,
    AVG(TOTAL_PURCHASE_COUNT) as avg_purchase_count,
    AVG(AVERAGE_ORDER_VALUE) as avg_order_value
FROM CUSTOMER_DETAILS
GROUP BY LOYALTY_LEVEL;
```

#### 3. 识别热销产品（结合 TRANSACTIONS 表）
```sql
SELECT 
    p.PRODUCT_NAME,
    p.CATEGORY,
    SUM(t.QUANTITY) as total_quantity_sold,
    COUNT(DISTINCT t.ORDER_ID) as order_count,
    SUM(t.QUANTITY * t.PRICE) as total_revenue
FROM TRANSACTIONS t
JOIN PRODUCTS p ON t.PRODUCT_ID = p.PRODUCT_ID
GROUP BY p.PRODUCT_ID, p.PRODUCT_NAME, p.CATEGORY
ORDER BY total_quantity_sold DESC;
```

## 2. User Interaction Analysis (用户交互分析)

### 功能描述
通过分析用户与网站的交互行为（点击、搜索、加购物车等），帮助：
- 识别转化障碍 (Identify barriers to conversion)
- 发现用户体验优化机会 (Enhance user experience opportunities)

### 新表结构

#### USER_INTERACTIONS 表

创建了新表 `USER_INTERACTIONS` 来记录用户交互行为：

- **INTERACTION_ID**: 交互事件唯一标识
- **CUSTOMER_ID**: 客户ID（可为空，支持匿名用户）
- **SESSION_ID**: 会话ID
- **INTERACTION_TYPE**: 交互类型
  - `click`: 点击
  - `search`: 搜索
  - `view_product`: 查看产品
  - `add_to_cart`: 加入购物车
  - `remove_from_cart`: 从购物车移除
  - `checkout_start`: 开始结账
  - `checkout_complete`: 完成结账
  - `page_view`: 页面浏览
- **INTERACTION_DATE**: 交互时间戳
- **PRODUCT_ID**: 相关产品ID（可为空）
- **PAGE_URL**: 页面URL
- **SEARCH_QUERY**: 搜索查询文本（如果交互类型为搜索）
- **ADDED_TO_CART**: 是否加入购物车
- **PURCHASE_COMPLETED**: 是否完成购买
- **DURATION_SECONDS**: 交互持续时间（秒）

### 分析示例查询

#### 1. 分析转化漏斗
```sql
SELECT 
    INTERACTION_TYPE,
    COUNT(*) as interaction_count,
    COUNT(DISTINCT SESSION_ID) as unique_sessions
FROM USER_INTERACTIONS
WHERE INTERACTION_TYPE IN ('view_product', 'add_to_cart', 'checkout_start', 'checkout_complete')
GROUP BY INTERACTION_TYPE
ORDER BY 
    CASE INTERACTION_TYPE
        WHEN 'view_product' THEN 1
        WHEN 'add_to_cart' THEN 2
        WHEN 'checkout_start' THEN 3
        WHEN 'checkout_complete' THEN 4
    END;
```

#### 2. 识别高流失页面
```sql
SELECT 
    PAGE_URL,
    COUNT(*) as total_views,
    COUNT(CASE WHEN ADDED_TO_CART = 1 THEN 1 END) as cart_additions,
    COUNT(CASE WHEN PURCHASE_COMPLETED = 1 THEN 1 END) as purchases,
    ROUND(COUNT(CASE WHEN PURCHASE_COMPLETED = 1 THEN 1 END) * 100.0 / COUNT(*), 2) as conversion_rate
FROM USER_INTERACTIONS
WHERE INTERACTION_TYPE = 'page_view'
GROUP BY PAGE_URL
ORDER BY conversion_rate ASC;
```

#### 3. 分析搜索行为
```sql
SELECT 
    SEARCH_QUERY,
    COUNT(*) as search_count,
    COUNT(CASE WHEN ADDED_TO_CART = 1 THEN 1 END) as resulting_cart_additions,
    COUNT(CASE WHEN PURCHASE_COMPLETED = 1 THEN 1 END) as resulting_purchases
FROM USER_INTERACTIONS
WHERE INTERACTION_TYPE = 'search' AND SEARCH_QUERY IS NOT NULL
GROUP BY SEARCH_QUERY
ORDER BY search_count DESC
LIMIT 20;
```

#### 4. 分析产品浏览到购买的转化
```sql
SELECT 
    p.PRODUCT_NAME,
    p.CATEGORY,
    COUNT(DISTINCT CASE WHEN ui.INTERACTION_TYPE = 'view_product' THEN ui.SESSION_ID END) as views,
    COUNT(DISTINCT CASE WHEN ui.ADDED_TO_CART = 1 THEN ui.SESSION_ID END) as cart_additions,
    COUNT(DISTINCT CASE WHEN ui.PURCHASE_COMPLETED = 1 THEN ui.SESSION_ID END) as purchases,
    ROUND(COUNT(DISTINCT CASE WHEN ui.PURCHASE_COMPLETED = 1 THEN ui.SESSION_ID END) * 100.0 / 
          NULLIF(COUNT(DISTINCT CASE WHEN ui.INTERACTION_TYPE = 'view_product' THEN ui.SESSION_ID END), 0), 2) as conversion_rate
FROM USER_INTERACTIONS ui
JOIN PRODUCTS p ON ui.PRODUCT_ID = p.PRODUCT_ID
WHERE ui.PRODUCT_ID IS NOT NULL
GROUP BY p.PRODUCT_ID, p.PRODUCT_NAME, p.CATEGORY
HAVING views > 0
ORDER BY conversion_rate DESC;
```

#### 5. 分析用户会话行为
```sql
SELECT 
    SESSION_ID,
    COUNT(*) as total_interactions,
    COUNT(DISTINCT INTERACTION_TYPE) as unique_interaction_types,
    COUNT(CASE WHEN ADDED_TO_CART = 1 THEN 1 END) as cart_actions,
    MAX(CASE WHEN PURCHASE_COMPLETED = 1 THEN 1 ELSE 0 END) as completed_purchase,
    SUM(DURATION_SECONDS) as total_duration_seconds
FROM USER_INTERACTIONS
GROUP BY SESSION_ID
ORDER BY total_interactions DESC;
```

## 使用建议

1. **定期更新客户购买行为数据**：当有新订单时，更新 `CUSTOMER_DETAILS` 表中的购买行为字段
2. **实时记录用户交互**：在网站前端集成事件追踪，实时写入 `USER_INTERACTIONS` 表
3. **定期分析转化漏斗**：使用用户交互数据识别转化障碍点
4. **客户细分**：基于忠诚度等级和购买行为进行客户细分和个性化营销

## 数据生成

运行以下命令生成包含新字段的测试数据：

```bash
cd tools
python generate_sqlite_data.py
```

这将生成：
- 20 个客户（包含购买行为数据）
- 30 个订单
- 20 个产品
- 200 个用户交互事件

