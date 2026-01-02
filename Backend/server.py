import sys
import os
import json
import configparser
from datetime import timedelta, datetime
from flask import Flask, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, get_jwt_identity, verify_jwt_in_request, jwt_required
from gevent import pywsgi
from database import db
from functions import (
    register_user,
    login_user,
    response,
    get_my_profile,
    profile_edit,
    update_log,
    insert_log,
    retrieve_log,
    delete_log,
    dv_summation,
    get_7_day_history,
    get_daily_needs
)
from chat_handler import handle_chat_message, set_config_path

config_file = sys.argv[1]
config = configparser.ConfigParser()
config.read(config_file, encoding='utf-8')
set_config_path(config_file)

app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = True
CORS(app, supports_credentials=True)


jwt = JWTManager(app)
app.config['JWT_SECRET_KEY'] = config.get('server', 'JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=5)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://%s:%s@%s:%d/%s' % (
    config.get('postgres', 'user'),
    config.get('postgres', 'password'),
    config.get('postgres', 'host'),
    config.getint('postgres', 'port'),
    config.get('postgres', 'database')
)

app.config['SQLALCHEMY_ECHO'] = config.getboolean('postgres', 'debug')
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args': {'connect_timeout': 10}}
db.init_app(app)

# Initialize Redis connection on startup
try:
    from redis_client import get_redis_client
    get_redis_client()
except Exception as e:
    print(f"Redis initialization warning: {e}. Continuing without cache.")

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
    return response(404, f'Endpoint not found,{str(error)}')

@app.errorhandler(405)
def method_not_allowed(error):
    return response(405, f'Method not allowed,{str(error)}')

@app.errorhandler(500)
def internal_error(error):
    return response(500, f'Internal server error{str(error)}')

@app.errorhandler(Exception)
def handle_exception(e):
    return response(500, f'Server error: {str(e)}')

@app.route('/register', methods=['POST'])
def register():
    return register_user(request)

@app.route('/login', methods=['POST'])
def login():
    return login_user(request)
@app.route('/my_profile', methods=['GET'])
@jwt_required()
def my_profile():
    return get_my_profile()
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

@app.route('/history_7days', methods=['GET'])
@jwt_required()
def history_7days():
    return get_7_day_history()

@app.route('/api/chat', methods=['POST'])
@jwt_required()
def chat():
    try:
        return handle_chat_message(request)
    except Exception as e:
        return response(500, f'Chat endpoint error: {str(e)}')

@app.route('/api/chat/task/<task_id>', methods=['GET'])
@jwt_required()
def chat_task_status(task_id):
    """Check status of background LLM task."""
    try:
        try:
            from celery_app import celery_app
            from celery.result import AsyncResult
        except ImportError:
            return response(503, "Background jobs not available")
        
        task_result = AsyncResult(task_id, app=celery_app)
        
        if task_result.ready():
            if task_result.successful():
                result = task_result.result
                if isinstance(result, dict) and "error" in result:
                    return response(500, result["error"])
                return response(200, "Chat response generated", result)
            else:
                return response(500, f"Task failed: {str(task_result.info)}")
        else:
            return response(202, "Task still processing", {"status": "processing"})
    except Exception as e:
        return response(500, f'Task status error: {str(e)}')

@app.route('/api/chat/history', methods=['GET', 'POST', 'DELETE'])
@jwt_required()
def chat_history():
    """Get, save, or delete chat history from/to Redis."""
    try:
        try:
            from redis_client import cache_get, cache_set, cache_delete, get_cache_key_for_chat
        except ImportError:
            if request.method == 'GET':
                return response(200, "Chat history retrieved (Redis not available)", {
                    "history": []
                })
            return response(503, "Redis not available")
        
        username = get_jwt_identity()
        if not username:
            return response(401, "Authentication required")
        
        chat_key = get_cache_key_for_chat(username)
        
        if request.method == 'GET':
            history = cache_get(chat_key)
            return response(200, "Chat history retrieved", {
                "history": history if history else []
            })
        elif request.method == 'POST':
            data = request.get_json()
            if not data or 'history' not in data:
                return response(400, "Missing 'history' field")
            
            history = data.get('history', [])
            if not isinstance(history, list):
                return response(400, "History must be a list")
            
            cache_set(chat_key, history, ttl=86400 * 7)  # 7 days
            return response(200, "Chat history saved", {"history": history})
        else:  # DELETE
            cache_delete(chat_key)
            return response(200, "Chat history cleared", {"history": []})
            
    except Exception as e:
        return response(500, f'Chat history error: {str(e)}')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', config.getint('server', 'port') if config.has_section('server') else 8080))
    server = pywsgi.WSGIServer(("0.0.0.0", port), app)
    server.serve_forever()