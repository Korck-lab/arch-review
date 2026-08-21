# Reports Service — CSV Export

`reports` is the data-export subsystem of a business-intelligence platform. Analysts generate reports; the export endpoint lets a user download a generated report as CSV. Two dependencies are in play: `reports.storage` reads generated report files from a blob storage service, and `reports.config` holds the service's settings.

`reports/export.py` writes a downloaded report into a per-user export folder served back to the caller. `reports/storage.py` fetches the report lines from the blob service.

## The PR

Title: "self-service CSV export". The PR adds the export endpoint that writes a report into the user's export folder and makes the storage read more tolerant of transient network errors by retrying. It claims the changes let users download their own reports reliably.
