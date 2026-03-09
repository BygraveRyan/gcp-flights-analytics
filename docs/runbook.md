# Flights Analytics — Operations Runbook
>
> **Project:** `flights-analytics-prod` | **Region:** `europe-west2`
> This document captures infrastructure setup steps, troubleshooting decisions, and operational notes that live outside the codebase. Treat this as the source of truth for anything that happens in the terminal.

---

## Phase 2 — Cloud Functions Ingestion

### 2.1 Infrastructure Setup

#### VPC & Networking

A Serverless VPC Access connector was required to route Cloud Function egress through a static IP. This is needed because external APIs (FR24) may require IP allowlisting in future.

```bash
# Create VPC connector
gcloud compute networks vpc-access connectors create flights-vpc-connector \
  --region=europe-west2 \
  --subnet=default \
  --subnet-project=flights-analytics-prod \
  --min-instances=2 \
  --max-instances=3 \
  --machine-type=e2-micro

# Verify connector is READY before deploying functions
gcloud compute networks vpc-access connectors describe flights-vpc-connector \
  --region=europe-west2
```

**Expected output:** `state: READY`

#### Cloud NAT

Cloud NAT was configured to provide consistent egress IPs for all serverless traffic.

```bash
# Create Cloud Router
gcloud compute routers create flights-nat-router \
  --network=default \
  --region=europe-west2

# Create NAT gateway
gcloud compute routers nats create flights-nat-config \
  --router=flights-nat-router \
  --region=europe-west2 \
  --auto-allocate-nat-external-ips \
  --nat-all-subnet-ip-ranges
```

> ⚠️ **Known CLI/Console discrepancy:** The GCP Console shows NAT as covering `VM instances, GKE nodes, serverless` but the CLI `describe` output may not reflect serverless coverage explicitly. Trust the Console — the NAT was correctly configured. This caused confusion during setup and is a known GCP display inconsistency.

#### Secret Manager

FR24 API key stored in Secret Manager — never use environment variables for credentials.

```bash
# Store FR24 API key
echo -n "YOUR_FR24_API_KEY" | gcloud secrets create fr24-api-key \
  --data-file=- \
  --project=flights-analytics-prod

# Grant pipeline SA access
gcloud secrets add-iam-policy-binding fr24-api-key \
  --member="serviceAccount:flights-pipeline-sa@flights-analytics-prod.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=flights-analytics-prod

# Verify access
gcloud secrets versions access latest --secret=fr24-api-key \
  --project=flights-analytics-prod
```

> ⚠️ **Production key pending:** As of Phase 2 completion, the sandbox key is stored. Update this secret when the FR24 Explorer plan ($9/month) is purchased. The sandbox key returns static predefined data with the same schema as production.

#### Cloud Functions Deployment

```bash
# Deploy BTS ingestion function
gcloud functions deploy fn-ingest-bts-csv \
  --gen2 \
  --runtime=python312 \
  --region=europe-west2 \
  --source=cloud_functions/ingest_bts_csv \
  --entry-point=ingest_bts_csv \
  --trigger-http \
  --no-allow-unauthenticated \
  --service-account=flights-pipeline-sa@flights-analytics-prod.iam.gserviceaccount.com \
  --timeout=540s \
  --memory=512Mi \
  --project=flights-analytics-prod

# Deploy FR24 ingestion function
gcloud functions deploy fn-ingest-fr24 \
  --gen2 \
  --runtime=python312 \
  --region=europe-west2 \
  --source=cloud_functions/ingest_fr24 \
  --entry-point=ingest_fr24 \
  --trigger-http \
  --no-allow-unauthenticated \
  --vpc-connector=flights-vpc-connector \
  --egress-settings=all-traffic \
  --service-account=flights-pipeline-sa@flights-analytics-prod.iam.gserviceaccount.com \
  --timeout=120s \
  --memory=256Mi \
  --project=flights-analytics-prod
```

---

### 2.2 Troubleshooting Log

#### Issue: OpenSky Network blocks GCP IP ranges

**Date:** March 2026  
**Symptoms:** `fn-ingest-opensky` consistently timed out at TCP level. No HTTP response — connection never established.

**Diagnosis steps:**

1. Deployed a temporary `test-egress` function hitting `httpbin.org/ip`
2. Confirmed GCP egress was working — returned IP `34.13.52.23`
3. Confirmed the IP `34.13.52.23` was a GCP IP range
4. Tested OpenSky directly — same timeout regardless of NAT/VPC config
5. Confirmed OpenSky actively blocks GCP IP ranges at network level

**Resolution:** Migrated to FlightRadar24 API v1. OpenSky is not viable from any GCP serverless compute.

**Lesson:** Always verify external API IP restrictions before building ingestion logic. Check the API provider's documentation for cloud provider restrictions.

---

#### Issue: NAT configuration confusion — CLI vs Console discrepancy

**Date:** March 2026  
**Symptoms:** `gcloud compute routers nats describe` output did not explicitly show serverless coverage, causing uncertainty about whether NAT was correctly configured.

**Resolution:** GCP Console showed correct configuration (`VM instances, GKE nodes, serverless`). The CLI display is incomplete for serverless NAT coverage — this is a known GCP issue. Trust the Console for NAT serverless status.

---

#### Issue: AI tooling (Gemini) diagnosing code when root cause was networking

**Date:** March 2026  
**Symptoms:** Gemini kept suggesting code fixes (timeout values, request headers, auth logic) when the real problem was OpenSky blocking GCP IPs at network level.

**Lesson:** AI tools are blind to infrastructure state. When a function fails with connection timeouts, rule out networking first before debugging code. Use a minimal egress test function to isolate the problem layer.

---

### 2.3 Data Source Reference

#### FR24 API v1

| Property | Value |
|---|---|
| Endpoint | `https://fr24api.flightradar24.com/api/live/flight-positions/full` |
| Auth | Bearer token via Secret Manager (`fr24-api-key`) |
| Header | `Accept-Version: v1` |
| Bounding box | `61.5,49.0,-8.5,10.5` (north, south, west, east) |
| Coverage | UK + NW Europe |
| Plan | Explorer ($9/month, 30k credits) — **sandbox key in use until purchased** |
| Response format | `{"data": [...]}` — native FR24 field names |

#### Bronze Zone Schema (Raw FR24 Fields)

Fields stored exactly as received from FR24 — no renaming, no unit conversion:

| FR24 Field | Type | Notes |
|---|---|---|
| `fr24_id` | string | FR24 internal flight ID |
| `hex` | string | ICAO24 hex address (maps to `icao24` in Silver) |
| `lat` | float | Latitude |
| `lon` | float | Longitude |
| `alt` | int | Altitude in **feet** (converted to metres in Silver) |
| `gspeed` | int | Ground speed in **knots** (converted to m/s in Silver) |
| `vspeed` | int | Vertical speed |
| `callsign` | string | Flight callsign |
| `ingestion_timestamp` | string | Injected at ingestion — ISO format UTC |

> **Unit conversion note (Silver job):** `alt_metres = alt_feet × 0.3048` | `velocity_ms = gspeed_knots × 0.514444`

#### GCS Bronze Path

```
gs://flights-bronze-flights-analytics-prod/fr24/{year}/{month:02d}/{day:02d}/positions_{YYYYMMDD_HHMMSS}.ndjson
```

---

### 2.4 Cleanup After Phase 2

```bash
# Delete temporary diagnostic functions (already done)
gcloud functions delete test-egress --region=europe-west2 --project=flights-analytics-prod
gcloud functions delete test-fr24 --region=europe-west2 --project=flights-analytics-prod

# TODO: Delete OpenSky secrets after FR24 production key confirmed working
gcloud secrets delete opensky-client-id --project=flights-analytics-prod
gcloud secrets delete opensky-client-secret --project=flights-analytics-prod
```

---

## Active Infrastructure State (End of Phase 2)

| Resource | Name | Status |
|---|---|---|
| Cloud Function | `fn-ingest-bts-csv` | ✅ Active |
| Cloud Function | `fn-ingest-fr24` | ✅ Active (sandbox key) |
| VPC Connector | `flights-vpc-connector` | ✅ Active |
| Cloud NAT | `flights-nat-config` | ✅ Active |
| Secret | `fr24-api-key` | ✅ Sandbox key stored |
| Secret | `opensky-client-id` | ⚠️ Pending deletion |
| Secret | `opensky-client-secret` | ⚠️ Pending deletion |

---

*Phases 3–11 infrastructure notes will be added as each phase is completed.*
---

## Phase 3 — PySpark Bronze→Silver + Dataplex DQ

### 3.1 Troubleshooting Log

#### Issue: Dataplex Data Quality YAML syntax mismatch

**Date:** March 2026
**Symptoms:** `gcloud dataplex datascans create data-quality` command failed with a Protobuf parsing error: `Failed to parse value(s) in protobuf [GoogleCloudDataplexV1DataQualitySpec]: ... customSqlExpectation`

**Diagnosis steps:**

1.  The initial `silver_flights_dq.yaml` was created based on the `architecture.md` documentation, which used `rule_type: CUSTOM_SQL_EXPR` and a `sql_expression` that was a boolean statement.
2.  The `gcloud` error indicated a problem with `customSqlExpectation`, suggesting the format was incorrect.
3.  The user provided a corrected snippet using `rowConditionExpectation` and a row-level boolean `sqlExpression`. This implies that for row-level custom checks, `rowConditionExpectation` is the correct directive.

**Resolution:**

The `dataplex/dq_rules/silver_flights_dq.yaml` file was updated to use `rowConditionExpectation` for custom SQL checks. The `sqlExpression` was changed to a boolean expression that evaluates per row. The `architecture.md` file was also updated to reflect the correct syntax.

**Lesson:**

The `gcloud` CLI for Dataplex Data Quality scans has a specific YAML structure that may not be perfectly reflected in older documentation. The error message from `gcloud` can be misleading. When a Protobuf parsing error occurs, it's a strong indicator of a syntax mismatch between the YAML file and the API's expectations. The best course of action is to consult the latest official documentation or experiment with the format (`tableCondition` vs `rowCondition`) to find the working syntax. In this case, the fix was to use a row-level condition (`rowConditionExpectation`) instead of a table-level aggregate condition.

---

#### Issue: Dataplex Auto DQ requires BigQuery table, not GCS

**Date:** March 2026
**Symptoms:** `gcloud dataplex datascans create data-quality` failed when `--data-source-resource` pointed to a GCS bucket URI.

**Diagnosis:** Dataplex Auto Data Quality scans for "curated" zones or external data only support BigQuery tables (including external tables) as the data source resource. It cannot scan raw GCS buckets directly.

**Resolution:**
1. Created the `ext_silver_bts` BigQuery external table pointing to the Silver GCS bucket.
2. Updated the DQ scan to target the BQ table resource.

```bash
# 1. Create external table (pulled forward from Phase 5)
bq query --use_legacy_sql=false "
CREATE EXTERNAL TABLE IF NOT EXISTS \`flights-analytics-prod.flights_raw.ext_silver_bts\`
WITH PARTITION COLUMNS (flight_date DATE)
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://flights-silver-flights-analytics-prod/bts/*.parquet'],
  hive_partition_uri_prefix = 'gs://flights-silver-flights-analytics-prod/bts'
);"

# 2. Create DQ scan targeting the BQ table
gcloud dataplex datascans create data-quality silver-flights-dq \
  --location=europe-west2 \
  --data-source-resource=\"//bigquery.googleapis.com/projects/flights-analytics-prod/datasets/flights_raw/tables/ext_silver_bts\" \
  --data-quality-spec-file=dataplex/dq_rules/silver_flights_dq.yaml \
  --display-name=\"Silver BTS Flights DQ Scan\" \
  --project=flights-analytics-prod
```

**Lesson:** Dataplex DQ is tightly coupled with the BigQuery storage engine for execution. Always wrap GCS data in an external table if you need to run DQ scans against it. Note that `ext_silver_bts` is now already created for Phase 5; do not recreate it.

---

#### Issue: Dataplex DQ scan creation fails on empty external table

**Date:** March 2026
**Symptoms:** `gcloud dataplex datascans create data-quality` failed with an error indicating it "matched no files" when targeting the BigQuery external table `flights_raw.ext_silver_bts`.

**Diagnosis steps:**
1. Dataplex performs an eager validation query against the target BigQuery external table at scan creation time to verify the schema and connectivity.
2. The `ext_silver_bts` table points to `gs://flights-silver-flights-analytics-prod/bts/*.parquet`.
3. Since the Silver GCS bucket was empty (no Spark jobs had run yet), the external table could not resolve any files, causing the validation query to fail and blocking the scan creation.

**Resolution:**
Uploaded a zero-row "seed" Parquet file containing the correct BTS Silver schema to the Silver bucket. This satisfies Dataplex's eager validation without affecting query results or DQ statistics.

```bash
# Upload zero-row seed file to satisfy Dataplex validation
# (File: gs://flights-silver-flights-analytics-prod/bts/seed.parquet)

# Create the DQ scan (now succeeds as validation query finds the seed file)
gcloud dataplex datascans create data-quality silver-flights-dq \
  --location=europe-west2 \
  --data-source-resource="//bigquery.googleapis.com/projects/flights-analytics-prod/datasets/flights_raw/tables/ext_silver_bts" \
  --data-quality-spec-file=dataplex/dq_rules/silver_flights_dq.yaml \
  --display-name="Silver BTS Flights DQ Scan" \
  --project=flights-analytics-prod
```

**Lesson:** Dataplex DQ scans require the target data source to be queryable at the moment of creation. For BigQuery external tables pointing to GCS, at least one file matching the schema must exist in the URI path. A zero-row seed Parquet file is a robust way to enable "infrastructure-first" deployments before the first ingestion/transformation job runs.

---
