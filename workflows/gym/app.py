import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
from flask import Flask
from routes.main import main_bp
from routes.routine import routine_bp
from routes.dashboard import dashboard_bp
from routes.profile import profile_bp  # Importar el nuevo blueprint de perfil
load_dotenv()# Inicializar la aplicación Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'c7d69e294b3259ca49542de11ab0eacf8738291fd87a62a3')
# Registrar blueprints
app.register_blueprint(main_bp)
app.register_blueprint(routine_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(profile_bp)  # Registrar el nuevo blueprint

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)