---
layout: post
title: google gmail auth system (LLD)
author: sal
date: 2026-01-16-17:58:27
categories: [ system design, tutorial ]
image: assets/images/4.jpg
---

This Low-Level Design (LLD) synthesizes lessons from the Google 2020 authentication outage (quota-system migration failure), the Cloudflare 2025 "Bot Management" feature file incident (memory preallocation limits), and modern distributed systems best practices (Paxos, gRPC, strong consistency).

# Low-Level Design: google gmail auth system

## 1. Data Schema & Persistence

The system utilizes a globally distributed, sharded database (based on Spanner/Paxos principles) to balance strong consistency for security with regional low-latency reads.

### 1.1. Account Database (NoSQL/Spanner Style)
**Table:** `UserCredentials`
| Field | Type | Description |
| :--- | :--- | :--- |
| `user_id` | `int64` | Primary Key (Internal immutable ID). |
| `email_canonical` | `string` | Indexed for lookup (e.g., "user@gmail.com"). |
| `password_kdf` | `bytes` | Argon2 or Scrypt hashed password + salt. |
| `mfa_config` | `jsonb` | TOTP secrets, WebAuthn public keys, recovery codes. |
| `account_status` | `enum` | ACTIVE, LOCKED, PENDING_MIGRATION, DELETED. |
| `version_id` | `int64` | Paxos sequence number for consistency checks. |
| `last_updated_ts` | `timestamp` | ISO-8601 UTC (strict validation). |

### 1.2. Quota & Usage Schema (In-Memory/Distributed)
**Table:** `ServiceQuota`
*Designed to prevent the "0-reported usage" bug seen in the 2020 outage.*
| Field | Type | Description |
| :--- | :--- | :--- |
| `service_key` | `string` | "UserIDService_AuthLookups". |
| `tenant_id` | `string` | Identity of the calling internal service. |
| `current_usage` | `atomic_int` | High-frequency counter. |
| `hard_limit` | `int64` | Fail-closed threshold. |
| `grace_period_limit` | `int64` | Temporary threshold during system migrations. |

## 2. API Specifications (Internal gRPC)

Internal services (Gmail, Drive, etc.) communicate with the **User ID Service** via gRPC for type safety and streaming capabilities.

### 2.1. Authenticate (Unary RPC)
**Request:**
```protobuf
message AuthRequest {
  string email = 1;
  string plain_password = 2;
  AuthContext context = 3; // IP, DeviceID, AppID
}
```
**Response:**
```protobuf
message AuthResponse {
  enum Result { SUCCESS = 0; CHALLENGE_REQUIRED = 1; FAIL = 2; STALE_DATA = 3; }
  Result status = 1;
  string session_token = 2;
  MfaChallenge challenge = 3;
  int64 paxos_version = 4; // Used to detect outdated data rejection
}
```

### 2.2. ValidateSession (Unary RPC)
Utilized for high-frequency session checks at the edge proxy level.

## 3. Implementation Details & Algorithms

### 3.1. Paxos-Based Consistency & "Stale Data" Logic
To maintain security, the system prioritizes **Consistency** over **Availability** (CP in CAP). 
*   **Paxos Leader:** Regional instances nominate a leader for writes (e.g., password changes, lockouts).
*   **Rejection Logic:** If a read replica detects its `version_id` is significantly behind the global leader (heartbeat delta > threshold), it must return `STALE_DATA` rather than risk authenticating a revoked user.
*   **Write Capacity Safety:** The Paxos leader requires a non-zero write-quota to commit logs. To prevent the 2020 outage scenario, the quota system implements a **Safe-Default** where a failure to fetch quota results in a "Soft-Fail" (allow cached limit) rather than "Hard-Fail" (limit = 0).

### 3.2. Quota Enforcement Logic (The Migration Pattern)
During migrations between quota systems, the logic uses a **Dual-Write/Single-Read** strategy:
1.  **Ingress:** Update usage in both Old and New systems.
2.  **Authority:** Check usage against the "Authoritative" system defined by a dynamic feature flag.
3.  **Circuit Breaker:** If `Usage == 0` is reported by the New system during a migration phase, the system triggers an automated "Sanity Check" against the Old system to prevent mass-lockouts.

### 3.3. Memory Management: Dynamic Preallocation
Learning from the Cloudflare 2025 "Feature File" panic, the Auth System's configuration loader (handling bot signals or security rules) uses **Dynamic Vectors** with **Strict Upper Bounds** rather than `unwrap()` on fixed-size buffers:
```rust
// Prevents panic if config file size doubles due to DB permission error
fn load_config(data: Vec<u8>) -> Result<Config, Error> {
    if data.len() > MAX_SAFE_BUFFER_SIZE {
        Metrics::log_anomaly("ConfigSizeOverflow", data.len());
        return Err(Error::ConfigTooLarge); // Fallback to last-known-good
    }
    // Use safe parsing, avoid .unwrap()
}
```

## 4. Operational Monitoring

### 4.1. Key Service Level Indicators (SLIs)
*   **Availability:** Successful `AuthResponse` / Total Requests (Target: 99.999%).
*   **Latency:** p99 for `ValidateSession` (Target: < 5ms).
*   **Freshness:** Max delta between regional replica `version_id` and Paxos Leader `version_id`.

### 4.2. Critical Anomaly Detection (AIOps Alerts)
*   **The "Flatline" Alert:** Trigger a SEV-0 if any "Usage" metric drops to 0 while "Inbound Request" volume remains constant (directly targeting the 2020 outage signature).
*   **Metadata Duplicate Alert:** Monitor the row-count of database metadata queries. If ClickHouse/Spanner metadata row-counts double within a single deployment window, trigger an automated rollback of permission changes.
*   **Dependency Independence:** Monitoring and internal emergency communication tools (e.g., Status Page) are hosted on an isolated infrastructure (different TLD and identity provider) to ensure visibility during a global auth failure.