import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from user_service.router import router

app = FastAPI(title="VendorNest User Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy", "service": "users"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("user_service.main:app", host="0.0.0.0", port=8002, reload=True)
