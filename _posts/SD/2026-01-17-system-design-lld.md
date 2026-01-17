---
layout: post
title: System Design (LLD)
author: sal
date: 2026-01-17-19:05:39
categories: [ system design, tutorial ]
image: assets/images/4.jpg
---

This Low-Level Design (LLD) synthesizes the architectural patterns of Netflix’s RENO (Rapid Event Notification), Meta’s PTP (Precision Time Protocol) implementation, and Netflix’s Distributed Counter and Traffic Migration frameworks. 

The resulting system, referred to as **System Design**, is a high-precision, event-driven state synchronization and notification platform designed to provide linearizable updates across 200M+ global devices with nanosecond timing accuracy.

---

# Low-Level Design: System Design

## 1. Data Model

The system utilizes a multi-tiered storage strategy to balance high-throughput event logging with low-latency state retrieval.

### 1.1. High-Precision Event Store (Cassandra)
Events are persisted using an **Event Sourcing** pattern to allow for state reconstruction and auditing.
*   **Table: `event_log`**
    *   `entity_id` (UUID, Partition Key): The member or device ID.
    *   `event_time_ns` (BigInt, Clustering Key): TAI timestamp from PTP with nanosecond precision.
    *   `event_type` (Enum): e.g., `VIEW_ACTIVITY`, `PLAN_CHANGE`.
    *   `payload` (Blob): Protobuf-encoded event data.
    *   `idempotency_token` (String): Combination of `client_request_id` and `event_bucket`.
    *   **Rationale:** Wide-column layout allows for efficient range scans by time. Partitioning by `entity_id` ensures all updates for a single user are co-located.

### 1.2. Distributed Counter Store (Hybrid EVCache/Cassandra)
Used for tracking cross-device limits (e.g., download limits, concurrent streams).
*   **Hot Path (EVCache):** `namespace:counter_name` -> `AtomicInteger`. Best-effort regional counts.
*   **Durable Path (Cassandra):**
    *   `namespace` (Partition Key)
    *   `counter_id` (Clustering Key)
    *   `last_rollup_count` (BigInt)
    *   `last_rollup_ts` (BigInt)
    *   `last_write_ts` (BigInt): Used for LWW (Last-Write-Wins) resolution during background rollups.

### 1.3. Device Registry & Connectivity State (In-Memory/Redis)
*   **Key:** `member_id`
*   **Fields:**
    *   `device_list`: List of `device_id`, `platform_type` (iOS, Android, TV).
    *   `connection_status`: Online/Offline (Heartbeat-based, updated via Zuul Push).
    *   `wou_ns` (Window of Uncertainty): Current clock skew estimate for the device.

---

## 2. API / Interface Design

### 2.1. Internal Precision Clock Interface (fbclock)
Exposes the Meta-inspired **Window of Uncertainty (WOU)** to internal services.
*   **`get_time_window()`**
    *   **Returns:** `{"earliest_ns": long, "latest_ns": long, "wou_ns": int}`
    *   **Logic:** Returns a range rather than a point. Consumers must block until `read_timestamp + WOU` to ensure linearizability.

### 2.2. Rapid Event Ingestion API
*   **`POST /v1/events/notify`**
    *   **Request:** `{"entity_id": UUID, "priority": int, "idempotency_token": string, "event_data": Protobuf}`
    *   **Response:** `202 Accepted` (includes `correlation_id`).
    *   **Logic:** Routes to priority-sharded SQS queues. High-priority (maturity level changes) triggers aggressive scale-up; low-priority (diagnostic signals) is processed best-effort.

### 2.3. Distributed Counter API
*   **`add_and_get_count(namespace, counter_id, delta, token)`**
    *   **Guarantees:** Eventually consistent global count with idempotent retries.
    *   **Rollup:** Background process aggregates `event_log` into `last_rollup_count` using a sliding window to ignore events within the current `accept_limit` (to handle clock skew).

---

## 3. Critical Execution Flows

### 3.1. Event Processing & Targeted Push (Hot Path)
1.  **Ingestion:** Manhattan framework receives the event and assigns a PTP-synchronized hardware timestamp.
2.  **Prioritization:** The event is routed to an **Amazon SQS** queue based on its priority shard.
3.  **Deduplication:** The processing cluster checks the `idempotency_token` against a 24-hour Bloom filter.
4.  **Targeted Delivery:** 
    *   System queries the **Device Registry** for the `member_id`.
    *   Filters for online devices via **Zuul Push** registry.
    *   Parallelizes outbound calls to **APNS (Apple)**, **FCM (Google)**, and **Zuul Push (Web/TV)** using a **Bulkhead Pattern** to prevent downstream failure propagation.

### 3.2. Traffic Migration (Shadow Replay)
To migrate a critical service (e.g., changing the Licensing Engine):
1.  **Traffic Forking:** A dedicated service captures production requests asynchronously via **Mantis**.
2.  **Normalization:** Timestamps and non-deterministic fields in the replay payload are scrubbed or aligned.
3.  **Comparison:** Replayed responses are compared against production responses in **Apache Iceberg**.
4.  **Lineage Tracking:** Checksums of all dependencies (metadata, studio rules) are attached to the diff to filter "noisy" mismatches caused by upstream data changes.

### 3.3. Failure Handling
*   **Stale Events:** A gating filter checks `event_age`. If `now() - event_time > threshold`, the event is dropped to prevent flooding the system with old updates after a recovery.
*   **Thundering Herd:** Aggressive cluster scale-up policies (cooldown-less) trigger when SQS queue depth exceeds 10k messages.

---

## 4. Monitoring & Observability

### 4.1. Precision Timing Metrics (PTP-Specific)
*   **`phc_offset_ns`:** Difference between the Time Card and the Network Interface Card (NIC). Alert if > 50ns.
*   **`linearizability_failure_count`:** Incremented if a quorum check reveals a follower node’s clock has drifted outside the WOU.
*   **`WOU_size_ns`:** Tracks the probability (99.9999%) that the true time is within the returned window.

### 4.2. Operational Health (RED Metrics)
*   **Rate:** 150k RPS peak.
*   **Errors:** Sharded by platform (iOS, Android, TV) to isolate vendor-specific push notification failures (e.g., APNS certificate expiry).
*   **Duration:** End-to-end latency from server trigger to device receipt (P99 < 500ms).

### 4.3. Real-Time Stream Processing
*   **Mantis Integration:** Allows developers to "tap" into the live event stream at a specific `device_id` granularity for real-time troubleshooting without adding log overhead to the entire fleet.
*   **Auditability:** Every state change in the `event_log` is mapped to a `command_id` to trace the specific user action (e.g., "Why was this license revoked?").