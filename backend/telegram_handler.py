from fastapi import Request

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.debug(f"HTTP request start: {request.method} {request.url}")
    try:
        response = await call_next(request)
    except Exception as e:
        logging.exception("Exception in request handling")
        raise
    logging.debug(f"HTTP request end: {request.method} {request.url} -> {response.status_code}")
    return response
