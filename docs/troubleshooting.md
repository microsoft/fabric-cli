---
hide:
  - navigation
  #- toc
---

# Troubleshooting

This page contains common issues and their solutions when using the Fabric CLI.

## Encrypted cache error

| Issue | `[AuthenticationFailed] Encrypted cache error` on first launch |
|-------|----------------------------------------------------------------|
| **Cause** | System cannot securely encrypt authentication tokens (missing encryption libraries, containerized environment, security policies, or dependency issues) |
| **Solution** | Enable plaintext fallback: `fab config set encryption_fallback_enabled true` |
| **Security Note** | Tokens stored unencrypted in `~/.config/fab/cache.bin` - use caution on shared systems |
