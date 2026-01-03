import json
import requests
from datetime import date, datetime, timedelta
from decimal import Decimal
from flask import Request, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity
from sqlalchemy import text
from database import db
from config import USDA_API_KEY


def response(code: int, message: str, data: any = None):
    res = {'code': code, 'message': message, 'data': {}}
    if data is not None:
        res['data'] = data.__dict__ if hasattr(data, '__dict__') else data

    def json_serial(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        raise TypeError(f"Type {type(obj)} not serializable")

    return make_response(
        json.dumps(res, sort_keys=True, ensure_ascii=False, default=json_serial),
        200
    )

def query(sql: str, param=None):
    res = db.session.execute(text(sql), param)
    data = [dict(zip(result.keys(), result)) for result in res]
    return data

def execute(sql: str, param=None):
    try:
        result = db.session.execute(text(sql), param)
        db.session.commit()
        return result
    except Exception as e:
        db.session.rollback()
        raise e

def register_user(request: Request):
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    age = data.get('age')
    sex = data.get('sex')
    height = data.get('height')
    weight = data.get('weight')
    activity_level = data.get('activity_level')
    goal = data.get('goal')

    try:
        if not all([username, password, age, sex, height, weight, activity_level, goal]):
            return response(400, 'All fields are required')
        
        try:
            age = int(age)
            if not 1 <= age <= 150:
                return response(400, 'Age must be between 1 and 150')
        except (ValueError, TypeError):
            return response(400, 'Age must be a valid integer')

        existing_user = query(
            'SELECT id FROM users WHERE username = :username',
            {'username': username}
        )

        if existing_user:
            return response(400, 'Username already exists')

        password_hash = generate_password_hash(password)

        sql = """
            INSERT INTO users (username, password_hash, age, sex, height_cm, weight_kg, activity_level, goal)
            VALUES (:username, :password_hash, :age, :sex, :height, :weight, :activity_level, :goal)
            RETURNING id, username
        """
        params = {
            'username': username,
            'password_hash': password_hash,
            'age': age,
            'sex': sex,
            'height': height,
            'weight': weight,
            'activity_level': activity_level,
            'goal': goal
        }

        result = execute(sql, params)
        row = result.fetchone()
        if not row:
            return response(500, 'Failed to register user')

        access_token = create_access_token(
            identity=username,
            expires_delta=timedelta(hours=5)
        )

        return response(
            200,
            'User registered successfully',
            {
                'user': {'id': row['id'], 'username': username},
                'token': access_token
            }
        )

    except Exception as error:
        db.session.rollback()
        return response(500, f'Internal server error: {str(error)}')

def login_user(request: Request):
    credentials = request.get_json()
    username = credentials.get('username')
    password = credentials.get('password')

    try:
        if not username or not password:
            return response(400, 'Username and password are required')

        result = query(
            'SELECT id, username, password_hash FROM users WHERE username = :username',
            {'username': username}
        )

        if not result:
            return response(400, 'Invalid username or password')

        user = result[0]

        if not check_password_hash(user['password_hash'], password):
            return response(400, 'Invalid username or password')

        access_token = create_access_token(
            identity=username,
            expires_delta=timedelta(hours=5)
        )

        return response(
            200,
            'Login successful',
            {
                'user': {'id': user['id'], 'username': user['username']},
                'token': access_token
            }
        )

    except Exception as error:
        db.session.rollback()
        print('Login error:', error)
        return response(500, 'Internal server error')

def get_my_profile():
    username = get_jwt_identity()
    if not username:
        return response(400, "Authentication required")

    try:
        sql = """
            SELECT username, age, sex, height_cm, weight_kg, activity_level, goal
            FROM users WHERE username = :username
        """
        result = query(sql, {"username": username})
        return response(200, "Profile retrieved successfully", result[0])
    except Exception as e:
        db.session.rollback()
        print(f"Get profile error: {e}")
        return response(500, "Failed to retrieve profile")


def profile_edit(request: Request):
    current_username = get_jwt_identity()

    data = request.get_json()
    if not data:
        return response(400, 'Invalid JSON payload')

    allowed_fields = {'age', 'sex', 'height_cm', 'weight_kg', 'activity_level', 'goal'}

    updates = {}
    params = {'username': current_username}

    for key, value in data.items():
        if key not in allowed_fields:
            return response(400, f'Cannot update field: {key}')

        # Convert age to int if provided
        if key == 'age':
            try:
                value = int(value)
            except (ValueError, TypeError):
                return response(400, 'Age must be a valid integer')
        
        updates[key] = value
        params[key] = value
    
    if not updates:
        return response(400, 'No valid fields provided to update')

    set_clause = ', '.join(f"{col} = :{col}" for col in updates)
    sql = f"UPDATE users SET {set_clause} WHERE username = :username"

    try:
        result = execute(sql, params)

        if result.rowcount == 0:
            return response(400, 'User not found')

        return response(200, 'Profile updated successfully')

    except Exception as e:
        db.session.rollback()
        print('Profile edit error:', e)
        return response(500, 'Failed to update profile')


def search_food_in_usda(food_name: str):
    try:
        api_key = USDA_API_KEY
        search_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
        query_params = {
            "api_key": api_key
        }
        search_body = {
            "query": food_name,
            "pageSize": 5,
            "dataType": ["Survey (FNDDS)", "Foundation", "SR Legacy"]
        }

        search_response = requests.post(
            search_url, 
            params=query_params,
            json=search_body,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        if search_response.status_code != 200:
            print(f"USDA API error: {search_response.status_code}")
            return None

        search_data = search_response.json()

        if not search_data.get('foods') or len(search_data['foods']) == 0:
            return None

        # Try each food result until we find one with complete nutrition data
        for food_item in search_data['foods']:
            nutrients = {}
            for nutrient in food_item.get('foodNutrients', []):
                nutrient_name = nutrient.get('nutrientName', '').lower()
                nutrient_value = nutrient.get('value')
                if nutrient_value is None:
                    continue
                try:
                    nutrient_value = float(nutrient_value)
                except (ValueError, TypeError):
                    continue
                nutrient_unit = nutrient.get('unitName', '').lower()
                nutrient_id = nutrient.get('nutrientId')

                # Use nutrient IDs for more reliable matching (standard USDA IDs)
                # Energy: 1008 (kcal) or 1062 (kJ)
                # Protein: 1003
                # Carbohydrate: 1005
                # Fat: 1004
                if nutrient_id == 1008:  # Energy (kcal)
                    nutrients['calories'] = nutrient_value
                elif nutrient_id == 1062:  # Energy (kJ)
                    nutrients['calories'] = nutrient_value / 4.184
                elif nutrient_id == 1003:  # Protein
                    if nutrient_unit == 'g':
                        nutrients['protein'] = nutrient_value
                elif nutrient_id == 1005:  # Carbohydrate, by difference
                    if nutrient_unit == 'g':
                        nutrients['carbs'] = nutrient_value
                elif nutrient_id == 1004:  # Total lipid (fat)
                    if nutrient_unit == 'g':
                        nutrients['fat'] = nutrient_value
                else:
                    # Fallback to name-based matching if ID doesn't match
                    if not nutrients.get('calories'):
                        if 'energy' in nutrient_name:
                            if 'kcal' in nutrient_unit:
                                nutrients['calories'] = nutrient_value
                            elif 'kj' in nutrient_unit:
                                nutrients['calories'] = nutrient_value / 4.184
                    if not nutrients.get('protein'):
                        if ('protein' in nutrient_name or 'prot' in nutrient_name) and nutrient_unit == 'g':
                            nutrients['protein'] = nutrient_value
                    if not nutrients.get('carbs'):
                        if ('carbohydrate' in nutrient_name or 'carb' in nutrient_name or 'cho' in nutrient_name) and nutrient_unit == 'g':
                            nutrients['carbs'] = nutrient_value
                    if not nutrients.get('fat'):
                        if ('total lipid' in nutrient_name or 'fat, total' in nutrient_name or 'fat' == nutrient_name) and nutrient_unit == 'g':
                            nutrients['fat'] = nutrient_value

            # Use defaults of 0 for missing nutrients instead of failing
            calories = nutrients.get('calories', 0)
            protein = nutrients.get('protein', 0)
            carbs = nutrients.get('carbs', 0)
            fat = nutrients.get('fat', 0)

            # Accept if we have at least calories and one macro (more lenient requirement)
            if calories > 0 and (protein > 0 or carbs > 0 or fat > 0):
                return {
                    'name': food_item.get('description', food_name),
                    'calories': round(calories, 2),
                    'protein': round(protein, 2),
                    'carbs': round(carbs, 2),
                    'fat': round(fat, 2),
                    'serving_unit': 'g'
                }
        return None

    except requests.exceptions.RequestException as e:
        print(f"USDA API request error: {e}")
        return None
    except Exception as e:
        print(f"Error searching USDA: {e}")
        return None

def insert_log(request: Request):
    username = get_jwt_identity()
    data = request.get_json()

    if not data:
        return response(400, "Missing JSON payload")

    required_fields = {"food_name", "quantity", "intake_date"}
    if not required_fields.issubset(data):
        return response(400, "Missing required fields: food_name, quantity, intake_date")

    food_name = data.get("food_name")
    intake_date_str = data.get("intake_date")

    try:
        intake_date = date.fromisoformat(intake_date_str)
    except (ValueError, TypeError):
        return response(400, "intake_date must be a valid ISO date (YYYY-MM-DD)")

    if intake_date > date.today():
        return response(400, "Cannot log future intake dates")

    try:
        # Get user ID
        sql_user = "SELECT id FROM users WHERE username = :username"
        res = query(sql_user, {"username": username})
        if not res:
            return response(400, "User not found")
        user_id = res[0]["id"]

        try:
            quantity = float(data["quantity"])
            if quantity <= 0:
                return response(400, "Quantity must be positive")
        except (ValueError, TypeError):
            return response(400, "Quantity must be a number")

        food_check = query(
            "SELECT id, name, calories, protein, carbs, fat, serving_unit FROM food WHERE LOWER(name) = LOWER(:food_name)",
            {"food_name": food_name}
        )

        if food_check:
            food_id = food_check[0]["id"]
            food_serving_unit = food_check[0].get("serving_unit", "g")
        else:
            usda_food = search_food_in_usda(food_name)
            if not usda_food:
                return response(400, f"Food '{food_name}' not found in local database or USDA API")

            try:
                insert_food_sql = """
                    INSERT INTO food (name, calories, protein, carbs, fat, serving_unit)
                    VALUES (:name, :calories, :protein, :carbs, :fat, :serving_unit)
                    RETURNING id
                """
                food_result = execute(insert_food_sql, {
                    "name": usda_food['name'],
                    "calories": usda_food['calories'],
                    "protein": usda_food['protein'],
                    "carbs": usda_food['carbs'],
                    "fat": usda_food['fat'],
                    "serving_unit": usda_food['serving_unit']
                })
                food_row = food_result.fetchone()
                if not food_row:
                    return response(500, "Failed to insert food from USDA")
                food_id = food_row['id']
                food_serving_unit = usda_food['serving_unit']
            except Exception as e:
                db.session.rollback()
                return response(500, "Failed to insert food from USDA API")
        sql = """
            INSERT INTO user_intake 
                (user_id, food_id, quantity, intake_date, meal_type)
            VALUES 
                (:user_id, :food_id, :quantity, :intake_date, :meal_type)
            RETURNING id, user_id, food_id, quantity, intake_date, meal_type, created_at
        """

        params = {
            "user_id": user_id,
            "food_id": food_id,
            "quantity": quantity,
            "intake_date": intake_date,
            "meal_type": data.get("meal_type")
        }

        result = execute(sql, params)
        inserted_row = result.fetchone()

        if not inserted_row:
            return response(500, "Failed to insert intake entry")

        row_dict = dict(inserted_row)
        # Get date before converting to string for cache invalidation
        affected_date = row_dict.get("intake_date")
        if row_dict.get("intake_date"):
            row_dict["intake_date"] = row_dict["intake_date"].isoformat()
        if row_dict.get("created_at"):
            row_dict["created_at"] = row_dict["created_at"].isoformat()
        
        if row_dict.get("food_id"):
            food_query = query("SELECT name FROM food WHERE id = :food_id", {"food_id": row_dict["food_id"]})
            if food_query:
                row_dict["food_name"] = food_query[0]["name"]

        # Invalidate cache for the affected date
        try:
            from redis_client import invalidate_nutrition_cache
            if affected_date:
                invalidate_nutrition_cache(username, str(affected_date))
        except Exception as e:
            print(f"Cache invalidation error in insert_log: {e}")

        return response(200, "Intake entry created successfully", row_dict)

    except Exception as e:
        db.session.rollback()
        print("Insert log error:", e)
        return response(500, "Failed to create intake entry")


def update_log(request: Request):
    username = get_jwt_identity()
    data = request.get_json()

    if not data or "id" not in data:
        return response(400, "Missing intake entry ID")

    try:
        # Resolve user ID
        sql = "SELECT id FROM users WHERE username = :username"
        res = query(sql, {"username": username})
        if not res:
            return response(400, "User not found")

        user_id = res[0]["id"]
        intake_id = data["id"]
        food_id = None

        if "food_name" in data:
            food_name = data.get("food_name")
            food_check = query("SELECT id FROM food WHERE LOWER(name) = LOWER(:food_name)", {"food_name": food_name})
            
            if food_check:
                food_id = food_check[0]["id"]
            else:
                usda_food = search_food_in_usda(food_name)
                if not usda_food:
                    return response(400, f"Food '{food_name}' not found in local database or USDA API")
                
                try:
                    insert_food_sql = """
                        INSERT INTO food (name, calories, protein, carbs, fat, serving_unit)
                        VALUES (:name, :calories, :protein, :carbs, :fat, :serving_unit)
                        RETURNING id
                    """
                    food_result = execute(insert_food_sql, {
                        "name": usda_food['name'],
                        "calories": usda_food['calories'],
                        "protein": usda_food['protein'],
                        "carbs": usda_food['carbs'],
                        "fat": usda_food['fat'],
                        "serving_unit": usda_food['serving_unit']
                    })
                    food_row = food_result.fetchone()
                    if not food_row:
                        return response(500, "Failed to insert food from USDA")
                    food_id = food_row['id']
                except Exception as e:
                    db.session.rollback()
                    return response(500, "Failed to insert food from USDA API")

        allowed_fields = {"food_id", "quantity", "intake_date", "meal_type"}
        updates = {k: v for k, v in data.items() if k in allowed_fields}
        if food_id is not None:
            updates["food_id"] = food_id

        if not updates:
            return response(400, "No valid fields to update")

        if "intake_date" in updates:
            try:
                intake_date = date.fromisoformat(str(updates["intake_date"]))
                if intake_date > date.today():
                    return response(400, "Cannot log future intake dates")
                updates["intake_date"] = intake_date
            except (ValueError, TypeError):
                return response(400, "intake_date must be valid ISO date (YYYY-MM-DD)")
        
        if "quantity" in updates:
            try:
                quantity = float(updates["quantity"])
                if quantity <= 0:
                    return response(400, "Quantity must be positive")
                updates["quantity"] = quantity
            except (ValueError, TypeError):
                return response(400, "Quantity must be a number")

        set_clause = ", ".join(f"{k} = :{k}" for k in updates)

        sql = f"""
            UPDATE user_intake ui
            SET {set_clause},
                updated_at = NOW()
            WHERE ui.id = :intake_id
              AND ui.user_id = :user_id
            RETURNING 
                ui.id,
                ui.user_id,
                ui.food_id,
                ui.quantity,
                ui.intake_date,
                ui.meal_type,
                ui.created_at,
                ui.updated_at
        """

        updates["intake_id"] = intake_id
        updates["user_id"] = user_id
        result = execute(sql, updates)
        updated_row = result.fetchone()

        if not updated_row:
            return response(400, "Entry not found or unauthorized")

        result_dict = dict(updated_row)
        # Get date before converting to string for cache invalidation
        affected_date = result_dict.get("intake_date")
        if result_dict.get("intake_date"):
            result_dict["intake_date"] = result_dict["intake_date"].isoformat()
        if result_dict.get("created_at"):
            result_dict["created_at"] = result_dict["created_at"].isoformat()
        if result_dict.get("updated_at"):
            result_dict["updated_at"] = result_dict["updated_at"].isoformat()
        
        if result_dict.get("food_id"):
            food_query = query("SELECT name FROM food WHERE id = :food_id", {"food_id": result_dict["food_id"]})
            if food_query:
                result_dict["food_name"] = food_query[0]["name"]

        # Invalidate cache for the affected date (this also invalidates 7-day history cache)
        try:
            from redis_client import invalidate_nutrition_cache
            if affected_date:
                invalidate_nutrition_cache(username, str(affected_date))
        except Exception as e:
            print(f"Cache invalidation error in update_log: {e}")

        return response(200, "Intake entry updated successfully", result_dict)

    except Exception as e:
        db.session.rollback()
        print("Update log error:", e)
        return response(500, "Failed to update intake entry")


def retrieve_log(time_constraint: date = None):
    username = get_jwt_identity()

    try:
        # Try to get from cache first
        try:
            from redis_client import cache_get, cache_set, get_cache_key_for_logs
            date_filter = str(time_constraint) if time_constraint else "all"
            cache_key = get_cache_key_for_logs(username, date_filter)
            cached_data = cache_get(cache_key)
            if cached_data is not None:
                return response(200, "Logs retrieved successfully (cached)", cached_data)
        except ImportError:
            pass  # Redis not available, continue without cache
        
        sql = "SELECT id FROM users WHERE username = :username"
        res = query(sql, {"username": username})
        if not res:
            return response(400, "User not found")
        user_id = res[0]["id"]

        sql = """
            SELECT 
                ui.id,
                ui.user_id,
                ui.food_id,
                ui.quantity,
                ui.intake_date,
                ui.meal_type,
                ui.created_at,
                ui.updated_at,
                f.name AS food_name
            FROM user_intake ui
            LEFT JOIN food f ON ui.food_id = f.id
            WHERE ui.user_id = :user_id
        """
        params = {"user_id": user_id}

        if time_constraint:
            sql += " AND ui.intake_date <= :time_constraint"
            params["time_constraint"] = time_constraint

        sql += " ORDER BY ui.intake_date DESC, ui.created_at DESC"

        logs = query(sql, params)
        
        # Cache the result (24 hour TTL)
        try:
            from redis_client import cache_set, get_cache_key_for_logs
            date_filter = str(time_constraint) if time_constraint else "all"
            cache_key = get_cache_key_for_logs(username, date_filter)
            cache_set(cache_key, logs, ttl=86400)  # Cache for 24 hours
        except ImportError:
            pass
        
        return response(200, "Logs retrieved successfully", logs)

    except Exception as e:
        db.session.rollback()
        print("Retrieve log error:", e)
        return response(500, "Failed to retrieve logs")


def delete_log(request: Request):
    username = get_jwt_identity()
    data = request.get_json()

    if not data or "id" not in data:
        return response(400, "Missing intake entry ID")

    try:
        target_intake_id = data["id"]

        sql = "SELECT id FROM users WHERE username = :username"
        res = query(sql, {"username": username})

        if not res:
            return response(400, "User not found")

        user_id = res[0]["id"]
        sql = """
            DELETE FROM user_intake ui
            WHERE ui.id = :intake_id
              AND ui.user_id = :user_id
            RETURNING 
                ui.id,
                ui.user_id,
                ui.food_id,
                ui.quantity,
                ui.intake_date,
                ui.meal_type,
                ui.created_at,
                ui.updated_at
        """

        result = execute(sql, {"intake_id": target_intake_id, "user_id": user_id})
        deleted_row = result.fetchone()
        
        if not deleted_row:
            return response(400, "Entry not found or unauthorized")

        result_dict = dict(deleted_row)
        # Get date before converting to string for cache invalidation
        affected_date = result_dict.get("intake_date")
        if result_dict.get("intake_date"):
            result_dict["intake_date"] = result_dict["intake_date"].isoformat()
        if result_dict.get("created_at"):
            result_dict["created_at"] = result_dict["created_at"].isoformat()
        if result_dict.get("updated_at"):
            result_dict["updated_at"] = result_dict["updated_at"].isoformat()
        
        if result_dict.get("food_id"):
            food_query = query("SELECT name FROM food WHERE id = :food_id", {"food_id": result_dict["food_id"]})
            if food_query:
                result_dict["food_name"] = food_query[0]["name"]

        # Invalidate cache for the affected date
        try:
            from redis_client import invalidate_nutrition_cache
            if affected_date:
                invalidate_nutrition_cache(username, str(affected_date))
        except Exception as e:
            print(f"Cache invalidation error in delete_log: {e}")

        return response(200, "Intake entry deleted successfully", result_dict)

    except Exception as e:
        db.session.rollback()
        print("Delete log error:", e)
        return response(500, "Failed to delete intake entry")


def fetch_intake_rows(user_id: int, target_date: date):
    sql = """
        SELECT
            ui.food_id,
            ui.quantity,
            f.calories,
            f.protein,
            f.carbs,
            f.fat
        FROM user_intake ui
        JOIN food f ON ui.food_id = f.id
        WHERE ui.user_id = :user_id
          AND ui.intake_date = :target_date
    """
    return query(sql, {
        "user_id": user_id,
        "target_date": target_date
    })


def get_daily_nutrition(target_date: date = None):
    username = get_jwt_identity()
    if not target_date:
        target_date = date.today()

    try:
        # Try to get from cache first
        try:
            from redis_client import cache_get, cache_set, get_cache_key_for_daily_nutrition
            cache_key = get_cache_key_for_daily_nutrition(username, str(target_date))
            cached_data = cache_get(cache_key)
            if cached_data is not None:
                return cached_data
        except ImportError:
            pass  # Redis not available, continue without cache

        sql = "SELECT id FROM users WHERE username = :username"
        res = query(sql, {"username": username})

        if not res:
            return response(400, "User not found")

        user_id = res[0]["id"]
        intake_rows = fetch_intake_rows(user_id, target_date)

        if not intake_rows:
            # Cache None result as well (to avoid repeated DB queries)
            result = None
            try:
                from redis_client import cache_set, get_cache_key_for_daily_nutrition
                cache_key = get_cache_key_for_daily_nutrition(username, str(target_date))
                cache_set(cache_key, None, ttl=86400)  # Cache for 24 hours
            except ImportError:
                pass
            return result

        total = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}

        for row in intake_rows:
            quantity = float(row["quantity"]) if isinstance(row["quantity"], Decimal) else row["quantity"]
            calories = float(row["calories"]) if isinstance(row["calories"], Decimal) else row["calories"]
            protein = float(row["protein"]) if isinstance(row["protein"], Decimal) else row["protein"]
            carbs = float(row["carbs"]) if isinstance(row["carbs"], Decimal) else row["carbs"]
            fat = float(row["fat"]) if isinstance(row["fat"], Decimal) else row["fat"]

            factor = quantity / 100.0
            total["calories"] += calories * factor
            total["protein"] += protein * factor
            total["carbs"] += carbs * factor
            total["fat"] += fat * factor

        total = {k: round(v, 2) for k, v in total.items()}
        
        # Cache the result (24 hour TTL)
        try:
            from redis_client import cache_set, get_cache_key_for_daily_nutrition
            cache_key = get_cache_key_for_daily_nutrition(username, str(target_date))
            cache_set(cache_key, total, ttl=86400)  # Cache for 24 hours
        except ImportError:
            pass
        
        return total

    except Exception as e:
        db.session.rollback()
        print('Get daily nutrition error:', e)
        return None


def dv_summation():
    username = get_jwt_identity()

    try:
        nutrition = get_daily_nutrition(date.today())
        
        if nutrition is None:
            return response(200, "No intake today", {
                "date": str(date.today()),
                "calories": 0,
                "protein": 0,
                "carbs": 0,
                "fat": 0
            })

        return response(200, "Daily nutrition calculated successfully", {
            "date": str(date.today()),
            **nutrition
        })

    except Exception as e:
        db.session.rollback()
        print('Calculate dv nutrition error:', e)
        return response(500, 'Failed to calculate daily nutrition')


def get_daily_needs():
    username = get_jwt_identity()
    
    try:
        sql = """
            SELECT username, age, sex, height_cm, weight_kg, activity_level, goal
            FROM users WHERE username = :username
        """
        result = query(sql, {"username": username})
        if not result:
            return response(400, "User not found")
        
        profile = result[0]
        age_years = profile["age"]
        sex = profile["sex"].lower()
        weight_kg = float(profile["weight_kg"])
        height_cm = float(profile["height_cm"])
        activity_level = profile["activity_level"]
        
        # Validate data
        if not all([weight_kg, height_cm, age_years]):
            return response(400, "missing required profile data: weight_kg, height_cm, age")
        
        if sex not in ("male", "female"):
            return response(400, f"invalid sex value: {sex}")
        
        if activity_level not in ["sedentary", "light", "moderate", "active", "extra"]:
            return response(400, f"invalid activity_level: {activity_level}")
        
        if sex == "male":
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age_years + 5
        else:
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age_years - 161
        
        factors = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "extra": 1.9}
        tdee = bmr * factors[activity_level]
        protein = round(1.6 * weight_kg)
        fat = round((tdee * 0.25) / 9)
        carbs = round((tdee - (protein * 4 + fat * 9)) / 4)
        
        return response(200, "Daily needs calculated successfully", {
            "calories": round(tdee),
            "protein_g": protein,
            "fat_g": fat,
            "carbs_g": carbs,
            "bmr": round(bmr),
            "activity_multiplier": factors[activity_level]
        })
        
    except Exception as e:
        db.session.rollback()
        print('Get daily needs error:', e)
        return response(500, 'Failed to calculate daily needs')


def get_7_day_history():
    username = get_jwt_identity()
    
    try:
        # Try to get from cache first
        try:
            from redis_client import cache_get, cache_set, get_cache_key_for_7day_history
            cache_key = get_cache_key_for_7day_history(username)
            cached_data = cache_get(cache_key)
            if cached_data is not None:
                return response(200, "7-day history retrieved successfully (cached)", cached_data)
        except ImportError:
            pass  # Redis not available, continue without cache
        
        sql = "SELECT id FROM users WHERE username = :username"
        res = query(sql, {"username": username})
        
        if not res:
            return response(400, "User not found")
        
        user_id = res[0]["id"]
        today = date.today()
        history = []
        
        sql_profile = """
            SELECT username, age, sex, height_cm, weight_kg, activity_level, goal
            FROM users WHERE username = :username
        """
        profile_result = query(sql_profile, {"username": username})
        if not profile_result:
            return response(400, "User not found")
        
        profile = profile_result[0]
        age_years = profile["age"]
        sex = profile["sex"].lower()
        weight_kg = float(profile["weight_kg"])
        height_cm = float(profile["height_cm"])
        activity_level = profile["activity_level"]
        
        if sex == "male":
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age_years + 5
        else:
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age_years - 161
        
        factors = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "extra": 1.9}
        tdee = bmr * factors[activity_level]
        protein = round(1.6 * weight_kg)
        fat = round((tdee * 0.25) / 9)
        carbs = round((tdee - (protein * 4 + fat * 9)) / 4)
        
        daily_needs = {"calories": round(tdee), "protein_g": protein, "fat_g": fat, "carbs_g": carbs}
        
        for i in range(7):
            target_date = today - timedelta(days=i)
            nutrition = get_daily_nutrition(target_date)
            
            history.append({
                "date": str(target_date),
                "calories": nutrition.get("calories") if nutrition else None,
                "protein": nutrition.get("protein") if nutrition else None,
                "carbs": nutrition.get("carbs") if nutrition else None,
                "fat": nutrition.get("fat") if nutrition else None,
                "optimal": {
                    "calories": daily_needs.get("calories", 0),
                    "protein_g": daily_needs.get("protein_g", 0),
                    "carbs_g": daily_needs.get("carbs_g", 0),
                    "fat_g": daily_needs.get("fat_g", 0)
                }
            })
        
        result_data = {
            "history": history,
            "daily_needs": daily_needs
        }
        
        # Cache the result (24 hour TTL)
        try:
            from redis_client import cache_set, get_cache_key_for_7day_history
            cache_key = get_cache_key_for_7day_history(username)
            cache_set(cache_key, result_data, ttl=86400)  # Cache for 24 hours
        except ImportError:
            pass
        
        return response(200, "7-day history retrieved successfully", result_data)
        
    except Exception as e:
        db.session.rollback()
        print('Get 7-day history error:', e)
        return response(500, 'Failed to retrieve 7-day history')