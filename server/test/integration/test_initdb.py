from src.app.core.appinit.init_db import ensure_database_initialized
from test.conftest import app as app_test

with app_test.app_context() as ctx:
    ensure_database_initialized(app_test)
