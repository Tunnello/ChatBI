# 数据库概览

## 数据库结构

本数据库包含以下主要表：

1. **CUSTOMER_DETAILS** - 客户详细信息表
2. **ORDER_DETAILS** - 订单详情表
3. **PRODUCTS** - 产品信息表
4. **PAYMENTS** - 支付记录表
5. **TRANSACTIONS** - 交易流水表
6. **USER_INTERACTIONS** - 用户交互记录表

## 表关系说明

- CUSTOMER_DETAILS 和 ORDER_DETAILS 通过 CUSTOMER_ID 关联
- ORDER_DETAILS 和 PRODUCTS 通过 PRODUCT_ID 关联
- ORDER_DETAILS 和 PAYMENTS 通过 ORDER_ID 关联
- TRANSACTIONS 记录所有交易流水
- USER_INTERACTIONS 记录用户行为数据

## 主要业务场景

### 客户管理
- 客户注册和基本信息管理
- 客户购买历史和忠诚度分析
- 客户价值分析

### 订单管理
- 订单创建和状态跟踪
- 订单金额统计
- 订单趋势分析

### 产品管理
- 产品分类和价格管理
- 产品库存跟踪
- 产品销售分析

### 支付管理
- 支付方式记录
- 支付状态跟踪
- 支付金额统计

### 数据分析
- 销售趋势分析
- 客户行为分析
- 产品表现分析
- 收入统计

## 常用查询模式

### 聚合查询
- COUNT() - 统计数量
- SUM() - 求和
- AVG() - 平均值
- MAX() / MIN() - 最大/最小值

### 分组查询
- GROUP BY - 按字段分组
- HAVING - 分组后过滤

### 时间查询
- DATE() - 提取日期
- DATE('now', '-1 month') - 相对日期
- strftime() - 日期格式化

### 连接查询
- INNER JOIN - 内连接
- LEFT JOIN - 左连接
- 多表关联查询

## 数据完整性

- 所有表都有主键约束
- 外键关系确保数据一致性
- 日期字段使用标准日期格式
- 金额字段使用 DECIMAL 类型保证精度

