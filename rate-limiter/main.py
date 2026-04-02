from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import redis
import time

app = FastAPI()

r = redis.Redis(host='localhost', port=6379, db=0)

LIMIT = 5        # max requests
WINDOW = 60      # seconds

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host

    #Bypass the rate limiter for health check
    if request.url.path == "/health":
        return await call_next(request)
    
    # Get current time and window start
    now = time.time()
    window_start = now - WINDOW

    # Add current timestamp to sorted set
    r.zadd(client_ip, {now: now})
    r.expire(client_ip, WINDOW)

    # Remove timestamps older than 60 seconds
    r.zremrangebyscore(client_ip, 0, window_start)

    # Count requests in current window
    request_count = r.zcount(client_ip, window_start, now)

    print(f"IP: {client_ip} | Requests in last 60s: {request_count}")

    if request_count > LIMIT:
        return JSONResponse(
            status_code=429,
            content={"error": "Too many requests, slow down."},
            headers={
                "Retry-After": str(WINDOW),
                "X-RateLimit-Limit": str(LIMIT),
                "X-RateLimit-Remaining": str(max(0, LIMIT - request_count))
            }
        )

    response = await call_next(request)
    return response

@app.get("/")
def root():
    return {"message": "hello"}


@app.get("/health")
def health():
    return {"status": "ok"}