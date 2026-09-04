# Brahma Connect Protocol

Brahma Connect uses a small JSON protocol so Brahma, companion apps, and
device agents can communicate consistently over WebSocket.

## Required envelope

Every message must contain:

- `type`
- `request_id`
- `timestamp`
- `payload`

Example:

```json
{
  "type": "hello",
  "request_id": "c5b6f5d6b2f8438f8b7c2b4b27a4f6c1",
  "timestamp": "2026-08-08T10:00:00+00:00",
  "payload": {}
}
```

## Core message types

- `hello`
- `pair_request`
- `pair_approved`
- `authenticate`
- `device_online`
- `device_offline`
- `capabilities`
- `execute`
- `result`
- `event`
- `error`
- `ping`
- `pong`
- `file_transfer`
- `screen_capture`
- `chat_message`

## Expected flow

1. Agent connects and sends `hello`.
2. Gateway responds with a pairing request or known-device instructions.
3. User approves the device in Brahma.
4. Agent sends `authenticate` with the persistent secret.
5. Gateway marks the device online and publishes capabilities.
6. Brahma sends `execute` requests.
7. Agent replies with `result` or `error`.

## Notes

- Pairing offers expire.
- Devices can be revoked or forgotten.
- Capability checks happen before routing commands.
- File transfer and screen capture are modeled as capabilities, not special cases.
