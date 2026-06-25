import pytest
from app.routes import main_routes

@pytest.fixture(autouse=True)
def reset_cache():
    main_routes._inr_per_usd_cache = None
    main_routes._inr_per_usd_cache_time = 0
