"""
SARMAAN e-Playbook backend entrypoint.

Phase 2 scope: app boots, exposes a health endpoint, and wires up router
stubs for the domains defined in the architecture doc. Real business logic
for each router lands in later phases (auth in Phase 4, content/releases in
Phases 5-6, sync/ai in later phases).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import health, auth, modules, languages, media, videos, releases, sync, ai, analytics, audit

settings = get_settings()

app = FastAPI(
    title="SARMAAN e-Playbook API",
    version="0.1.0",
    description="Backend API for the SARMAAN e-Playbook admin portal and mobile app.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(modules.router, prefix="/modules", tags=["modules"])
app.include_router(languages.router, prefix="/languages", tags=["languages"])
app.include_router(media.router, prefix="/media", tags=["media"])
app.include_router(videos.router, prefix="/videos", tags=["videos"])
app.include_router(releases.router, prefix="/releases", tags=["releases"])
app.include_router(sync.router, prefix="/sync", tags=["sync"])
app.include_router(ai.router, prefix="/ai", tags=["ai"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(audit.router, prefix="/audit", tags=["audit"])


@app.get("/", tags=["health"])
def root():
    return {"service": "sarmaan-eplaybook-api", "status": "ok", "version": app.version}
