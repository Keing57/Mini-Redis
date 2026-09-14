# Mini-Redis

A fully functional, multi-threaded in-memory data structure store built entirely from scratch in Python. It mimics the behavior of a real Redis server, communicating over TCP sockets on port 6379. 

I built this project through 34 iterative versions to deeply understand socket programming, concurrency, and in-memory data management.

## Features
*   **Multi-threaded Architecture:** Handles multiple concurrent client connections safely using thread locks.
*   **Supported Data Structures:** Strings, Lists, Hashes, Sets, and Sorted Sets (ZSET).
*   **Persistence:** Background snapshot saving (`BGSAVE`) to a `dump.json` file to prevent data loss on restart.
*   **Key Expiration:** Millisecond-precision TTL support (`EXPIRE`, `PEXPIRE`, `PERSIST`).
*   **Transactions:** Queueing commands with `MULTI`, `EXEC`, and `DISCARD`.
*   **Iterators:** Non-blocking `SCAN` implementation with glob-style pattern matching.
*   **CLI Client:** Includes a custom interactive CLI tool with command history.

## Getting Started
Start the server:
python server.py

Connect using the custom client:
python client.py

Or just use netcat:
nc 127.0.0.1 6379
