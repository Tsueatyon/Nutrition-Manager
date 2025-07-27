
import os
from datetime import datetime, date

from flask import Flask, request, make_response, jsonify
from flask_cors import CORS
import json,sys,configparser
from flask_sqlalchemy import SQLAlchemy
from gevent import pywsgi
from flask_jwt_extended import get_jwt_identity, create_access_token, verify_jwt_in_request, JWTManager
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
config = configparser.ConfigParser()
config.read(sys.argv[1], encoding='utf-8')

#initialize frame
app = Flask(__name__)
CORS(app, supports_credentials=True)
jwt = JWTManager(app)
db = SQLAlchemy()

# PostgreSQL connection string
# postgresql+psycopg2://username:password@host:port/database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://%s:%s@%s:%d/%s' % (
    config.get('postgres', 'user'),
    config.get('postgres', 'password'),
    config.get('postgres', 'host'),
    config.getint('postgres', 'port'),
    config.get('postgres', 'database')
)

app.config['SQLALCHEMY_ECHO'] = config.getboolean('postgres', 'debug')
app.config['JWT_SECRET_KEY'] = "2ba1756a7b793952f60a3e33c56f3beb5a0e53c258bbc8d223d95abf1d0875b4"
db.init_app(app)

@app.after_request
def after_request(resp):
    resp.headers['Content-Type'] = 'application/json'
    return resp


@app.before_request
def before_request():
    public_endpoints = ['/login','/register']
    if request.path in public_endpoints:
        return None
    try:
        verify_jwt_in_request()
        current_user = get_jwt_identity()
        if not current_user:
            return response(999, 'Invalid token - please re-login')
    except Exception as e:
        return response(999, 'Please re-login - token missing or invalid')
    return None

def searchdata(list,id):
    for i in range(len(list)):
        if list[i]['id'] == id:
            return list[i]
    return None
def editdata(list,id,data):
    for i in range(len(list)):
        if list[i]['id'] == id:
            list[i] = data
            return
    return

def deletedata(list,id):
    for i in range(len(list)):
        if list[i]['id'] == id:
            del list[i]
            return
    return
#search in sql
def query(sql,param=None):
    res=db.session.execute(sql,param)
    data=[dict(zip(result.keys(),result)) for result in res]
    return data

#write in sql
def execute(sql,param=None):
    result=db.session.execute(sql,param)
    db.session.commit()
    return result
@app.route('/login',methods=['POST'] )
def login():
    param=json.loads(request.data)
    if 'username' not in param:
        return response(1000,'Enter Username')
    if 'password' not in param:
        return response(1001,'Enter Password')
    sql="SELECT * FROM users WHERE username=:username"
    ret=query(sql,{'username':param['username']})
    if len(ret)>0 and ret[0]['password'] == param['password']:
        access_token = create_access_token(identity = param['username'])
        return response(0, 'Login successful', {'access_token': access_token})
    else:
        return response(1, 'Invalid credentials', [])
@app.route('/logout',methods=['POST'] )
def logout():
    resp=response(0,'logged out')
    resp.delete_cookie('id')
    return resp

def response(code,message,data:any=None):
    res={'code':code,'message':message,'data':{}}
    if data is not None:
        if hasattr(data,'__dict__'):
            res['data']=data.__dict__
        else:
            res['data']=data
    return make_response(json.dumps(res,sort_keys=True,ensure_ascii=False),200)
@app.route('/my_profile',methods=['GET'] )
def get_my_profile():
    user_list = []
    username = get_jwt_identity()
    sql = 'select * from users WHERE username=:username'
    rets = query(sql, {'username': username})
    if len(rets) > 0:
        for idx, row in enumerate(rets):
            user_list.append({'username': row['username'],'height':float(row['height']),'weight':float(row['weight']),'age':float(row['age'])})
    return response(0,'ok',user_list)

@app.route('/profile_delete',methods=['POST'] )
def profile_delete():
    data = request.get_json()
    if not data:
        return response(1, 'Missing or invalid JSON')
    username = data.get('username')
    if not username:
        return response(1, 'Username is required')
    sql = 'DELETE FROM users WHERE username=:username'
    execute(sql, {'username': username})
    return response(0, 'Deleted')

@app.route('/register',methods=['POST'] )
def profile_add():
    field=[]
    vals={}

    data=request.get_json()
    if not data:
        return response(1,'index error')
    if 'username' not in data:
        return response(1,'enter username')
    if 'password' not in data:
        return response(1,'enter password')
    field.append('username')
    vals['username']=data['username']
    field.append('password')
    vals['password']=data['password']

    usql = 'select * from users where username=:username'
    rets= query(usql,{'username':data['username']})
    if len(rets)>0:
        return response(1,'duplicate username, please enter new username')
    if 'height' in data:
        field.append('height')
        vals['height']=float(data['height'])
    if 'weight' in data:
        field.append('weight')
        vals['weight']=float(data['weight'])
    if 'age' in data:
        field.append('age')
        vals['age']=float(data['age'])

    sql='insert into users (%s) values (:%s)' % (', '.join(field),',:'.join(field))
    execute(sql,vals)
    return response(0,'profile added')
@app.route('/profile_edit',methods=['PUT'] )
def profile_edit():
    param = request.get_json()
    if not param:
        return response(1, 'index error')

    username = get_jwt_identity()
    field = []
    vals = {}
    for key in ['height', 'weight', 'age']:
        if key in param:
            try:
                vals[key] = float(param[key]) if key == 'weight' else int(param[key])
                field.append(key)
            except (ValueError, TypeError):
                return response(1, f'{key} must be a valid number')
    if not field:
        return response(1, 'No fields to update')
    vals['username'] = username
    sets = [f"{f} = :{f}" for f in field]
    sql = f"UPDATE users SET {', '.join(sets)} WHERE username = :username"
    execute(sql, vals)
    return response(0, 'profile updated')

@app.route('/nutrition_add',methods=['PUT'] )
def nutrition_update():
    param = request.get_json(force=True)
    username= get_jwt_identity()
    required_entries = ['food','nutrients','quantity']
    for entry in required_entries:
        if entry not in param:
            return response(1,f'Missing entry{entry}')
    if 'timestamp' not in param:
        time =  datetime.now().isoformat()
    else:
        time = param['timestamp']
    quantity = float(param['quantity'])
    nutrient = param['nutrients']
    try:
        sql = 'select nutrition_log from users where username=:username'
        user_result = query(sql, {'username': username})
        if not user_result:
            return response(1, 'user not found')

        nutrition_data = user_result[0]['nutrition_log'] if user_result[0]['nutrition_log'] else []

        # Convert dict to list if needed
        if isinstance(nutrition_data, dict):
            current_log = [nutrition_data]
        elif isinstance(nutrition_data, list):
            current_log = nutrition_data
        else:
            current_log = []

        new_entry = {
            'food': param['food'],
            'quantity': quantity,
            'nutrients': {k:(v*(quantity/100))for k, v in nutrient.items()},
            'timestamp': time
        }
        current_log.append(new_entry)
        update_sql = '''
            UPDATE users 
            SET nutrition_log = :nutrition_log 
            WHERE username = :username
        '''
        execute(update_sql, { 'nutrition_log': json.dumps(current_log), 'username': username})
        return response(0, 'Nutrition data updated successfully')
    except Exception as e:
        db.session.rollback()
        return response(1,'Failed to insert nutrition data',str(e))

@app.route('/retrieve_log',methods=['GET'] )
def retrieve_log():
    username = get_jwt_identity()
    if not username:
        return response(999, 'authentication required')
    sql = 'select nutrition_log from users where username=:username'
    res = query(sql, {'username':username})
    return response(0,"log_returned",res[0]['nutrition_log'])


# prerequisite: Login and pass timestamp and food name
@app.route('/delete_log',methods=['POST'] )
def delete_log():
    username = get_jwt_identity()
    if not username:
        return response(999, 'authentication required')
    sql = 'select nutrition_log from users where username=:username'
    res = query(sql, {'username':username})
    if not res:
        return response(1, 'user not found')
    param = json.loads(request.data)
    target_timestamp = param['timestamp']
    target_food = param['food']
    log_data = res[0]['nutrition_log'] if res and res[0]['nutrition_log'] else []
    if isinstance(log_data, str):
        log_data = json.loads(log_data)
    for i,data in enumerate(log_data):
        if data.get("timestamp") == target_timestamp and data.get("food") == target_food:
            deleted_log = data
            log_data.remove(data)
            sql = 'UPDATE users SET nutrition_log = :nutrition_log WHERE username = :username'
            execute(sql, {'username':username, 'nutrition_log':json.dumps(log_data)})
            return response(0,'delete nutrition data successfully',deleted_log)
    return response(1,'data not found on this timestamp')
'''
def calculate_dv_percentages(totals):
    """Calculate Daily Value percentages based on FDA guidelines"""
    # FDA Daily Values (based on 2000 calorie diet)
    daily_values = {
        'calories': 2000,
        'protein': 50,  # grams
        'carbs': 300,  # grams
        'fat': 65,  # grams
        'fiber': 25,  # grams
        'sugar': 50,  # grams (added sugars)
        'sodium': 2300,  # mg
        'vitamins': {
            'vitamin_c': 90,  # mg
            'vitamin_d': 20,  # mcg
            'vitamin_a': 900,  # mcg
            'vitamin_e': 15,  # mg
            'vitamin_k': 120,  # mcg
            'thiamine': 1.2,  # mg
            'riboflavin': 1.3,  # mg
            'niacin': 16,  # mg
            'vitamin_b6': 1.7,  # mg
            'folate': 400,  # mcg
            'vitamin_b12': 2.4,  # mcg
        },
        'minerals': {
            'calcium': 1300,  # mg
            'iron': 18,  # mg
            'magnesium': 420,  # mg
            'phosphorus': 1250,  # mg
            'potassium': 4700,  # mg
            'zinc': 11,  # mg
        }
    }

    percentages = {}

    # Calculate macronutrient percentages
    macronutrients = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']
    for nutrient in macronutrients:
        if nutrient in daily_values and nutrient in totals:
            if daily_values[nutrient] > 0:
                percentages[nutrient] = round((totals[nutrient] / daily_values[nutrient]) * 100, 1)
            else:
                percentages[nutrient] = 0

    # Calculate vitamin percentages
    percentages['vitamins'] = {}
    if 'vitamins' in totals:
        for vitamin, amount in totals['vitamins'].items():
            if vitamin in daily_values['vitamins']:
                if daily_values['vitamins'][vitamin] > 0:
                    percentages['vitamins'][vitamin] = round((amount / daily_values['vitamins'][vitamin]) * 100, 1)
                else:
                    percentages['vitamins'][vitamin] = 0

    # Calculate mineral percentages
    percentages['minerals'] = {}
    if 'minerals' in totals:
        for mineral, amount in totals['minerals'].items():
            if mineral in daily_values['minerals']:
                if daily_values['minerals'][mineral] > 0:
                    percentages['minerals'][mineral] = round((amount / daily_values['minerals'][mineral]) * 100, 1)
                else:
                    percentages['minerals'][mineral] = 0
    return percentages
'''

@app.route('/dv_summation', methods=['GET'])
def dv_summation():
    username = get_jwt_identity()
    sql = 'SELECT nutrition_log FROM users WHERE username = :username'
    user_result = query(sql, {'username': username})
    log = user_result[0]['nutrition_log']
    if not log:
        return response(1, 'log not found')
    if isinstance(log, str):
        log = json.loads(log)
    today = date.today().isoformat()
    daily_totals = {
        'calories': 0,
        'protein': 0,
        'carbs': 0,
        'fat': 0,
        'fiber': 0,
        'sugar': 0,
        'sodium': 0,
        'vitamins': {},
        'minerals': {},
        'total_entries': 0,
        'foods_consumed': []
    }

    for entry in log:
        entry_date = entry.get('timestamp', '').split('T')[0]
        if entry_date == today:
            daily_totals['total_entries'] += 1
            timestamp = entry.get('timestamp', '')
            time_part = timestamp.split('T')[1] if 'T' in timestamp else ''
            daily_totals['foods_consumed'].append({
                'food': entry.get('food'),
                'quantity': entry.get('quantity'),
                'time': time_part
            })

            nutrients = entry.get('nutrients', {})
            macronutrients = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']
            for nutrient in macronutrients:
                daily_totals[nutrient] += nutrients.get(nutrient, 0)

            vitamins = nutrients.get('vitamins', {})
            for vitamin, amount in vitamins.items():
                daily_totals['vitamins'][vitamin] = daily_totals['vitamins'].get(vitamin, 0) + amount

            minerals = nutrients.get('minerals', {})
            for mineral, amount in minerals.items():
                daily_totals['minerals'][mineral] = daily_totals['minerals'].get(mineral, 0) + amount
    return response(0,"Here is today's nutrient in take", daily_totals)

if __name__ == '__main__':
    #app.run(port=9000)
    server=pywsgi.WSGIServer(("0.0.0.0", config.getint('server','port')), app)
    server.serve_forever()