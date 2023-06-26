from app.factory import create_app
from core.logging import configure_logger


# Logging
configure_logger()

# Create FastAPI App
app = create_app()
