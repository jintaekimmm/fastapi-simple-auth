from app.factory import create_app
from internal.logging import configure_logger

# Logging Settings
configure_logger()

# Create FastAPI
app = create_app()