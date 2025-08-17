from ..main import app as _app
from .routers import watchlist, why_moving, screeners
import os

# Reuse the main application defined in backend/main.py
app = _app

# Include new watchlist router under /api/watchlist
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(why_moving.router, prefix="/api/why-moving", tags=["why_moving"])

# Optional screeners feature flag (default on)
if os.getenv("FF_SCREENERS", "true").lower() == "true":
    app.include_router(screeners.router, prefix="/api/screeners", tags=["screeners"])
