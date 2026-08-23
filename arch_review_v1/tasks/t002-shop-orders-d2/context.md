# Shop API — Order History

`shop` is the order-management backend of a small e-commerce store. A customer places an order; the API records it and exposes a history page. Two dependencies are in play: `shop.db` wraps the PostgreSQL connection with `fetchone`/`fetchall` helpers, and `shop.catalog` resolves product titles for the storefront.

`shop/orders.py` builds the order history view: it reads a customer's orders and fills in the customer name and item titles. `shop/catalog.py` is a small helper that looks up a product's title. Product titles are immutable: a rename creates a new product id, and a product exists before any order references it.

## The PR

Title: "cache product lookups to speed up the orders page". The PR replaces the join that resolved customer names with a per-order lookup, catches failures in that lookup so the page renders anyway, and adds an in-process cache for product titles. It claims the changes cut database load without changing what the page shows.
