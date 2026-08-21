# Public API — Customer Webhooks

`api` is the public REST API of a SaaS platform. Authenticated clients manage their customer records and now want push notifications when a customer's data changes. Two dependencies are in play: `api.db` wraps the API's PostgreSQL tables, and `api.secrets` mints webhook signing secrets.

`api/customers.py` serves customer records. `api/webhooks.py` registers webhooks that receive a customer's events. Existing API routes sit behind an ownership middleware that checks the caller may act on the customer id it passes.

## The PR

Title: "webhooks for customer changes". The PR adds webhook registration and renames one customer field for brevity. The new webhook route is registered on the framework directly, outside the ownership middleware. It claims the changes are backward compatible.
