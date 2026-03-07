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
