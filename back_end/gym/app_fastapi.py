# Archivo: back_end/gym/app_fastapi.py
import os
import sys
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

# --- Importaciones Corregidas ---
try:
    # Usar importación relativa (. significa desde el mismo directorio gym)
    from .middlewares import AuthenticationMiddleware
    from .services.fitbit_scheduler import start_scheduler # Asumiendo que está en services/
except ImportError as e:
    # Log crítico si falla importación esencial
    logging.critical(f"Error crítico importando módulos locales: {e}", exc_info=True)
    sys.exit(f"Error importando módulos locales: {e}")

# --- Fin Importaciones Corregidas ---


# Cargar variables de entorno
load_dotenv()

# --- Configuración de Logging (Nivel DEBUG) ---
logging.basicConfig(
    level=logging.DEBUG, # <-- ASEGÚRATE QUE SEA DEBUG
    format='%(asctime)s - %(name)s [%(levelname)s] - %(message)s', # Añadido levelname
    handlers=[
        logging.StreamHandler(sys.stdout), # Log a consola stdout
        # logging.FileHandler('app.log', encoding='utf-8') # Opcional: guardar en archivo
    ]
)
# Configurar logging para librerías externas si son muy ruidosas
logging.getLogger('uvicorn').setLevel(logging.INFO)
logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
logging.getLogger('fastapi').setLevel(logging.INFO)
logging.getLogger('watchfiles').setLevel(logging.WARNING)

logger = logging.getLogger(__name__) # Logger para este archivo

# Deshabilitar LangSmith (si no lo usas o según configuración)
# ... (código LangSmith existente) ...

# Definir contexto de vida
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = None
    try:
        # Asegúrate que start_scheduler está correctamente importado arriba
        scheduler = start_scheduler()
        if scheduler: logger.info("✅ Fitbit scheduler iniciado correctamente")
    except NameError:
        logger.error("Fitbit scheduler no pudo iniciarse porque start_scheduler no está definido (Import Error?)")
    except Exception as e:
        logger.error(f"💥 Error iniciando Fitbit scheduler: {str(e)}", exc_info=True)

    yield

    if scheduler and getattr(scheduler, 'running', False): # Chequeo más seguro
        try:
            scheduler.shutdown()
            logger.info("🛑 Fitbit scheduler detenido.")
        except Exception as e:
            logger.error(f"💥 Error deteniendo Fitbit scheduler: {str(e)}")

# Inicializar FastAPI
app = FastAPI(lifespan=lifespan)

# Configurar CORS
cors_origins_str = os.getenv('CORS_ORIGINS', 'http://localhost,http://localhost:3000') # Valor por defecto más seguro
cors_origins = [origin.strip() for origin in cors_origins_str.split(',') if origin.strip()]

logger.info("--- 🌍 Configuración CORS 🌍 ---")
logger.info(f"Raw CORS_ORIGINS string from env: '{cors_origins_str}'")
logger.info(f"Parsed origins list for CORSMiddleware: {cors_origins}")
logger.info("---------------------------------")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de sesiones
secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    logger.warning("SECRET_KEY no definida en .env. Usando valor temporal (inseguro!).")
    secret_key = os.urandom(24).hex()
app.add_middleware(SessionMiddleware, secret_key=secret_key)

# Middleware de autenticación (DESPUÉS de CORS y Session)
# Asegúrate que AuthenticationMiddleware está correctamente importado arriba
try:
    app.add_middleware(AuthenticationMiddleware)
except NameError:
     logger.critical("💥 AuthenticationMiddleware no definido (Import Error?) - ¡LA AUTENTICACIÓN NO FUNCIONARÁ!")
     # Considera detener la app si el middleware es esencial
     # sys.exit("Middleware de autenticación no pudo ser añadido.")


# Importar routers (usando importaciones relativas)
# --- Importaciones Corregidas ---
try:
    # Usar importación relativa (. significa desde el mismo directorio gym)
    from .routes import auth as auth_routes
    from .routes import chatbot as chatbot_routes
    from .routes import dashboard as dashboard_routes
    from .routes import main as main_routes
    from .routes import profile as profile_routes
    from .routes import routine as routine_routes

    logger.info("Incluyendo routers...")
    app.include_router(main_routes.router)
    app.include_router(routine_routes.router)
    app.include_router(dashboard_routes.router)
    app.include_router(profile_routes.router)
    app.include_router(chatbot_routes.router)
    app.include_router(auth_routes.router)
    logger.info("✅ Routers incluidos.")
# --- Fin Importaciones Corregidas ---
except ImportError as e:
    # Loguea el error específico de importación del router
    logger.critical(f"💥 Error Crítico importando routers (relativa): {e}", exc_info=True)
    sys.exit(f"Error importando routers: {e}")


# Punto de entrada principal
if __name__ == '__main__':
    import uvicorn
    logger.info("Iniciando servidor Uvicorn directamente...")
    # Nota: Las opciones de SSL se pasan aquí si ejecutas directamente,
    # pero en Docker se suelen manejar en el start.sh o comando de uvicorn
    uvicorn.run(
        "app_fastapi:app",
        host="0.0.0.0",
        port=5050,
        reload=True, # Cambia a False en producción
        log_level="debug",
        # Añade aquí las opciones SSL si necesitas ejecutar con HTTPS directamente
        # ssl_keyfile=os.getenv("SSL_KEY_PATH_IN_CONTAINER"),
        # ssl_certfile=os.getenv("SSL_CERT_PATH_IN_CONTAINER")
    )