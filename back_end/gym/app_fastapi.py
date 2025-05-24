# Archivo: back_end/gym/app_fastapi.py
import os
import sys
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

# ---- NUEVO: CONFIGURACIÓN DEL PYTHON PATH ----
# Añadir el directorio raíz al Python path para poder importar fitness_agent
print("Current Directory:", os.getcwd())
print("Initial Python Path:", sys.path)

# Intentar múltiples posibles localizaciones
possible_paths = [
    "/app",                # Directorio raíz del contenedor
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")), # Subir dos niveles
]

for path in possible_paths:
    if os.path.exists(path):
        if path not in sys.path:
            sys.path.insert(0, path)
            print(f"Added {path} to Python path")

print("Updated Python Path:", sys.path)

# --- Importaciones Corregidas ---
try:
    # Usar importación relativa (. significa desde el mismo directorio gym)
    from .middlewares import AuthenticationMiddleware
    from .services.fitbit_scheduler import start_scheduler
except ImportError as e:
    # Log crítico si falla importación esencial
    logging.critical(f"Error crítico importando módulos locales: {e}", exc_info=True)
    sys.exit(f"Error importando módulos locales: {e}")

# Cargar variables de entorno
load_dotenv()

# --- Configuración de Logging (Nivel DEBUG) ---
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s [%(levelname)s] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
# Configurar logging para librerías externas
logging.getLogger('uvicorn').setLevel(logging.INFO)
logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
logging.getLogger('fastapi').setLevel(logging.INFO)
logging.getLogger('watchfiles').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Definir contexto de vida
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = None
    try:
        scheduler = start_scheduler()
        if scheduler: logger.info("✅ Fitbit scheduler iniciado correctamente")
    except NameError:
        logger.error("Fitbit scheduler no pudo iniciarse porque start_scheduler no está definido (Import Error?)")
    except Exception as e:
        logger.error(f"💥 Error iniciando Fitbit scheduler: {str(e)}", exc_info=True)

    yield

    if scheduler and getattr(scheduler, 'running', False):
        try:
            scheduler.shutdown()
            logger.info("🛑 Fitbit scheduler detenido.")
        except Exception as e:
            logger.error(f"💥 Error deteniendo Fitbit scheduler: {str(e)}")

# Inicializar FastAPI
app = FastAPI(lifespan=lifespan)

# Configurar CORS - MEJORADA
cors_origins_str = os.getenv('CORS_ORIGINS', 'http://localhost,http://localhost:3000,http://localhost:5050')
cors_origins = [origin.strip() for origin in cors_origins_str.split(',') if origin.strip()]

# Añadir comodín en desarrollo si es necesario
if os.getenv('ENV', 'development') == 'development':
    if '*' not in cors_origins:
        cors_origins.append('*')
        logger.info("Añadido comodín '*' a CORS para desarrollo")

logger.info("--- 🌍 Configuración CORS 🌍 ---")
logger.info(f"Entorno: {os.getenv('ENV', 'development')}")
logger.info(f"Raw CORS_ORIGINS string from env: '{cors_origins_str}'")
logger.info(f"Parsed origins list for CORSMiddleware: {cors_origins}")
logger.info("---------------------------------")

# En app_fastapi.py - Reemplaza la configuración CORS actual
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # O usa tu lista cors_origins si prefieres ser más restrictivo
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)
# Middleware de sesiones
secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    logger.warning("SECRET_KEY no definida en .env. Usando valor temporal (inseguro!).")
    secret_key = os.urandom(24).hex() #
app.add_middleware(SessionMiddleware, secret_key=secret_key)

# Middleware de autenticación (DESPUÉS de CORS y Session)
try:
    app.add_middleware(AuthenticationMiddleware)
except NameError:
     logger.critical("💥 AuthenticationMiddleware no definido (Import Error?) - ¡LA AUTENTICACIÓN NO FUNCIONARÁ!")

# Importar routers (usando importaciones relativas)
try:
    # Routers existentes
    from .routes import auth as auth_routes
    from .routes import chatbot as chatbot_routes  # Usaremos esta versión actualizada
    from .routes import dashboard as dashboard_routes
    from .routes import main as main_routes
    from .routes import profile as profile_routes
    from .routes.fitbit import router as fitbit_router
    from .routes import routine as routine_routes
    from .routes import login_handler as login_routes # Asegúrate que esta importación es correcta
    from .routes.internal import router as internal_router
    from .routes.nutrition import router as nutrition_router

    logger.info("Incluyendo routers...")
    app.include_router(login_routes.router) # <--- DESCOMENTADO
    app.include_router(main_routes.router)
    app.include_router(routine_routes.router)
    app.include_router(dashboard_routes.router)
    app.include_router(profile_routes.router)
    app.include_router(fitbit_router)
    app.include_router(chatbot_routes.router)  # Este contiene el nuevo código para fitness_agent
    app.include_router(auth_routes.router)
    app.include_router(internal_router)

    # NUEVO: Incluir el router combinado de nutrición
    app.include_router(nutrition_router)
    
    logger.info("✅ Routers incluidos.")
except ImportError as e:
    logger.critical(f"💥 Error Crítico importando routers (relativa): {e}", exc_info=True)
    sys.exit(f"Error importando routers: {e}")

@app.get("/fitbit-callback")
async def fitbit_callback_direct(request: Request):
    """Endpoint para manejar callback de OAuth de Fitbit y redirigir al handler correcto"""
    logger.info(f"Recibido callback directo de Fitbit. Redireccionando a /api/fitbit/callback")
    # Forwarding to the proper callback handler with all query parameters
    redirect_url = f"/api/fitbit/callback?{request.query_params}"
    return RedirectResponse(url=redirect_url, status_code=307)

# Servir archivos estáticos del frontend
frontend_build_dir = os.getenv('FRONTEND_BUILD_DIR', '../front_end/build')
if os.path.exists(frontend_build_dir):
    logger.info(f"🖥️ Sirviendo archivos estáticos desde: {frontend_build_dir}")
    app.mount("/static", StaticFiles(directory=f"{frontend_build_dir}/static"), name="static")
    
    # Ruta para manejar otras rutas de frontend (SPA)
    @app.get("/{rest_of_path:path}")
    async def serve_spa(request: Request, rest_of_path: str):
        # Ignorar rutas de API y archivos estáticos ya montados
        if rest_of_path.startswith("api/") or rest_of_path.startswith("static/") or rest_of_path.startswith("docs") or rest_of_path.startswith("openapi.json"):
            # No servir rutas de API, docs, o static desde esta función
            # Para /docs y /openapi.json, FastAPI los maneja si están habilitados.
            # Si se produce un 404 aquí para /docs, asegúrate que no está deshabilitado en la config de FastAPI.
            raise HTTPException(status_code=404, detail="Not found")
        
        index_path = os.path.join(frontend_build_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        else:
            logger.warning(f"No se encontró el archivo index.html en {frontend_build_dir}")
            raise HTTPException(status_code=404, detail="Frontend no encontrado") 
else:
    logger.warning(f"El directorio del frontend '{frontend_build_dir}' no existe. No se servirán archivos estáticos del frontend.")


# Punto de entrada principal (si se ejecuta directamente, aunque con uvicorn usualmente no se llega aquí)
if __name__ == '__main__':
    import uvicorn
    # Esto es para ejecución directa. Para producción/desarrollo con `uvicorn main:app --reload`,
    # esta parte no se ejecuta necesariamente a menos que llames `python app_fastapi.py`.
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))