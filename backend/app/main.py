from ..main import app as _app
from .routers import watchlist, why_moving

# Reuse the main application defined in backend/main.py
app = _app

# Include new watchlist router under /api/watchlist
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(why_moving.router, prefix="/api/why-moving", tags=["why_moving"])
