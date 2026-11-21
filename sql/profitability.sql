WITH return_totals AS (
    SELECT
        order_id,
        SUM(returned_quantity) AS returned_quantity,
        SUM(refund_amount) AS refund_amount,
        SUM(return_shipping_cost) AS return_shipping_cost,
        SUM(recovered_inventory_cost) AS recovered_inventory_cost
    FROM returns
    GROUP BY order_id
),

order_economics AS (
    SELECT
        o.*,
        p.product_name,
        p.category,
        s.seller_name,

        COALESCE(r.returned_quantity, 0) AS returned_quantity,
        COALESCE(r.refund_amount, 0) AS refund_amount,
        COALESCE(r.return_shipping_cost, 0) AS return_shipping_cost,
        COALESCE(r.recovered_inventory_cost, 0)
            AS recovered_inventory_cost,

        o.paid_amount - COALESCE(r.refund_amount, 0)
            AS net_revenue,

        o.quantity * o.unit_cost
            - COALESCE(r.recovered_inventory_cost, 0)
            AS net_product_cost,

        ROUND(
            (
                o.paid_amount
                - COALESCE(r.refund_amount, 0)
            ) * o.fee_rate,
            2
        ) AS marketplace_fee

    FROM orders AS o

    JOIN products AS p
        ON o.product_id = p.product_id

    JOIN sellers AS s
        ON o.seller_id = s.seller_id

    LEFT JOIN return_totals AS r
        ON o.order_id = r.order_id
)

SELECT
    *,
    net_revenue
        - net_product_cost
        - marketplace_fee
        - shipping_cost
        - return_shipping_cost AS contribution_profit

FROM order_economics
ORDER BY order_date, order_id;