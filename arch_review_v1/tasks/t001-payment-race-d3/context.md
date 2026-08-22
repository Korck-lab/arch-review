# Payment Service — Checkout

`billing` is the checkout subsystem of a payments platform. A customer places an order; the system charges the card on file and debits the internal balance ledger. Two dependencies are in play: `billing.accounts` owns the balance ledger, and `billing.gateway` fronts the card network provider. A gateway call can fail transiently with `GatewayError`.

The gateway signature is `charge_card(card_token, amount_cents, idempotency_key=None)`. The provider deduplicates two calls that carry the same idempotency key: the second returns the first charge instead of billing again.

`billing/charge.py` orchestrates a checkout: validate the amount, charge the card, record the debit. `billing/retry.py` is a small helper that wraps gateway calls so transient provider errors are retried a bounded number of times.

## The PR

Title: "improve checkout performance". The PR adds a balance pre-check before charging so checkout fails fast on insufficient funds, wraps the card charge in the retry helper, and removes a logging call from the hot path. It claims the changes reduce checkout latency without changing behavior.
