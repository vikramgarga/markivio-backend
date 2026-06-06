from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import diagnose, intake, research, synthesize, briefs

app = FastAPI(
    title="Markivio Backend",
    description="Strategy Studio — multi-stage human + AI consulting workflow",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Legacy single-pass endpoints (kept for backward compatibility)
app.include_router(diagnose.router, prefix="/api")
app.include_router(intake.router, prefix="/api")
app.include_router(research.router, prefix="/api")
app.include_router(synthesize.router, prefix="/api")

# Strategy Studio — multi-stage workflow
app.include_router(briefs.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
