# Warehouse Service — Inventory Sync

`warehouse` is the inventory backend of a small fulfillment company. The web app exposes health and admin endpoints; a background job keeps local inventory deltas in sync with the hub. Two dependencies are in play: `warehouse.store` owns the database connection, and `warehouse.app` is the Flask app that owns process setup.

The hub accepts a delta by id and is idempotent: pushing the same delta twice applies it once. It parses the request body directly as JSON and does not validate the Content-Type header, so a push succeeds regardless of the header urllib sends.

`warehouse/app.py` creates the Flask app and opens the store connection. `warehouse/sync.py` is the sync job that pushes pending deltas to the hub.

## The PR

Title: "decouple the sync job from the web app". The PR adds a `/sync` admin endpoint that triggers the job and pins the sync interval. It claims the change lets operators trigger a sync on demand without changing behavior.
