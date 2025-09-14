# Caching

The Fabric CLI provides two types of caching for better experience and security:

## Token Caching

Tokens are managed via Microsoft Authentication Library (MSAL) extensions. By default, tokens are securely encrypted and stored in the user's home directory under `.config/fab/cache.bin`. The platforms that support encryption are: Windows, MacOS, and Linux. Maintain caution when handling or sharing this file, especially on systems without encryption support.

## HTTP Response Caching

Certain endpoints are cached by default to diminish network traffic and improve overall responsiveness.

You can disable this feature by running (the default value is `true`):

```
fab config set cache_enabled false
```

To clear cached HTTP responses, run:

```
fab config clear-cache
```
