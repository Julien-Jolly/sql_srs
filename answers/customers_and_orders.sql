SELECT * FROM orders_data
INNER JOIN order_details_data
USING (order_id)