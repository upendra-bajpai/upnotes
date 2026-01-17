---
layout: post
title: Designing a Rate Limiter at Scale (LLD)
author: sal
date: 2026-01-16-18:34:36
categories: [ system design, tutorial ]
image: assets/images/4.jpg
---

This Low-Level Design (LLD) synthesizes high-scale architectural patterns from Netflix’s **RAW Hollow** (in-memory state), Uber’s **Zanzibar/API Gateway** (middleware orchestration), and Netflix’s **Service-Level Prioritized Load Shedding**.

# Low-Level Design: Designing a Rate Limiter at Scale

## 1. Data Schema & Persistence
To achieve the O(1) read performance described in the Netflix Tudum architecture, we utilize a tiered storage approach: **RAW Hollow** for static configuration (rules) and **Redis** for dynamic state (counters).

### 1.1. Static Configuration (Rules) — RAW Hollow Schema
Configuration is distributed as a compressed, in-memory dataset to every Rate Limiter node. This avoids I/O for fetching "how many requests are allowed for User X."
```json
// Entity: RateLimitRule (Compressed via RAW Hollow)
{
  "rule_id": "uuid",
  "resource_path": "/api/v1/playback",
  "priority_bucket": "CRITICAL", // Values: CRITICAL, DEGRADED, BEST_EFFORT, BULK
  "limit": 5000,
  "window_seconds": 60,
  "burst_capacity": 1.2, // 20% burst over limit
  "client_type": "ANDROID_MOBILE" 
}
```

### 1.2. Dynamic State (Counters) — Redis Hash Structure
Dynamic counters use a **Sliding Window Counter** to avoid "stampeding herds" at the edge of fixed windows.
*   **Key:** `rate_limit:{user_id}:{rule_id}:{current_minute_timestamp}`
*   **Structure:** Redis Hash or Atomic Counter.
*   **TTL:** `window_seconds * 2` (to allow for overlapping window calculations).

## 2. API Specifications
Leveraging Uber’s Gateway design, we define a high-performance internal RPC (gRPC) to handle 2,500+ QPS per node.

### 2.1. Internal Rate Limiter Check (gRPC)
**Request Payload:**
```protobuf
message RateLimitRequest {
  string user_id = 1;
  string resource_path = 2;
  map<string, string> headers = 3; // For X-Netflix.Request-Name
  uint32 weight = 4; // Cost of the request
  PriorityBucket priority = 5; // Determined by Protocol Manager
}
```
**Response Payload:**
```protobuf
message RateLimitResponse {
  bool allowed = 1;
  uint32 remaining_tokens = 2;
  int64 retry_after_ms = 3;
  string cluster_utilization_status = 4; // e.g., "DEGRADED_MODE"
}
```

## 3. Implementation Details & Algorithms

### 3.1. The Sliding Window Algorithm (Lua-based)
To ensure atomicity and prevent race conditions (Concurrency Management), the logic is encapsulated in a Redis Lua script. This prevents the "check-then-set" race condition common in distributed systems.

**Logic Flow:**
1.  Calculate current window and previous window counts.
2.  `Weight = current_count + (previous_count * (remainder_of_window / window_size))`.
3.  If `Weight + request_weight <= limit`, increment and return `allowed=true`.

### 3.2. Service-Level Prioritized Load Shedding
Following Netflix's "Option 3" approach, the Rate Limiter doesn't just return a binary allow/deny. It monitors **System Utilization (CPU/IO)**:
*   **Steady State:** All priority buckets (Critical to Bulk) are serviced.
*   **Congestion Mode (CPU > 60%):** The `ConcurrencyLimitServletFilter` logic kicks in. The Rate Limiter begins shedding **BULK** and **BEST_EFFORT** requests even if they are under their individual limits, reserving Redis throughput and CPU for **CRITICAL** requests.

### 3.3. Write Path vs. Read Path (CQRS)
*   **Write Path:** Admin UI (Uber-style) updates rules in a Git-backed repo, triggering a **Kafka** event.
*   **Read Path:** The Ingestion service compiles the new rules into a **RAW Hollow** snapshot and propagates it to all nodes for O(1) local lookups.

## 4. Operational Monitoring

### 4.1. Key Metrics & SLIs (Service Level Indicators)
*   **Decision Latency:** P99 target < 2ms (crucial since this sits in the critical path of every Uber/Netflix request).
*   **Shedding Rate by Priority:** Percentage of `DEGRADED` vs. `CRITICAL` requests dropped.
*   **Redis Cache Freshness:** Lag between global counter increments and local enforcement.

### 4.2. Shadow Validations (Uber "Kaptre" Pattern)
Before deploying a new "Aggressive" rate limit rule, we utilize **Shadow Validation**:
1.  **Capture:** Production traffic headers are mirrored.
2.  **Replay:** The Rate Limiter processes the mirrored request against the new rule in a "dry-run" mode.
3.  **Analysis:** If the shadow rule drops >5% of `CRITICAL` traffic, the "confidence score" is lowered, and the build is automatically rolled back (Canary Deployment).

### 4.3. Reliability Mechanisms
*   **Dead Letter Queues (DLQ):** Any rate-limit event that fails due to Redis timeout is logged to a Kafka-backed DLQ for "Completeness Checks" (Uber pattern), ensuring we can audit why a user was incorrectly throttled.
*   **Fail-Open Policy:** If the Rate Limiter service experiences an outage, the API Gateway (Uber Zanzibar) defaults to **Fail-Open**, allowing traffic through but flagging it with a `X-RateLimit-Error` header for downstream load shedding.