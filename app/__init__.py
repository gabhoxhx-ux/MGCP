"""
Paquete de la aplicación Flask
"""

import os
from pathlib import Path
from flask import Flask, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

# Base directory (project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Crear carpeta database si no existe
DB_DIR = os.path.join(BASE_DIR, 'database')
os.makedirs(DB_DIR, exist_ok=True)

# Explicit template/static folders inside the package to avoid TemplateNotFound when
# running from different working directories
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
static_dir = os.path.join(os.path.dirname(__file__), 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# Use an absolute path for the SQLite DB file so the app can be started from any cwd
db_path = os.path.join(DB_DIR, 'mgcp.db')
# Convertir backslashes a forward slashes para SQLite
sqlite_url = f'sqlite:///{db_path}'.replace('\\', '/')

# Resolver DATABASE_URL si viene desde .env como ruta relativa
env_url = os.getenv('DATABASE_URL')
final_url = None
if env_url and env_url.startswith('sqlite:///'):
	# Extraer la parte de ruta después del prefijo
	path_part = env_url.replace('sqlite:///', '')
	# Detectar ruta absoluta en Windows (e.g., C:/...)
	is_windows_abs = len(path_part) >= 2 and path_part[1] == ':'
	if not os.path.isabs(path_part) and not is_windows_abs:
		abs_path = os.path.join(BASE_DIR, path_part)
	else:
		abs_path = path_part
	final_url = 'sqlite:///' + abs_path.replace('\\', '/')
else:
	final_url = env_url if env_url else sqlite_url

app.config['SQLALCHEMY_DATABASE_URI'] = final_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-2025')
app.config['ADMIN_USER'] = os.getenv('ADMIN_USER', 'admin')
app.config['ADMIN_PASS'] = os.getenv('ADMIN_PASS', 'admin123')

db = SQLAlchemy(app)

# Importar modelos y registrar rutas
from .models import Cliente, Propuesta, VersionPropuesta, RespuestaCliente, Notificacion, CostoIndirecto
from . import routes  # noqa: F401 - registra rutas en el app

# Utilidad: decorador simple para proteger rutas de administración
def login_required(view_func):
	def wrapper(*args, **kwargs):
		path = request.path
		# Permitir portal cliente y estáticos sin login
		if path.startswith('/cliente/') or path.startswith('/static/'):
			return view_func(*args, **kwargs)
		# Permitir login/logout públicos
		if path in ['/login', '/logout']:
			return view_func(*args, **kwargs)
		# Verificar sesión admin
		if session.get('admin_logged_in'):
			return view_func(*args, **kwargs)
		return redirect(url_for('login'))
	wrapper.__name__ = view_func.__name__
	return wrapper

# Seguridad básica: cabeceras HTTP (CSP/HSTS/Frame/Referrer)
@app.after_request
def set_security_headers(response):
	response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains'  # HSTS
	response.headers['X-Content-Type-Options'] = 'nosniff'
	response.headers['X-Frame-Options'] = 'SAMEORIGIN'
	response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
	response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"
	return response

__all__ = ['app', 'db', 'Cliente', 'Propuesta', 'VersionPropuesta', 'RespuestaCliente', 'Notificacion', 'CostoIndirecto']
