# File Storage

The Fabric CLI maintains several files in the user's home directory under `.config/fab/`:

| File                | Description                                                                                                               |
|---------------------|---------------------------------------------------------------------------------------------------------------------------|
| `cache.bin`         | Stores sensitive authentication data and is encrypted by default on supported platforms (Windows, MacOS, and Linux)     |
| `config.json`       | Contains non-sensitive CLI configuration settings and preferences                                                        |
| `auth.json`         | Maintains CLI authentication non-sensitive information                                                                  |
| `context-<session_id>.json` | Stores the current navigational context for the shell session |
