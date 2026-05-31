with open("tests/test_main_routes.py", "r") as f:
    content = f.read()

import_statement = "from app.routes.main_routes import get_inr_per_usd, FALLBACK_INR_PER_USD"
new_import = "from app.routes.main_routes import get_inr_per_usd, FALLBACK_INR_PER_USD\nimport app.routes.main_routes\n\n@pytest.fixture(autouse=True)\ndef reset_cache():\n    app.routes.main_routes._inr_per_usd_cache = None\n    app.routes.main_routes._inr_per_usd_cache_time = 0"

content = content.replace(import_statement, new_import)

with open("tests/test_main_routes.py", "w") as f:
    f.write(content)
