# 数据库查询示例和常见问题

## 常见查询场景

### 客户分析查询
- 查询所有客户的总购买金额
- 按忠诚度等级统计客户数量
- 查找最近30天注册的新客户
- 查询平均订单价值最高的客户

### 订单分析查询
- 统计每个月的订单总数和总金额
- 查询订单状态分布（已完成、待处理、已取消）
- 查找订单金额超过1000的大额订单
- 分析订单趋势，按时间线展示

### 产品分析查询
- 统计每个产品类别的产品数量
- 查询价格最高的10个产品
- 按类别统计产品平均价格
- 查找最受欢迎的产品类别

### 支付分析查询
- 统计不同支付方式的订单数量
- 查询支付状态分布
- 分析支付金额趋势
- 查找支付失败的订单

### 交易分析查询
- 统计每日交易总额
- 查询交易类型分布
- 分析交易趋势
- 查找异常交易记录

## SQL 查询示例

### 示例1：统计产品类别数量
```sql
SELECT CATEGORY, COUNT(*) as product_count 
FROM PRODUCTS 
GROUP BY CATEGORY
```

### 示例2：查询客户购买统计
```sql
SELECT 
    CUSTOMER_ID,
    FIRST_NAME,
    LAST_NAME,
    TOTAL_PURCHASE_COUNT,
    TOTAL_PURCHASE_AMOUNT,
    LOYALTY_LEVEL
FROM CUSTOMER_DETAILS
ORDER BY TOTAL_PURCHASE_AMOUNT DESC
LIMIT 10
```

### 示例3：订单时间趋势分析
```sql
SELECT 
    DATE(ORDER_DATE) as order_day,
    COUNT(*) as order_count,
    SUM(ORDER_AMOUNT) as total_amount
FROM ORDER_DETAILS
GROUP BY DATE(ORDER_DATE)
ORDER BY order_day DESC
```

## 数据可视化建议

### 柱状图
- 产品类别数量分布
- 客户忠诚度等级分布
- 订单状态分布

### 折线图
- 订单金额趋势
- 交易量趋势
- 客户注册趋势

### 饼图
- 支付方式占比
- 产品类别占比
- 订单状态占比

### 面积堆积图
- 按时间线的订单金额堆积
- 按类别的销售趋势

## 常见问题解答

**Q: 如何查询最近一个月的订单？**
A: 使用 DATE 函数和日期比较，例如：`WHERE ORDER_DATE >= DATE('now', '-1 month')`

**Q: 如何计算客户的平均订单价值？**
A: 使用 AVERAGE_ORDER_VALUE 字段，或通过 TOTAL_PURCHASE_AMOUNT / TOTAL_PURCHASE_COUNT 计算

**Q: 如何按时间分组统计？**
A: 使用 DATE() 函数提取日期部分，然后 GROUP BY DATE(字段名)

**Q: 如何查找重复数据？**
A: 使用 GROUP BY 和 HAVING COUNT(*) > 1

