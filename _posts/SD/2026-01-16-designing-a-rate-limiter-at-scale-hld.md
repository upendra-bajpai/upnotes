---
layout: post
title: Designing a Rate Limiter at Scale (HLD)
author: sal
date: 2026-01-16-18:33:49
categories: [ system design, tutorial ]
image: assets/images/4.jpg
---

This High-Level Design (HLD) synthesizes large-scale architectural patterns from Netflix and Uber—specifically **CQRS for configuration management**, **Prioritized Load Shedding**, and **Middleware-driven Gateway architecture**—to build a robust, globally distributed Rate Limiter.

---

# High-Level Design: Designing a Rate Limiter at Scale

## 1. Architectural Overview
This design utilizes a **Control Plane/Data Plane separation**. The Data Plane (API Gateway) handles request-time enforcement using in-memory state, while the Control Plane (Configuration Service) manages rule distribution using a CQRS pattern inspired by Netflix’s "RAW Hollow" for high-density, low-latency metadata distribution.

```mermaid
graph TD
    User((User/Client)) -->|Request| Gateway[API Gateway / Edge]
    
    subgraph "Data Plane (Enforcement)"
        Gateway -->|Middleware| RL_Logic[Rate Limit Middleware]
        RL_Logic -->|O(1) Check| LocalCache[(In-Memory State: RAW Hollow)]
        RL_Logic -->|Incr/Decr| RedisCluster[(Global Distributed Counter: Redis)]
    end

    subgraph "Control Plane (Management)"
        Admin[Admin/Dev Portal] -->|Define Rules| ConfigService[Config Management Service]
        ConfigService -->|Publish| Kafka((Kafka Events))
        Kafka -->|Ingest| StateProducer[RAW Hollow Producer]
        StateProducer -->|Broadcast Snapshot| LocalCache
    end

    subgraph "Observability & Validation"
        RL_Logic -->|Async Metrics| Telemetry[Prometheus/Grafana]
        RL_Logic -->|Shadow Mode| ShadowValidator[Shadow Testing Engine]
    end

    RL_Logic -->|Allow| Backend[Downstream Microservices]
    RL_Logic -->|Block 429| User
```

---

## 2. Core Components

### A. The Middleware Layer (Data Plane)
Inspired by **Uber’s API Gateway**, the rate limiter is implemented as a pluggable middleware within the request lifecycle. It performs:
*   **Protocol Management:** Deserializes JSON, Thrift, or Protobuf to extract identity keys (e.g., `user_id`, `api_key`).
*   **Identification:** Uses headers or JWT claims to bucket the request into priority tiers (**Critical, Degraded, Best Effort, Bulk**), a strategy proven by **Netflix’s Load Shedding** model.

### B. Distributed State & Local Cache
To solve the "Consistency vs. Latency" trade-off:
*   **Global Counters:** A Redis Cluster handles global quotas for strict enforcement.
*   **RAW Hollow Integration:** We use Netflix’s **RAW Hollow** to distribute the "Rate Limit Rules" (the metadata) to every Gateway node. This allows the middleware to perform rule lookups in $O(1)$ time with zero I/O, as the entire rule set resides in the application's RAM.

### C. Priority Engine & Load Shedder
Rather than a "one-size-fits-all" drop, the system incorporates **Service-Level Prioritization**:
*   **CPU/IO Feedback:** If the downstream service reports high CPU utilization (via Netflix's feedback loop), the Rate Limiter dynamically tightens quotas for "Bulk" and "Best Effort" tiers while preserving "Critical" traffic (e.g., login or payment flows).

### D. Shadow Testing Engine
Following **Uber’s Accounting Data Testing** strategies, new rate-limiting rules are first deployed in **Shadow Mode**. The system processes the limit logic but does not drop the request; instead, it logs "Would-Have-Blocked" events to a datastore to analyze potential False Positives before moving to active enforcement.

---

## 3. System Attributes

### Scalability
*   **Horizontal Growth:** The Data Plane (Gateway) is stateless. Adding more nodes linearly increases the capacity to handle requests.
*   **Config Distribution:** By using **RAW Hollow**, we avoid the "N+1 lookup" problem. As the number of rules grows, the compressed in-memory footprint remains minimal (25% of uncompressed size).

### Availability
*   **Fail-Open Strategy:** If the Redis Cluster or the RAW Hollow distribution fails, the middleware defaults to "Allow." In a top-tier system, it is better to risk overloading a service than to block 100% of legitimate traffic due to a limiter failure.
*   **Regional Isolation:** Rate limiters are deployed per region to minimize cross-region latency (the "Speed of Light" constraint).

### Durability
*   **CQRS for Rules:** Configurations are stored in a persistent RDBMS and broadcast via Kafka. This ensures that even if a region is wiped, the "Source of Truth" for rate-limit policies is preserved and can be re-hydrated into the RAW Hollow snapshots.

---

## 4. Key Takeaways & Trade-offs

### I/O is the Enemy of Performance
Traditional rate limiters call a database/cache for every request. By using **RAW Hollow**, we eliminate rule-fetch I/O. As Netflix discovered with their Tudum architecture, moving data to the "near cache" (in-memory) reduced homepage construction from 1.4s to 0.4s. We apply this same logic to the Rate Limiter to keep P99 overhead < 1ms.

### Eventual Consistency vs. Strict Limits
We accept **Eventual Consistency** for configuration updates. If an Admin changes a limit from 100 to 200, it may take a few seconds for all Gateway nodes to receive the new RAW Hollow snapshot via Kafka. This is a deliberate trade-off to ensure the Data Plane never blocks on a Control Plane update.

### Testing in Production (Safe Deployment)
Rate limiters are dangerous—a bug can cause a total site outage. We adopt **Uber’s Canary and Shadow Testing** approach. Every rate-limit change goes through:
1.  **Shadow Validation:** Measure impact on production traffic without blocking.
2.  **Canary Deployment:** Enable enforcement for <2% of traffic.
3.  **Full Rollout:** Monitored by threshold-based alerts on "Dead Letter Queues" and error loggers.

### Dynamic vs. Static Limits
Static limits (e.g., 5 requests/sec) are fragile. By synthesizing **Netflix’s Prioritized Load Shedding**, our design allows the rate limiter to be "application-aware," shedding low-priority background tasks when the system detects congestive failure patterns, thus ensuring maximum reliability for the end-user.