# hookshot

Lightweight webhook relay server for local development with request inspection and replay.

---

## Installation

```bash
pip install hookshot
```

Or install from source:

```bash
git clone https://github.com/youruser/hookshot.git && cd hookshot && pip install -e .
```

---

## Usage

Start the relay server and forward incoming webhooks to your local service:

```bash
hookshot start --port 8080 --forward http://localhost:3000/webhook
```

Hookshot will provide a public URL you can register with your webhook provider. All requests are logged to the terminal for inspection.

**Replay a previous request:**

```bash
hookshot replay --id req_a1b2c3
```

**List captured requests:**

```bash
hookshot list
```

**Inspect a specific request:**

```bash
hookshot inspect --id req_a1b2c3
```

---

## How It Works

1. Hookshot exposes a public endpoint that receives webhook payloads.
2. Incoming requests are forwarded to your specified local URL.
3. All request headers, body, and metadata are stored locally for inspection and replay.

---

## Requirements

- Python 3.8+
- An internet connection for the public relay tunnel

---

## License

This project is licensed under the [MIT License](LICENSE).