# Brahma Connect

Brahma Connect is the local multi-device transport layer for Ultron Jarvis (Hidayat AI).

It keeps the AI brain inside the existing Brahma desktop app and adds a
gateway that can pair with companion devices on the local network.

## Included foundation

- FastAPI and WebSocket gateway scaffold
- Persistent device registry
- Temporary pairing offers with expiring codes
- Device capability tracking
- Command routing skeleton
- Optional mDNS discovery via Zeroconf when installed
- JSON protocol definitions with required message fields

## Protocol

Every message includes:

- `type`
- `request_id`
- `timestamp`
- `payload`

See [`agents/PROTOCOL.md`](agents/PROTOCOL.md) for the message contract and the
initial handshake flow.
