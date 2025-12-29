import sys
import os
import configparser
from datetime import timedelta, datetime
from flask import Flask, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, get_jwt_identity, verify_jwt_in_request, jwt_required
from gevent import pywsgi
from database import db
from functions import (
    register_user, login_user, response, get_my_profile, profile_edit,
    update_log, insert_log, retrieve_log, delete_log, dv_summation,
    get_30_day_history, get_daily_needs
)
from chat_handler import handle_chat_message, set_config_path

config_file = sys.argv[1] if len(sys.argv) > 1 else 'config.prd.ini'
config = configparser.ConfigParser()
if os.path.exists(config_file):
    config.read(config_file, encoding='utf-8')
set_config_path(config_file)

app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = True

cors_origins_env = os.getenv('CORS_ORIGINS', '')
if cors_origins_env:
    # Check if wildcard pattern is used (allow all)
    if '*' in cors_origins_env or cors_origins_env.lower() == 'all':
        CORS(app, supports_credentials=True)
    else:
        # Support both comma and semicolon separators (semicolon for PowerShell compatibility)
        separators = ',' if ',' in cors_origins_env else ';'
        allowed_origins = [origin.strip() for origin in cors_origins_env.split(separators) if origin.strip()]
        CORS(app, supports_credentials=True, origins=allowed_origins)
else:
    # Default: allow all origins (was working before)
CORS(app, supports_credentials=True)

jwt = JWTManager(app)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY') or (
    config.get('server', 'JWT_SECRET_KEY') if config.has_section('server') else 'change-me-in-production'
)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=5)

database_url = os.getenv('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    if database_url.startswith('postgresql://') and '+psycopg2' not in database_url:
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
elif config.has_section('postgres'):
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://%s:%s@%s:%d/%s' % (
    config.get('postgres', 'user'),
    config.get('postgres', 'password'),
    config.get('postgres', 'host'),
    config.getint('postgres', 'port'),
    config.get('postgres', 'database')
)
else:
    raise ValueError("DATABASE_URL environment variable or postgres config section required")

app.config['SQLALCHEMY_ECHO'] = config.getboolean('postgres', 'debug') if config.has_section('postgres') else False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args': {'connect_timeout': 10}}
db.init_app(app)

@app.after_request
def after_request(resp):
    resp.headers['Content-Type'] = 'application/json'
    return resp

@app.before_request
def before_request():
    public_endpoints = ['/login', '/register']
    if request.path in public_endpoints:
        return None
    try:
        verify_jwt_in_request()
        if not get_jwt_identity():
            return response(401, 'Invalid token - please re-login')
    except Exception:
        return response(401, 'Authentication required - please re-login')
    return None

@app.errorhandler(404)
def not_found(error):
    return response(404, 'Endpoint not found')

@app.errorhandler(405)
def method_not_allowed(error):
    return response(405, 'Method not allowed')

@app.errorhandler(500)
def internal_error(error):
    return response(500, 'Internal server error')

@app.errorhandler(Exception)
def handle_exception(e):
    return response(500, f'Server error: {str(e)}')


@app.route('/my_profile', methods=['GET'])
@jwt_required()
def my_profile():
    return get_my_profile()

@app.route('/register', methods=['POST'])
def register():
    return register_user(request)

@app.route('/login', methods=['POST'])
def login():
    return login_user(request)

@app.route("/profile_edit", methods=["POST"])
@jwt_required()
def profile_edit_endpoint():
    return profile_edit(request)

@app.route("/insert_log", methods=["POST"])
@jwt_required()
def add_log():
    return insert_log(request)

@app.route("/update_log", methods=["POST"])
@jwt_required()
def modify_log():
    return update_log(request)

@app.route('/retrieve_log', methods=['GET'])
@jwt_required()
def get_log():
    date_str = request.args.get('date')
    time_constraint = None
    if date_str:
        try:
            time_constraint = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return response(400, 'Invalid date format. Use YYYY-MM-DD')
    return retrieve_log(time_constraint)

@app.route('/delete_log', methods=['POST'])
@jwt_required()
def remove_log():
    return delete_log(request)

@app.route('/dv_summation', methods=['GET'])
@jwt_required()
def daily_summary():
    return dv_summation()

@app.route('/daily_needs', methods=['GET'])
@jwt_required()
def daily_needs():
    return get_daily_needs()

@app.route('/history_30days', methods=['GET'])
@jwt_required()
def history_30days():
    return get_30_day_history()

@app.route('/api/chat', methods=['POST'])
@jwt_required()
def chat():
    try:
        return handle_chat_message(request)
    except Exception as e:
        return response(500, f'Chat endpoint error: {str(e)}')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', config.getint('server', 'port') if config.has_section('server') else 8080))
    server = pywsgi.WSGIServer(("0.0.0.0", port), app)
    server.serve_forever()