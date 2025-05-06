# back_end/gym/routes/__init__.py
import logging

# Configure logger
logger = logging.getLogger(__name__)

try:
    from .profile import router as profile_router
    from .auth import router as auth_router
    # Other imports...
except ImportError as e:
    logger.error(f"❌ Error importing router: {e}")