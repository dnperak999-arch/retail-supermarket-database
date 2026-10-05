-- report: order_contents
-- Lines sold: customer, order, product, and quantity.

SELECT
    Customer.full_name,
    CustomerOrder.order_id,
    Product.product_name,
    OrderItem.quantity
FROM CustomerOrder
JOIN Customer ON CustomerOrder.customer_id = Customer.customer_id
JOIN OrderItem ON CustomerOrder.order_id = OrderItem.order_id
JOIN Product ON OrderItem.product_id = Product.product_id;

-- report: low_stock
-- Products whose quantity in stock is below the reorder level.

SELECT
    Product.product_name,
    Inventory.quantity_in_stock,
    Inventory.reorder_level
FROM Product
JOIN Inventory ON Product.product_id = Inventory.product_id
WHERE Inventory.quantity_in_stock < Inventory.reorder_level;

-- report: payment_status
-- Payment method, status, and amount for each order.

SELECT
    CustomerOrder.order_id,
    Payment.payment_method,
    Payment.payment_status,
    Payment.amount
FROM CustomerOrder
JOIN Payment ON CustomerOrder.order_id = Payment.order_id;
