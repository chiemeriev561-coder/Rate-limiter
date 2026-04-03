from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import redis
import time
import uuid
from typing import Optional

app = FastAPI()

def get_client_ip(request: Request) -> str:
    if "X-Forwarded-For" in request.headers:
        return request.headers["X-Forwarded-For"].split(",")[0].strip()
    if "X-Real-IP" in request.headers:
        return request.headers["X-Real-IP"]
    return request.client.host or "unknown"

# Better Redis connection (use pool in real app)
r = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=2, socket_timeout=2)

LIMIT = 5
WINDOW = 60  # seconds

# Lua script for atomic sliding window (highly recommended)
LUA_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])

-- Remove old entries
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)

-- Count current requests in window
local count = tonumber(redis.call('ZCARD', key))

if count >= limit then
    return count  -- return current count so we know it's over limit
end

-- Add current request (use unique member to avoid collisions)
local member = ARGV[4]
redis.call('ZADD', key, now, member)
redis.call('EXPIRE', key, window + 10)  -- a bit of extra time

return count + 1
"""

# Load the script once
lua_rate_limit = r.register_script(LUA_SCRIPT)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path == "/health":
        return await call_next(request)

    client_ip = get_client_ip(request)
    redis_key = f"rate:ip:{client_ip}"
    now = int(time.time() * 1000)  # use milliseconds for better precision

    try:
        # Execute atomically
        current_count = lua_rate_limit(
            keys=[redis_key],
            args=[now, WINDOW, LIMIT, f"{now}-{uuid.uuid4().hex[:8]}"]
        )

        print(f"IP: {client_ip} | Requests in window: {current_count}")  # replace with proper logger later

        if current_count > LIMIT:
            return JSONResponse(
                status_code=429,
                content={"error": "Too many requests. Please slow down."},
                headers={
                    "Retry-After": str(WINDOW),
                    "X-RateLimit-Limit": str(LIMIT),
                    "X-RateLimit-Remaining": str(0),
                }
            )

    except redis.RedisError as e:
        # In banking: decide policy — fail closed (block) or fail open (allow with log)
        print(f"Redis error in rate limiter: {e} — allowing request (fail-open for now)")
        # For strict banking, you might want to return 429 or 503 instead

    response = await call_next(request)
    return response

@app.get("/")
def root():
    return {"message": "hello"}


@app.get("/health")
def health():
    return {"status": "ok"}
