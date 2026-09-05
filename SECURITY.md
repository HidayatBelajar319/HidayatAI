# Security Policy

## Supported Versions

Security fixes should be applied to the latest maintained version of this repository.

## Reporting a Vulnerability

If you discover a security issue, do not post secrets or exploit details in public issues.

Please report security concerns through a private channel or repository owner contact method.

## Responsible Disclosure

- Do not share API keys, bot tokens, or access credentials publicly.
- Revoke any exposed credentials immediately.
- Update local configuration files after rotating secrets.

## Ultron Jarvis Security Overview

This repository includes a security overview for Ultron Jarvis's current runtime model, gateway exposure, and authentication flow.

### Local credential handling

- API keys are stored in `config/api_keys.json`.
- The code reads `gemini_api_key` and `openrouter_api_key` directly from this file.
- This file is a local configuration artifact and should never be committed to source control.
- There is no built-in secret vault; security depends on file system permissions and local access controls.

### AI provider access

- Ultron Jarvis uses Gemini as the primary AI provider and OpenRouter as a fallback.
- Both API keys are loaded from the local config file and sent to the respective service clients.
- `config/api_keys.json` is plaintext JSON and is not encrypted by the application.

### Ultron Jarvis Connect gateway exposure

Ultron Jarvis Connect is the local device gateway layer for Ultron Jarvis.

#### Configuration

- Default gateway config: `config/brahma_connect.json`
- Default host: `0.0.0.0`
- Default port: `8765`
- Default advertise: `true`
- Default pairing TTL: `300` seconds

Because the gateway binds to `0.0.0.0`, it is reachable from any interface on the host unless OS firewall rules block it.

#### Discovery

- Optional mDNS discovery is provided through `brahma_connect.gateway.discovery.GatewayDiscovery` and Zeroconf.
- Discovery advertises service `_BRAHMA._tcp.local.` only when the Zeroconf library is installed and `advertise` is enabled.

#### Local network consideration

- The gateway is designed as a local network transport.
- There is no built-in TLS/SSL for the gateway websocket in the current code.
- Gateway traffic is not encrypted end-to-end by default and relies on LAN trust.

### Pairing and authentication flow

#### Pairing

- Pairing uses a temporary pairing offer created by `brahma_connect.gateway.pairing.PairingManager`.
- Each offer includes a `pairing_token`, a 6-digit `pairing_code`, and an expiration timestamp.
- Pairing offers expire after `pairing_ttl_seconds` (default 300 seconds).

#### Approval

- Incoming device connections begin with `HELLO` and create a pending request.
- A user must explicitly approve or reject each pending pairing request through the app.
- Approved devices are added to the registry and issued a permanent `device_secret`.

#### Device credentials

- Device records are stored in `config/brahma_connect/devices.json`.
- Device secrets are not stored plaintext; the repository stores a `secret_hash`.
- The `secret_hash` is computed using `hashlib.sha256(secret.encode('utf-8')).hexdigest()`.
- Authentication uses constant-time comparison (`hmac.compare_digest`) to avoid timing attacks.

#### Authentication

- Authenticated device connections use the websocket `/ws` endpoint and send an `AUTHENTICATE` message with `device_id` and `device_secret`.
- On successful authentication, the device is marked online and registered in the connection hub.
- Revoked devices are rejected by `DeviceManager.authenticate`.

### Gateway request handling

- The gateway exposes REST endpoints for `/gateway/info`, `/gateway/pair`, `/gateway/devices`, `/gateway/devices/{device_id}/revoke`, `/gateway/devices/{device_id}/forget`, `/gateway/pending`, `/gateway/pending/{pending_id}/approve`, and `/gateway/pending/{pending_id}/reject`.
- These endpoints are exposed on the same host and port as the gateway service.
- There is no API authentication for these admin endpoints in the current code, so local network access is effectively trusted.

### Firewall behavior

#### Dashboard firewall helper

- The local dashboard (`dashboard/server.py`) includes `_ensure_network_access`.
- This helper attempts to open a Windows firewall rule for dashboard ports and includes cross-platform stubs for macOS/Linux.
- The dashboard uses port `8000` by default and a legacy HTTPS alias on `8001`.

#### Gateway firewall behavior

- The gateway does not automatically open OS firewall ports.
- Because it binds to `0.0.0.0:8765`, administrators should verify and restrict firewall access manually if needed.

### Security strengths

- Pairing is explicit and requires user approval.
- Device secret handling uses hashed secrets and constant-time comparison.
- Temporary pairing codes expire quickly.
- Device revocation and forgetting are supported.
- The dashboard encrypts local commands using AES-256-CBC with a session-derived key.

### Security limitations

- No built-in gateway TLS/SSL for WebSocket `/ws`; websocket traffic is plaintext on the LAN.
- Admin REST endpoints have no authentication layer in the current codebase.
- Local API key storage is plaintext.
- The gateway host default of `0.0.0.0` exposes the service broadly unless OS firewall restrictions are applied.
- There is no remote access firewall or gateway-level authentication beyond pairing and device credentials.

### Recommendations

- Keep `config/api_keys.json` private and out of version control.
- Use OS firewall rules to restrict access to port `8765` when Ultron Jarvis Connect is enabled.
- Disable `advertise` in `config/brahma_connect.json` unless discovery is needed.
- Revoke lost or untrusted devices using `/gateway/devices/{device_id}/revoke`.
- Run Ultron Jarvis on a trusted local network.
- Consider adding HTTPS/TLS support for the gateway websocket and admin REST endpoints for secure remote access.

## Anti-Jailbreak & Security Protocol (Hidayat AI)

### Implemented Protections
- Request validation and sanitization (core/security_guard.py)
- Malicious code scanning before execution
- Path traversal prevention
- Command injection prevention
- Rate limiting on API endpoints
- Checksum-based file integrity verification
- Permission bypass detection

### Incident Logging
All security incidents are logged in this file with timestamp, severity, type, details, and action taken.

### Self-Editing Safeguards
- All self-edits restricted to Hidayat-AI-Main/ folder
- Protected files: LICENSE, TRADEMARK.md, main.py, core/*, config/*.json
- Mandatory backups before any edit
- User permission required for every change

## Self-Edit Audit Log
- `2026-09-04T13:09:02` **APPROVED** — target: `20260904_130512_327252_test_restore_target.py` | reason: Restore file from backup '20260904_130512_327252_test_restore_target.py' | detail: restore applied
- `2026-09-04T13:09:02` **APPROVED** — target: `test_restore_target.py` | reason: Edit to v2 | detail: edit applied
- `2026-09-04T13:08:16` **APPROVED** — target: `test_restore_target.py` | reason: Edit to v2 | detail: edit applied
- `2026-09-04T13:07:53` **APPROVED** — target: `test_restore_target.py` | reason: Edit to v2 | detail: edit applied
- `2026-09-04T13:05:12` **APPROVED** — target: `test_restore_target.py` | reason: Edit to v2 | detail: edit applied
- `2026-09-04T13:04:52` **APPROVED** — target: `test_edit_target.py` | reason: Apply improvement | detail: edit applied
- `2026-09-04T13:04:52` **DENIED** — target: `main.py` | reason: Try to edit main.py | detail: path validation failed
- `2026-09-04T13:04:50` **DENIED** — target: `test_edit_target.py` | reason: Should be denied | detail: user denied

- `2026-09-04T13:04:50` **APPROVED** — target: `test_edit_target.py` | reason: Test edit | detail: edit applied

## Security Incident Log
### [2026-09-04 13:08:32] - [CRITICAL] - [CHECKSUM_MISMATCH]
Details: Unauthorized file changes detected: tampered=['F:\\Project\\HidayatAI\\Hidayat-AI-Source-Code\\core\\self_editor.py'], missing=['F:\\Project\\HidayatAI\\Hidayat-AI-Main\\test_edit_target.py', 'F:\\Project\\HidayatAI\\Hidayat-AI-Main\\test_restore_target.py']
Source: self_edit
Action taken: alerted

### [2026-09-04 13:08:31] - [CRITICAL] - [PERMISSION_BYPASS]
Details: Forbidden action attempted even with approval: 'disable security'
Source: self_edit
Action taken: rejected

### [2026-09-04 13:08:31] - [CRITICAL] - [PERMISSION_BYPASS]
Details: Forbidden action attempted even with approval: 'edit security_guard.py'
Source: self_edit
Action taken: rejected

### [2026-09-04 13:08:31] - [CRITICAL] - [PERMISSION_BYPASS]
Details: Attempted high-risk action without approval: 'delete config/api_keys.json'
Source: self_edit
Action taken: rejected

### [2026-09-04 13:08:31] - [HIGH] - [MALICIOUS_PAYLOAD]
Details: Malicious payload from 'plugin': ['EVAL_RAW: eval() usage']
Source: plugin
Action taken: logged

### [2026-09-04 13:08:31] - [HIGH] - [COMMAND_INJECTION]
Details: Command injection attempt in request from 'plugin': 'rm -rf /'
Source: plugin
Action taken: logged

### [2026-09-04 13:08:30] - [HIGH] - [PATH_TRAVERSAL]
Details: Path traversal attempt in request from 'plugin': '../../etc/passwd'
Source: plugin
Action taken: logged

### [2026-09-04 13:08:30] - [HIGH] - [AUTH_MISSING]
Details: Request from 'dashboard' without auth token (user=u1)
Source: dashboard
Action taken: logged

### [2026-09-04 13:06:09] - [LOW] - [TEST_INCIDENT]
Details: Test logging format
Source: plugin
Action taken: logged

### [2026-09-04 13:05:46] - [CRITICAL] - [CHECKSUM_MISMATCH]
Details: Unauthorized file changes detected: tampered=['F:\\Project\\HidayatAI\\Hidayat-AI-Source-Code\\core\\self_editor.py'], missing=['F:\\Project\\HidayatAI\\Hidayat-AI-Main\\test_edit_target.py']
Source: self_edit
Action taken: alerted

### [2026-09-04 13:05:45] - [CRITICAL] - [PERMISSION_BYPASS]
Details: Forbidden action attempted even with approval: 'disable security'
Source: self_edit
Action taken: rejected

### [2026-09-04 13:05:45] - [CRITICAL] - [PERMISSION_BYPASS]
Details: Forbidden action attempted even with approval: 'edit security_guard.py'
Source: self_edit
Action taken: rejected

### [2026-09-04 13:05:45] - [CRITICAL] - [PERMISSION_BYPASS]
Details: Attempted high-risk action without approval: 'delete config/api_keys.json'
Source: self_edit
Action taken: rejected

### [2026-09-04 13:05:45] - [HIGH] - [MALICIOUS_PAYLOAD]
Details: Malicious payload from 'plugin': ['EVAL_RAW: eval() usage']
Source: plugin
Action taken: logged

### [2026-09-04 13:05:45] - [HIGH] - [COMMAND_INJECTION]
Details: Command injection attempt in request from 'plugin': 'rm -rf /'
Source: plugin
Action taken: logged

### [2026-09-04 13:05:45] - [HIGH] - [PATH_TRAVERSAL]
Details: Path traversal attempt in request from 'plugin': '../../etc/passwd'
Source: plugin
Action taken: logged


### [2026-09-04 13:05:44] - [HIGH] - [AUTH_MISSING]
Details: Request from 'dashboard' without auth token (user=u1)
Source: dashboard
Action taken: logged

