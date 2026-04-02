# Redis Rate Limiter API

A small FastAPI project that applies per-IP rate limiting with Redis.

## Features

- FastAPI application with Redis-backed request tracking
- Sliding-window rate limiting on the `/` endpoint
- `/health` endpoint excluded from rate limiting
- Pytest test suite for basic behavior and rate-limit headers

## Project Structure

```text
rate-limiter/
  main.py
  test_main.py
requirements.txt
```

## Requirements

- Python 3.11+
- Redis running on `localhost:6379`

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run The API

```bash
uvicorn rate-limiter.main:app --reload
```

If your shell has trouble importing from the `rate-limiter` directory name, run from inside that folder instead:

```bash
cd rate-limiter
uvicorn main:app --reload
```

## Endpoints

### `GET /`

Returns:

```json
{"message": "hello"}
```

After more than 5 requests within 60 seconds from the same client IP, the API returns `429 Too Many Requests`.

Rate-limit response headers include:

- `Retry-After`
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`

### `GET /health`

Returns:

```json
{"status": "ok"}
```

This endpoint is not rate-limited.

## Run Tests

```bash
.venv/bin/python -m pytest -q rate-limiter/test_main.py
```

The tests expect Redis to be available on `localhost:6379`.

## Upload To GitHub

1. Initialize git:

```bash
git init
git add .
git commit -m "Initial commit"
```

2. Create an empty GitHub repository.
3. Connect the local folder to GitHub and push:

```bash
git remote add origin <your-repo-url>
git branch -M main
git push -u origin main
```

## Notes

- Current rate-limit settings are defined in `rate-limiter/main.py` as:
  - `LIMIT = 5`
  - `WINDOW = 60`
- Redis must be running before starting the API or tests.
