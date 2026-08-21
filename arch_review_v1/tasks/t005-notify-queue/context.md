# Notify Service — Transactional Email

`notify` is the transactional-message service of a payments platform. Workers pull batches of emails from an outbound queue and hand each to the email provider. Two dependencies are in play: `notify.provider` fronts the email provider, raising `TransientError` for retryable failures, and `notify.db` wraps the queue's PostgreSQL tables.

`notify/sender.py` sends one email through the provider. `notify/queue.py` claims a batch of emails for a worker. The `outbound` table is indexed only on `id` and `claimed_by`; there is no index on `kind`.

## The PR

Title: "more robust delivery". The PR adds a retry loop around provider sends and lets workers claim emails by kind so different kinds are not starved. It claims the changes make delivery more reliable without sending anything twice.
