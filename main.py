from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import diagnose, intake, research, synthesize

app = FastAPI(
    title="Markivio Backend",
    description="Phase 1 MVP — Diagnostic + Intake + Research + Synthesize",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(diagnose.router, prefix="/api")
app.include_router(intake.router, prefix="/api")
app.include_router(research.router, prefix="/api")
app.include_router(synthesize.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
