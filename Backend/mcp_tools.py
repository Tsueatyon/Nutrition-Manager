from mcp.server.fastmcp import FastMCP
import json
import traceback
from datetime import date
from decimal import Decimal
from flask_jwt_extended import get_jwt_identity
from database import db
from sqlalchemy import text

mcp = FastMCP(name="nutrition-coach")

@mcp.tool()
def get_user_profile(username: str = None) -> str:
    if not username:
        username = get_jwt_identity()
    if not username:
        return json.dumps({"error": "not authenticated"})

    try:
        sql = text("""
            SELECT username, age, sex, height_cm, weight_kg, activity_level, goal 
            FROM users 
            WHERE username = :username
        """)
        
        result = db.session.execute(sql, {"username": username}).fetchone()
        
        if not result:
            return json.dumps({"error": "user not found"})
        
        return json.dumps({
            "username": result.username,
            "age": result.age,
            "sex": result.sex,
            "height_cm": float(result.height_cm) if result.height_cm else 0.0,
            "weight_kg": float(result.weight_kg) if result.weight_kg else 0.0,
            "activity_level": result.activity_level,
            "goal": result.goal
        })
    except Exception as e:
        traceback.print_exc()
        return json.dumps({"error": f"Failed to get profile: {str(e)}"})


@mcp.tool()
def get_today_nutrition(username: str = None) -> str:
    if not username:
        username = get_jwt_identity()
    if not username:
        return json.dumps({"error": "not authenticated"})

    try:
        today = date.today()
        
        user_sql = text("SELECT id FROM users WHERE username = :username")
        user_result = db.session.execute(user_sql, {"username": username}).fetchone()
        if not user_result:
            return json.dumps({"error": "user not found"})
        
        user_id = user_result.id
        intake_sql = text("""
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
              AND ui.intake_date = :today
        """)
        
        intake_rows = db.session.execute(intake_sql, {"user_id": user_id, "today": today}).fetchall()
        if not intake_rows:
            return json.dumps({"date": str(today), "calories": 0, "protein": 0, "carbs": 0, "fat": 0})
        
        total = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
        for row in intake_rows:
            quantity = float(row.quantity) if isinstance(row.quantity, Decimal) else row.quantity
            calories = float(row.calories) if isinstance(row.calories, Decimal) else row.calories
            protein = float(row.protein) if isinstance(row.protein, Decimal) else row.protein
            carbs = float(row.carbs) if isinstance(row.carbs, Decimal) else row.carbs
            fat = float(row.fat) if isinstance(row.fat, Decimal) else row.fat
            
            factor = quantity / 100.0
            total["calories"] += calories * factor
            total["protein"] += protein * factor
            total["carbs"] += carbs * factor
            total["fat"] += fat * factor
        
        total = {k: round(v, 1) for k, v in total.items()}
        
        return json.dumps({
            "date": str(today),
            "calories": total["calories"],
            "protein": total["protein"],
            "carbs": total["carbs"],
            "fat": total["fat"]
        })
    except Exception as e:
        traceback.print_exc()
        return json.dumps({"error": f"Failed to get nutrition: {str(e)}"})


@mcp.tool()
def calculate_daily_needs(sex: str = "male", weight_kg: float = None, height_cm: float = None,
                         age: int = None, activity_level: str = "moderate", goal: str = "maintain") -> str:
    if not all([weight_kg, height_cm, age]):
        return json.dumps({"error": "missing required parameters: weight_kg, height_cm, age"})

    if sex.lower() not in ("male", "female"):
        return json.dumps({"error": "sex must be 'male' or 'female'"})

    if activity_level not in ["sedentary", "light", "moderate", "active", "extra"]:
        return json.dumps({"error": "invalid activity_level"})
    
    if goal not in ["cut", "maintain", "bulk"]:
        return json.dumps({"error": "invalid goal. Must be 'cut', 'maintain', or 'bulk'"})

    if sex.lower() == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    factors = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "extra": 1.9}
    tdee = bmr * factors[activity_level]
    
    # Adjust TDEE based on goal
    goal_adjustments = {
        "cut": -0.20,      # 20% deficit for weight loss
        "maintain": 0.0,   # No adjustment for maintenance
        "bulk": 0.20       # 20% surplus for weight gain
    }
    goal_multiplier = 1.0 + goal_adjustments.get(goal, 0.0)
    adjusted_tdee = tdee * goal_multiplier

    protein = round(1.6 * weight_kg)
    fat = round((adjusted_tdee * 0.25) / 9)
    carbs = round((adjusted_tdee - (protein * 4 + fat * 9)) / 4)

    return json.dumps({
        "calories": round(adjusted_tdee),
        "protein_g": protein,
        "fat_g": fat,
        "carbs_g": carbs,
        "bmr": round(bmr),
        "tdee": round(tdee),
        "activity_multiplier": factors[activity_level],
        "goal": goal,
        "goal_adjustment": f"{goal_adjustments[goal]*100:.0f}%"
    })


@mcp.tool()
def get_user_daily_needs(username: str = None) -> str:
    if not username:
        username = get_jwt_identity()
    if not username:
        return json.dumps({"error": "not authenticated"})

    try:
        profile_result = get_user_profile(username)
        profile = json.loads(profile_result)
        if "error" in profile:
            return profile_result
        
        age_years = profile["age"]
        sex = profile["sex"].lower()
        weight_kg = float(profile["weight_kg"])
        height_cm = float(profile["height_cm"])
        activity_level = profile["activity_level"]
        goal = profile.get("goal", "maintain")
        
        if not all([weight_kg, height_cm, age_years]):
            return json.dumps({"error": "missing required profile data: weight_kg, height_cm, age"})
        if sex not in ("male", "female"):
            return json.dumps({"error": f"invalid sex value: {sex}"})
        if activity_level not in ["sedentary", "light", "moderate", "active", "extra"]:
            return json.dumps({"error": f"invalid activity_level: {activity_level}"})
        
        if sex == "male":
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age_years + 5
        else:
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age_years - 161
        
        factors = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "extra": 1.9}
        tdee = bmr * factors[activity_level]
        
        # Adjust TDEE based on goal
        goal_adjustments = {
            "cut": -0.20,      # 20% deficit for weight loss
            "maintain": 0.0,   # No adjustment for maintenance
            "bulk": 0.20       # 20% surplus for weight gain
        }
        goal_multiplier = 1.0 + goal_adjustments.get(goal, 0.0)
        adjusted_tdee = tdee * goal_multiplier
        
        protein = round(1.6 * weight_kg)
        fat = round((adjusted_tdee * 0.25) / 9)
        carbs = round((adjusted_tdee - (protein * 4 + fat * 9)) / 4)
        
        return json.dumps({
            "calories": round(adjusted_tdee),
            "protein_g": protein,
            "fat_g": fat,
            "carbs_g": carbs,
            "bmr": round(bmr),
            "tdee": round(tdee),
            "activity_multiplier": factors[activity_level],
            "goal": goal,
            "goal_adjustment": f"{goal_adjustments[goal]*100:.0f}%",
            "profile": {
                "age_years": age_years,
                "sex": sex,
                "weight_kg": weight_kg,
                "height_cm": height_cm,
                "activity_level": activity_level,
                "goal": goal
            }
        })
    except Exception as e:
        traceback.print_exc()
        return json.dumps({"error": f"Failed to get daily needs: {str(e)}"})

__all__ = ['mcp', 'get_user_profile', 'get_today_nutrition', 'calculate_daily_needs', 'get_user_daily_needs']