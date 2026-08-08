# Generated Enterprise Data Dictionary

This document explains the columns and business rules used to generate the enterprise datasets based on the Olist Brazilian E-Commerce dataset.

## `calendar.csv`
Time dimension for business intelligence and reporting.
- **date**: Date (YYYY-MM-DD).
- **year**, **quarter**, **month**, **week**, **weekday**: Standard date parts.
- **weekend**: Boolean, true if Saturday or Sunday.
- **holiday_flag**: Boolean, randomized but models 5% holidays.
- **festival**: Name of festival (Black Friday, Christmas, Carnival) or None.
- **financial_quarter**: Mapped to standard quarters.

## `finance.csv`
Financial transactions linked to orders and payments.
- **transaction_id**: Primary key, prefixed with `FIN` (e.g., FIN000001).
- **order_id**: Foreign key to `orders.csv`.
- **customer_id**: Foreign key to `customers.csv`.
- **revenue**: Taken from `payment_value`.
- **expense**: Derived from revenue and randomized margin. Higher revenue items typically get better margins.
- **profit**: `revenue - expense`.
- **tax**: 10% of revenue.
- **shipping_cost**: 30% of expenses.
- **marketing_cost**: 20% of expenses.
- **operating_cost**: 50% of expenses.
- **cash_flow**: Profit +/- a random variance representing cash timing.
- **gross_margin**: `(revenue - (shipping + operating)) / revenue`.
- **net_margin**: `profit / revenue`.
- **dscr**: Debt-Service Coverage Ratio, random between 1.1 and 2.5.
- **debt_ratio**: Random between 0.2 and 0.6.
- **finance_date**: Taken from `order_purchase_timestamp`.

## `inventory.csv`
Inventory tracking for all products in `products.csv`.
- **inventory_id**: Primary key, prefixed with `INV` (e.g., INV000001).
- **product_id**: Foreign key to `products.csv`.
- **warehouse_id**: Fake warehouse ID (W01-W04).
- **warehouse_name**: Warehouse location.
- **current_stock**: Correlated inversely with product popularity.
- **minimum_stock**, **maximum_stock**, **reorder_level**: Based on calculated max stock (which scales with popularity).
- **lead_time_days**: Random between 2 and 14.
- **stockout_risk**: Derived metric: `1 - (current_stock / max_stock)`.
- **inventory_turnover**: Derived based on popularity (sales velocity).
- **last_restock_date**: Random date within the last 30 days.

## `employees.csv`
Human resources dataset.
- **employee_id**: Primary key, prefixed with `EMP` (e.g., EMP000001).
- **employee_name**: Fake generated name.
- **department**: Business department (Engineering, Marketing, etc.).
- **designation**: Role (Intern, Software Engineer, Senior Engineer, Manager, Director).
- **manager_id**: Foreign key back to `employee_id`.
- **joining_date**: Fake start date.
- **salary**: Generated using business rules based on designation bands.
- **bonus**: Derived as a percentage of salary depending on designation.
- **performance_score**: Score from 2.5 to 5.0.
- **experience_years**: Derived based on designation requirements.
- **email**, **phone**, **region**: Fake generated details.

## `marketing.csv`
Marketing campaigns by product category.
- **campaign_id**: Primary key, prefixed with `CMP` (e.g., CMP000001).
- **campaign_name**: Fake name.
- **channel**: Facebook, Google, Email, TikTok.
- **budget**: Random budget.
- **impressions**, **clicks**, **conversions**: Correlated down the funnel.
- **conversion_rate**: `conversions / clicks`.
- **roi**: Generated via business rules per channel (e.g., Google is 2.0-4.5).
- **campaign_start**, **campaign_end**: Fake dates.
- **product_category**: Randomly selected from valid Olist categories.

## `operations.csv`
Warehouse operations and supply chain metrics.
- **operation_id**: Primary key, prefixed with `OPS`.
- **warehouse_id**: Foreign key to `inventory.csv`.
- **processing_time**: Base time + penalty based on warehouse stockout risk.
- **downtime_minutes**: Base downtime + penalty based on stockout risk.
- **incident_count**: Correlated with stockout risk.
- **utilization**: Percentage of capacity used.
- **labor_hours**: Logged hours.
- **shipment_delay_days**: Correlated with stockout risk.
- **efficiency_score**: `1 - (downtime/1000) - (incidents/10)`.
- **operation_date**: Date of operation.

## `risk_metrics.csv`
Customer risk profiles.
- **risk_id**: Primary key, prefixed with `RSK`.
- **customer_id**: Foreign key to `customers.csv`.
- **financial_risk**: Random base score.
- **operational_risk**: Random base score.
- **customer_risk**: Correlated with fake customer satisfaction. Low satisfaction -> High churn prob -> High risk.
- **overall_risk**: Weighted average of all risk types.
- **risk_category**: Low, Medium, or High.
- **confidence_score**: Model confidence.

## `executive_kpis.csv`
Monthly rolled-up metrics for executive dashboards.
- **month**: YYYY-MM.
- **revenue**: Simulated monthly revenue.
- **profit**: Simulated monthly profit.
- **orders**, **customers**: Correlated inversely with simulated AOV.
- **growth_rate**: MoM growth.
- **average_order_value**, **customer_lifetime_value**, **customer_retention**, **inventory_turnover**, **operating_margin**, **net_margin**: Executive-level aggregations and averages.
