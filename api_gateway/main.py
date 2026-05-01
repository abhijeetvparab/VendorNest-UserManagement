import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="VendorNest API Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVICE_MAP = {
    "/api/auth":    "http://localhost:8001",
    "/api/users":   "http://localhost:8002",
    "/api/vendors": "http://localhost:8003",
}


def _resolve(path: str) -> str | None:
    for prefix, target in SERVICE_MAP.items():
        if path.startswith(prefix):
            return target
    return None


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "app": "VendorNest API Gateway", "version": "1.0.0",
            "services": {"auth": ":8001", "users": ":8002", "vendors": ":8003"}}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy", "service": "gateway"}


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy(path: str, request: Request):
    full_path = f"/api/{path}"
    target = _resolve(full_path)
    if target is None:
        return Response(content='{"detail":"Service not found"}', status_code=404,
                        media_type="application/json")

    url = f"{target}{full_path}"
    if request.url.query:
        url += f"?{request.url.query}"

    body = await request.body()
    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in ("host", "content-length")}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.request(
            method=request.method,
            url=url,
            content=body,
            headers=headers,
        )

    excluded = {"transfer-encoding", "content-encoding", "content-length", "connection"}
    fwd_headers = {k: v for k, v in resp.headers.items() if k.lower() not in excluded}

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=fwd_headers,
        media_type=resp.headers.get("content-type"),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_gateway.main:app", host="0.0.0.0", port=8000, reload=True)
