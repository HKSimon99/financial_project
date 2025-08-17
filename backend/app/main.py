from ..main import app as _app
from .routers import watchlist

# Reuse the main application defined in backend/main.py
app = _app

# Include new watchlist router under /api/watchlist
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
