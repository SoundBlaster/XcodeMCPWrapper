# P13-T1: Design Persistent Broker Architecture and Protocol Contract

**Phase:** 13 — Persistent Broker & Shared Xcode Session
**Priority:** P0
**Status:** In Progress
**Branch:** feature/P13-T1-persistent-broker-architecture
**Created:** 2026-02-16

---

## 1. Objective

Define the architecture, transport contract, and module scaffold for a long-lived broker process that owns a single `xcrun mcpbridge` upstream connection and multiplexes multiple MCP clients through it.

This is a **design-only** task. The deliverables are:

1. `SPECS/ARCHIVE/P13-T1_.../broker_architecture_spec.md` — lifecycle and sequence diagrams
2. `SPECS/ARCHIVE/P13-T1_.../adr_broker_transport_security.md` — ADR (transport + security)
3. `src/mcpbridge_wrapper/broker/__init__.py` — initial module scaffold (stubs only, no logic)
4. `src/mcpbridge_wrapper/broker/daemon.py` — stub
5. `src/mcpbridge_wrapper/broker/transport.py` — stub
6. `src/mcpbridge_wrapper/broker/proxy.py` — stub
7. `src/mcpbridge_wrapper/broker/types.py` — shared type definitions

---

## 2. Background

Currently every MCP client that connects spawns a fresh `xcrun mcpbridge` subprocess. This causes:
- Repeated Xcode permission prompts (BUG-T4)
- Higher startup latency per session
- Process accumulation under load

A persistent broker resolves these by owning one upstream subprocess and serving N concurrent clients via a local transport.

---

## 3. Architecture Specification

### 3.1 Component Roles

| Component | Role |
|-----------|------|
| **Broker Daemon** | Long-lived process, owns `xcrun mcpbridge` subprocess, accepts local client connections |
| **Upstream Bridge** | Single `xcrun mcpbridge` process, its stdin/stdout are owned exclusively by the Broker |
| **Client Proxy** | Short-lived per-MCP-client subprocess; connects to Broker via Unix socket, bridges client stdio ↔ Broker |
| **Web UI** | Continues attaching to Broker process (reuse existing mechanism) |

### 3.2 Lifecycle States

```
Broker Daemon

   INIT
    │   Create socket file (mode 0600)
    │   Write PID lock file
    │   Launch xcrun mcpbridge upstream
    ▼
  READY ──────────────────────────────────────────┐
    │   Accept client connections                  │
    │   Forward requests to upstream               │ client disconnect
    │   Route responses back to originating client │ (no effect on upstream)
    │                                              │
    ▼                                              │
  BUSY ◄──────────────────────────────────────────┘
    │
    │  upstream crash/EOF
    ▼
  RECONNECTING
    │   Relaunch xcrun mcpbridge (backoff: 0s, 1s, 2s, 5s)
    │   Fail pending requests with JSON-RPC error -32001
    ▼
  READY  (on success)
    │
    │  SIGTERM / SIGINT / broker stop command
    ▼
  STOPPING
    │   Drain in-flight requests (grace period: 5s)
    │   Send EOF to upstream subprocess
    │   Close all client connections with JSON-RPC error -32000
    │   Remove socket file and PID file
    ▼
  STOPPED
```

### 3.3 Stale-Socket Recovery

On startup, if `broker.sock` exists:

1. Read PID file. If PID file missing → remove socket, continue.
2. `kill -0 <pid>` — if process alive → refuse to start (another instance running).
3. If process dead → remove socket and PID file, continue startup.

### 3.4 Request/Response Correlation

JSON-RPC allows concurrent requests. The broker must route each response to the correct client.

**Strategy: ID-namespace remapping**

- Each client has a sequential `client_id` assigned on connect (monotonic counter, reset on restart).
- Outgoing request IDs are remapped: `broker_id = (client_id << 20) | original_id`.
  - Supports up to 2^20 = 1 048 576 concurrent request IDs per client.
  - Supports up to 2^44 clients before wrap-around (sufficient for any realistic session).
- Upstream receives remapped IDs. Responses arrive with remapped IDs.
- Broker extracts `client_id = broker_id >> 20`, looks up active client session, restores `original_id`, forwards response.
- JSON-RPC notifications (`id == null`) are broadcast to all active clients.

**Edge cases:**
- Client disconnects with in-flight requests → broker discards responses for that `client_id`.
- Upstream sends a response for unknown remapped ID → log warning, discard.
- String IDs: if `original_id` is a string, broker uses a per-client string→int mapping table, restores string on response.

### 3.5 Sequence Diagram — Normal Request

```
Client A              Broker Daemon            Upstream Bridge
   │                       │                         │
   │  {"id":1,"method":    │                         │
   │   "tools/call",...}   │                         │
   │──────────────────────►│                         │
   │                       │  remap id: 1 → A<<20|1 │
   │                       │──────────────────────── ►│
   │                       │                         │
   │                       │◄────────────────────────│
   │                       │  {"id": A<<20|1, ...}   │
   │                       │  restore id: → 1        │
   │◄──────────────────────│                         │
   │  {"id":1,"result":..} │                         │
```

### 3.6 Sequence Diagram — Upstream Reconnect

```
Broker Daemon            Upstream Bridge
     │                         │
     │◄── EOF/crash ───────────┤
     │                         X
     │  → fail pending reqs (-32001)
     │  → enter RECONNECTING state
     │  → backoff: 0s
     │  → launch new xcrun mcpbridge
     │──────────────────────── ► (new upstream)
     │  → enter READY state
```

### 3.7 Sequence Diagram — Client Proxy Connect

```
MCP Client (stdio)     Client Proxy              Broker Daemon
      │                     │                          │
      │                     │  connect(broker.sock)    │
      │                     │─────────────────────────►│
      │                     │◄─── ACK (session_id) ───│
      │  JSON-RPC request   │                          │
      │────────────────────►│  forward (with remap)   │
      │                     │─────────────────────────►│
      │                     │◄── response (remapped) ─│
      │◄── JSON-RPC resp ───│  restore id             │
      │                     │                          │
      │  EOF / disconnect   │                          │
      │────────────────────►│  close session           │
      │                     │─────────────────────────►│
      │                     X  (broker drops client)   │
      │                                                │ (upstream stays alive)
```

---

## 4. ADR: Transport and Security Choices

### ADR-001: Transport — Unix Domain Socket (UDS)

**Status:** Accepted

**Context:**
The broker serves local clients only. Options considered:
- TCP loopback (localhost:port)
- Unix domain socket (`/tmp/mcpbridge_wrapper/broker.sock` or `$XDG_RUNTIME_DIR/...`)
- Named pipe (macOS / FIFO)

**Decision:** Unix domain socket (`{data_dir}/broker.sock`)

**Rationale:**
- No port allocation conflicts
- Kernel enforces filesystem permissions (mode 0600 → owner-only access)
- `SO_PEERCRED` / `getpeereid()` can verify connecting process UID at OS level
- Standard on macOS and Linux; no external library required
- Lower attack surface than TCP (no remote access even on misconfigured hosts)

**Consequences:**
- Clients on Windows cannot use Unix sockets (acceptable: Xcode is macOS-only)
- Socket path must survive `tmp` cleanup (use `~/.local/share/mcpbridge_wrapper/` or `$HOME/.mcpbridge_wrapper/`)

### ADR-002: Security — Local Peer Credential Verification

**Status:** Accepted

**Context:**
How to prevent an unprivileged local process from hijacking the broker.

**Decision:** Verify peer UID on every new connection using `getpeereid()`.

**Rules:**
- Accept connections only from the same UID as the broker process.
- Immediately close connections from mismatched UIDs.
- No bearer tokens needed for same-user local communication (threat model: multi-user host; single-user laptop is lower risk).

**Consequences:**
- Multi-user setups each get their own broker instance (by UID isolation).
- No encryption needed for loopback UDS.

### ADR-003: Socket File Location

**Status:** Accepted

**Decision:** Default socket path = `~/.mcpbridge_wrapper/broker.sock`
PID file path = `~/.mcpbridge_wrapper/broker.pid`

**Rationale:**
- Survives `tmp` cleanup
- Predictable across reboots
- User-writable without `sudo`
- Matches existing `data_dir` conventions used by the Web UI audit log

### ADR-004: Reconnect Backoff

**Status:** Accepted

**Decision:** Exponential backoff with cap: `min(2^attempt, 30)` seconds, starting at 0s.
Max attempts: unlimited (broker does not give up; operational intervention expected).
During RECONNECTING, new client connections are accepted but get a pending-queue entry; they are served once upstream comes back (up to 60s queue TTL).

---

## 5. Module Scaffold

```
src/mcpbridge_wrapper/broker/
├── __init__.py      # Public exports: BrokerDaemon, BrokerProxy, BrokerConfig
├── types.py         # Shared dataclasses: ClientSession, PendingRequest, BrokerState
├── daemon.py        # BrokerDaemon class (lifecycle, upstream management)
├── transport.py     # UnixSocketServer (accept loop, client session management)
└── proxy.py         # BrokerProxy (stdio ↔ socket forwarding for client processes)
```

**Key Types (types.py):**

```python
@dataclass
class BrokerConfig:
    socket_path: Path
    pid_file: Path
    upstream_cmd: list[str]  # e.g. ["xcrun", "mcpbridge"]
    reconnect_backoff_cap: int = 30  # seconds
    queue_ttl: int = 60              # seconds
    graceful_shutdown_timeout: int = 5

@dataclass
class ClientSession:
    session_id: int
    peer_uid: int
    connected_at: float
    writer: asyncio.StreamWriter
    pending: dict[int, asyncio.Future]   # broker_id → Future

@dataclass
class PendingRequest:
    client_id: int
    original_id: int | str
    broker_id: int
    queued_at: float

class BrokerState(enum.Enum):
    INIT = "init"
    READY = "ready"
    RECONNECTING = "reconnecting"
    STOPPING = "stopping"
    STOPPED = "stopped"
```

---

## 6. Acceptance Criteria (per Workplan)

- [ ] Architecture covers startup, shutdown, reconnect, and stale-socket recovery ✅ (§3.2, §3.3)
- [ ] Correlation strategy for concurrent JSON-RPC requests is specified ✅ (§3.4)
- [ ] Security boundary for local clients is documented ✅ (ADR-001, ADR-002)
- [ ] Design is reviewed and approved for implementation

---

## 7. Out of Scope

- Actual implementation of daemon logic (P13-T2)
- Multi-client transport logic (P13-T3)
- Client proxy mode (P13-T4)
- Integration testing (P13-T5)
- Documentation updates (P13-T6)

---

## 8. Dependencies

| Dependency | Status |
|------------|--------|
| P2-T6: Subprocess wrapper (`bridge.py`) | ✅ Complete |
| P3-T10: Response transformation | ✅ Complete |
