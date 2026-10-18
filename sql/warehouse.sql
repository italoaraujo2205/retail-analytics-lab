-- Grain: one row per item. Money is stored in integer cents.
CREATE TABLE dim_customer AS SELECT customer_id, region FROM stg_customers;
CREATE UNIQUE INDEX pk_customer ON dim_customer(customer_id);
CREATE TABLE dim_product AS SELECT product_id, category FROM stg_products;
CREATE UNIQUE INDEX pk_product ON dim_product(product_id);

CREATE TABLE fct_order_item AS
SELECT i.item_id, i.order_id, i.product_id, i.quantity,
       CASE WHEN o.status = 'delivered'
            THEN CAST(ROUND(i.quantity * i.unit_price * (1 - i.discount_rate) * 100) AS INTEGER)
            ELSE 0 END AS net_revenue_cents,
       CASE WHEN o.status = 'delivered'
            THEN CAST(ROUND(i.quantity * i.unit_cost * 100) AS INTEGER)
            ELSE 0 END AS cogs_cents
FROM stg_order_items i JOIN stg_orders o ON i.order_id = o.order_id;
CREATE UNIQUE INDEX pk_order_item ON fct_order_item(item_id);
CREATE INDEX ix_item_order ON fct_order_item(order_id);

-- Aggregate items BEFORE joining fulfillment cost: avoids order/item fan-out.
CREATE TABLE fct_order AS
WITH item_totals AS (
    SELECT order_id, SUM(net_revenue_cents) AS revenue, SUM(cogs_cents) AS cogs
    FROM fct_order_item GROUP BY order_id
)
SELECT o.order_id, o.customer_id, o.order_date, o.status,
       t.revenue AS net_revenue_cents, t.cogs AS cogs_cents,
       CAST(ROUND(o.fulfillment_cost * 100) AS INTEGER) AS fulfillment_cents,
       t.revenue - t.cogs - CAST(ROUND(o.fulfillment_cost * 100) AS INTEGER) AS contribution_cents
FROM stg_orders o JOIN item_totals t ON o.order_id = t.order_id;
CREATE UNIQUE INDEX pk_order ON fct_order(order_id);
CREATE INDEX ix_order_customer_date ON fct_order(customer_id, order_date);

CREATE VIEW mart_monthly AS
SELECT substr(order_date, 1, 7) AS month,
       SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) AS delivered_orders,
       COUNT(DISTINCT CASE WHEN status = 'delivered' THEN customer_id END) AS active_customers,
       ROUND(SUM(net_revenue_cents) / 100.0, 2) AS net_revenue,
       ROUND(SUM(contribution_cents) / 100.0, 2) AS contribution,
       ROUND(SUM(net_revenue_cents) / 100.0 / NULLIF(SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END), 0), 2) AS average_ticket,
       1.0 * SUM(contribution_cents) / NULLIF(SUM(net_revenue_cents), 0) AS contribution_margin
FROM fct_order GROUP BY substr(order_date, 1, 7);

-- Gross margin excludes fulfillment, unlike order-level contribution margin.
CREATE VIEW mart_category AS
SELECT p.category,
       ROUND(SUM(i.net_revenue_cents) / 100.0, 2) AS net_revenue,
       ROUND(SUM(i.net_revenue_cents - i.cogs_cents) / 100.0, 2) AS gross_profit,
       1.0 * SUM(i.net_revenue_cents - i.cogs_cents) / NULLIF(SUM(i.net_revenue_cents), 0) AS gross_margin
FROM fct_order_item i JOIN dim_product p ON i.product_id = p.product_id
GROUP BY p.category;
