"""
Unit tests for functions.py
"""
import pytest
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from werkzeug.security import generate_password_hash

# Import functions to test
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions import (
    response,
    register_user,
    login_user,
    get_my_profile,
    profile_edit,
    insert_log,
    update_log,
    retrieve_log,
    delete_log,
    get_daily_nutrition,
    dv_summation,
    get_daily_needs,
    get_7_day_history,
    search_food_in_usda
)


@pytest.fixture
def app():
    """Create a Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def app_context(app):
    """Create Flask application context"""
    with app.app_context():
        yield app


@pytest.fixture
def mock_request():
    """Create a mock Flask request"""
    request = Mock()
    return request


@pytest.fixture
def mock_db():
    """Mock database session"""
    with patch('functions.db') as mock_db:
        mock_db.session = Mock()
        yield mock_db


@pytest.fixture
def mock_query():
    """Mock query function"""
    with patch('functions.query') as mock_query:
        yield mock_query


@pytest.fixture
def mock_execute():
    """Mock execute function"""
    with patch('functions.execute') as mock_execute:
        yield mock_execute


@pytest.fixture
def mock_jwt_identity():
    """Mock JWT identity"""
    with patch('functions.get_jwt_identity') as mock_jwt:
        yield mock_jwt


class TestResponse:
    """Test response helper function"""
    
    def test_response_with_data(self, app_context):
        """Test response function with data"""
        result = response(200, "Success", {"key": "value"})
        assert result.status_code == 200
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 200
        assert data['message'] == "Success"
        assert data['data'] == {"key": "value"}
    
    def test_response_without_data(self, app_context):
        """Test response function without data"""
        result = response(400, "Error")
        assert result.status_code == 200  # response always returns 200
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 400
        assert data['message'] == "Error"
        assert data['data'] == {}
    
    def test_response_with_date(self, app_context):
        """Test response function with date object"""
        test_date = date.today()
        result = response(200, "Success", {"date": test_date})
        data = json.loads(result.get_data(as_text=True))
        assert data['data']['date'] == test_date.isoformat()


class TestRegisterUser:
    """Test register_user function"""
    
    def test_register_user_success(self, app_context, mock_request, mock_query, mock_execute):
        """Test successful user registration"""
        mock_request.get_json.return_value = {
            'username': 'testuser',
            'password': 'testpass',
            'age': 25,
            'sex': 'male',
            'height': 175,
            'weight': 70,
            'activity_level': 'moderate',
            'goal': 'maintain'
        }
        mock_query.return_value = []  # No existing user
        # Create a dict-like object for the row
        mock_row = {'id': 1, 'username': 'testuser'}
        mock_execute.return_value = Mock(fetchone=Mock(return_value=mock_row))
        
        with patch('functions.create_access_token') as mock_token:
            mock_token.return_value = 'test_token'
            result = register_user(mock_request)
            data = json.loads(result.get_data(as_text=True))
            assert data['code'] == 200
            assert 'token' in data['data']
            assert data['data']['user']['username'] == 'testuser'
    
    def test_register_user_missing_fields(self, app_context, mock_request):
        """Test registration with missing fields"""
        mock_request.get_json.return_value = {'username': 'testuser'}
        result = register_user(mock_request)
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 400
    
    def test_register_user_duplicate_username(self, app_context, mock_request, mock_query):
        """Test registration with duplicate username"""
        mock_request.get_json.return_value = {
            'username': 'testuser',
            'password': 'testpass',
            'age': 25,
            'sex': 'male',
            'height': 175,
            'weight': 70,
            'activity_level': 'moderate',
            'goal': 'maintain'
        }
        mock_query.return_value = [{'id': 1}]  # Existing user
        result = register_user(mock_request)
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 400
        assert 'already exists' in data['message'].lower()
    
    def test_register_user_invalid_age(self, app_context, mock_request, mock_query):
        """Test registration with invalid age"""
        mock_request.get_json.return_value = {
            'username': 'testuser',
            'password': 'testpass',
            'age': 'invalid',
            'sex': 'male',
            'height': 175,
            'weight': 70,
            'activity_level': 'moderate',
            'goal': 'maintain'
        }
        mock_query.return_value = []
        result = register_user(mock_request)
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 400


class TestLoginUser:
    """Test login_user function"""
    
    def test_login_user_success(self, app_context, mock_request, mock_query):
        """Test successful login"""
        password = 'testpass'
        password_hash = generate_password_hash(password)
        mock_request.get_json.return_value = {
            'username': 'testuser',
            'password': password
        }
        mock_query.return_value = [{
            'id': 1,
            'username': 'testuser',
            'password_hash': password_hash
        }]
        
        with patch('functions.create_access_token') as mock_token:
            mock_token.return_value = 'test_token'
            result = login_user(mock_request)
            data = json.loads(result.get_data(as_text=True))
            assert data['code'] == 200
            assert 'token' in data['data']
            assert data['data']['user']['username'] == 'testuser'
    
    def test_login_user_missing_credentials(self, app_context, mock_request):
        """Test login with missing credentials"""
        mock_request.get_json.return_value = {}
        result = login_user(mock_request)
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 400
    
    def test_login_user_invalid_username(self, app_context, mock_request, mock_query):
        """Test login with invalid username"""
        mock_request.get_json.return_value = {
            'username': 'nonexistent',
            'password': 'testpass'
        }
        mock_query.return_value = []  # User not found
        result = login_user(mock_request)
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 400
    
    def test_login_user_invalid_password(self, app_context, mock_request, mock_query):
        """Test login with invalid password"""
        password_hash = generate_password_hash('correctpass')
        mock_request.get_json.return_value = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        mock_query.return_value = [{
            'id': 1,
            'username': 'testuser',
            'password_hash': password_hash
        }]
        result = login_user(mock_request)
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 400


class TestGetMyProfile:
    """Test get_my_profile function"""
    
    def test_get_my_profile_success(self, app_context, mock_jwt_identity, mock_query):
        """Test successful profile retrieval"""
        mock_jwt_identity.return_value = 'testuser'
        mock_query.return_value = [{
            'username': 'testuser',
            'age': 25,
            'sex': 'male',
            'height_cm': 175,
            'weight_kg': 70,
            'activity_level': 'moderate',
            'goal': 'maintain'
        }]
        
        result = get_my_profile()
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 200
        assert data['data']['username'] == 'testuser'
    
    def test_get_my_profile_no_auth(self, app_context, mock_jwt_identity):
        """Test profile retrieval without authentication"""
        mock_jwt_identity.return_value = None
        result = get_my_profile()
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 400


class TestProfileEdit:
    """Test profile_edit function"""
    
    def test_profile_edit_success(self, app_context, mock_request, mock_jwt_identity, mock_execute):
        """Test successful profile update"""
        mock_jwt_identity.return_value = 'testuser'
        mock_request.get_json.return_value = {
            'age': 26,
            'weight_kg': 72
        }
        mock_execute.return_value = Mock(rowcount=1)
        
        result = profile_edit(mock_request)
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 200
        assert 'successfully' in data['message'].lower()
    
    def test_profile_edit_no_data(self, app_context, mock_request, mock_jwt_identity):
        """Test profile update with no data"""
        mock_jwt_identity.return_value = 'testuser'
        mock_request.get_json.return_value = None
        result = profile_edit(mock_request)
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 400
    
    def test_profile_edit_invalid_field(self, app_context, mock_request, mock_jwt_identity):
        """Test profile update with invalid field"""
        mock_jwt_identity.return_value = 'testuser'
        mock_request.get_json.return_value = {
            'invalid_field': 'value'
        }
        result = profile_edit(mock_request)
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 400
    
    def test_profile_edit_no_fields(self, app_context, mock_request, mock_jwt_identity):
        """Test profile update with no valid fields"""
        mock_jwt_identity.return_value = 'testuser'
        mock_request.get_json.return_value = {}
        result = profile_edit(mock_request)
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 400
    
    def test_profile_edit_invalid_age(self, app_context, mock_request, mock_jwt_identity):
        """Test profile update with invalid age"""
        mock_jwt_identity.return_value = 'testuser'
        mock_request.get_json.return_value = {
            'age': 'not_a_number'
        }
        result = profile_edit(mock_request)
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 400


class TestGetDailyNeeds:
    """Test get_daily_needs function"""
    
    def test_get_daily_needs_male(self, app_context, mock_jwt_identity, mock_query):
        """Test daily needs calculation for male"""
        mock_jwt_identity.return_value = 'testuser'
        mock_query.return_value = [{
            'username': 'testuser',
            'age': 30,
            'sex': 'male',
            'height_cm': 180,
            'weight_kg': 75,
            'activity_level': 'moderate',
            'goal': 'maintain'
        }]
        
        result = get_daily_needs()
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 200
        assert 'calories' in data['data']
        assert 'protein_g' in data['data']
        assert 'carbs_g' in data['data']
        assert 'fat_g' in data['data']
        assert data['data']['calories'] > 0
    
    def test_get_daily_needs_female(self, app_context, mock_jwt_identity, mock_query):
        """Test daily needs calculation for female"""
        mock_jwt_identity.return_value = 'testuser'
        mock_query.return_value = [{
            'username': 'testuser',
            'age': 25,
            'sex': 'female',
            'height_cm': 165,
            'weight_kg': 60,
            'activity_level': 'light',
            'goal': 'lose'
        }]
        
        result = get_daily_needs()
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 200
        assert data['data']['calories'] > 0
    
    def test_get_daily_needs_user_not_found(self, app_context, mock_jwt_identity, mock_query):
        """Test daily needs with user not found"""
        mock_jwt_identity.return_value = 'testuser'
        mock_query.return_value = []
        result = get_daily_needs()
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 400


class TestGetDailyNutrition:
    """Test get_daily_nutrition function"""
    
    def test_get_daily_nutrition_success(self, mock_jwt_identity, mock_query):
        """Test successful daily nutrition retrieval"""
        mock_jwt_identity.return_value = 'testuser'
        mock_query.return_value = [{'id': 1}]
        
        with patch('functions.fetch_intake_rows') as mock_fetch:
            mock_fetch.return_value = [
                {
                    'quantity': 100.0,
                    'calories': 200.0,
                    'protein': 10.0,
                    'carbs': 30.0,
                    'fat': 5.0
                },
                {
                    'quantity': 50.0,
                    'calories': 150.0,
                    'protein': 5.0,
                    'carbs': 20.0,
                    'fat': 3.0
                }
            ]
            
            result = get_daily_nutrition(date.today())
            assert result is not None
            assert result['calories'] > 0
            assert result['protein'] > 0
            assert result['carbs'] > 0
            assert result['fat'] > 0
    
    def test_get_daily_nutrition_no_data(self, mock_jwt_identity, mock_query):
        """Test daily nutrition with no intake data"""
        mock_jwt_identity.return_value = 'testuser'
        # query is called once to get user_id
        mock_query.return_value = [{'id': 1}]
        
        with patch('functions.fetch_intake_rows') as mock_fetch, \
             patch('redis_client.cache_set') as mock_cache_set, \
             patch('redis_client.cache_get') as mock_cache_get:
            mock_cache_get.return_value = None  # No cache
            mock_fetch.return_value = []  # No intake rows
            result = get_daily_nutrition(date.today())
            assert result is None
    
    def test_get_daily_nutrition_user_not_found(self, app_context, mock_jwt_identity, mock_query):
        """Test daily nutrition with user not found"""
        mock_jwt_identity.return_value = 'testuser'
        mock_query.return_value = []  # User not found
        
        # The function tries to import redis_client, catches ImportError if it fails
        # We'll patch the import to simulate redis not being available
        import builtins
        original_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if name == 'redis_client':
                raise ImportError("No module named 'redis_client'")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            result = get_daily_nutrition(date.today())
            # Returns response object when user not found
            data = json.loads(result.get_data(as_text=True))
            assert data['code'] == 400
            assert 'not found' in data['message'].lower()


class TestDvSummation:
    """Test dv_summation function"""
    
    def test_dv_summation_with_data(self, app_context, mock_jwt_identity):
        """Test dv_summation with nutrition data"""
        mock_jwt_identity.return_value = 'testuser'
        
        with patch('functions.get_daily_nutrition') as mock_nutrition:
            mock_nutrition.return_value = {
                'calories': 2000.0,
                'protein': 100.0,
                'carbs': 250.0,
                'fat': 65.0
            }
            result = dv_summation()
            data = json.loads(result.get_data(as_text=True))
            assert data['code'] == 200
            assert data['data']['calories'] == 2000.0
    
    def test_dv_summation_no_data(self, app_context, mock_jwt_identity):
        """Test dv_summation with no nutrition data"""
        mock_jwt_identity.return_value = 'testuser'
        
        with patch('functions.get_daily_nutrition') as mock_nutrition:
            mock_nutrition.return_value = None
            result = dv_summation()
            data = json.loads(result.get_data(as_text=True))
            assert data['code'] == 200
            assert data['data']['calories'] == 0


class TestRetrieveLog:
    """Test retrieve_log function"""
    
    def test_retrieve_log_success(self, app_context, mock_jwt_identity, mock_query):
        """Test successful log retrieval"""
        mock_jwt_identity.return_value = 'testuser'
        # query is called twice: once for user_id, once for logs
        mock_query.side_effect = [
            [{'id': 1}],  # User ID query
            [{
                'id': 1,
                'food_name': 'Apple',
                'quantity': 100,
                'intake_date': date.today()
            }]  # Logs query
        ]
        
        with patch('redis_client.cache_get') as mock_cache_get, \
             patch('redis_client.cache_set') as mock_cache_set:
            mock_cache_get.return_value = None  # No cache
            result = retrieve_log()
            data = json.loads(result.get_data(as_text=True))
            assert data['code'] == 200
            assert len(data['data']) > 0
    
    def test_retrieve_log_with_date_filter(self, app_context, mock_jwt_identity, mock_query):
        """Test log retrieval with date filter"""
        mock_jwt_identity.return_value = 'testuser'
        # query is called twice: once for user_id, once for logs
        mock_query.side_effect = [
            [{'id': 1}],  # User ID query
            []  # Logs query (empty)
        ]
        
        with patch('redis_client.cache_get') as mock_cache_get, \
             patch('redis_client.cache_set') as mock_cache_set:
            mock_cache_get.return_value = None  # No cache
            result = retrieve_log(date.today())
            data = json.loads(result.get_data(as_text=True))
            assert data['code'] == 200
            assert data['data'] == []  # Empty list


class TestInsertLog:
    """Test insert_log function"""
    
    def test_insert_log_success(self, app_context, mock_request, mock_jwt_identity, mock_query, mock_execute):
        """Test successful log insertion"""
        mock_jwt_identity.return_value = 'testuser'
        mock_request.get_json.return_value = {
            'food_name': 'Apple',
            'quantity': 100,
            'intake_date': '2024-01-01',
            'meal_type': 'breakfast'
        }
        # query is called multiple times: user_id, food lookup, then food name lookup
        mock_query.side_effect = [
            [{'id': 1}],  # User ID query
            [{'id': 1, 'name': 'Apple', 'calories': 52, 'protein': 0.3, 'carbs': 14, 'fat': 0.2, 'serving_unit': 'g'}],  # Food lookup
            [{'name': 'Apple'}]  # Food name lookup after insert
        ]
        mock_row = {
            'id': 1,
            'food_id': 1,
            'quantity': 100,
            'intake_date': date(2024, 1, 1),
            'meal_type': 'breakfast',
            'created_at': datetime.now()
        }
        mock_execute.return_value = Mock(fetchone=Mock(return_value=mock_row))
        
        with patch('redis_client.invalidate_nutrition_cache'):
            result = insert_log(mock_request)
            data = json.loads(result.get_data(as_text=True))
            assert data['code'] == 200
    
    def test_insert_log_missing_fields(self, app_context, mock_request, mock_jwt_identity):
        """Test log insertion with missing fields"""
        mock_jwt_identity.return_value = 'testuser'
        mock_request.get_json.return_value = {'food_name': 'Apple'}
        result = insert_log(mock_request)
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 400


class TestUpdateLog:
    """Test update_log function"""
    
    def test_update_log_success(self, app_context, mock_request, mock_jwt_identity, mock_query, mock_execute):
        """Test successful log update"""
        mock_jwt_identity.return_value = 'testuser'
        mock_request.get_json.return_value = {
            'id': 1,
            'quantity': 150
        }
        # query is called multiple times: user_id, then food name lookup
        mock_query.side_effect = [
            [{'id': 1}],  # User ID query
            [{'name': 'Apple'}]  # Food name query (after update)
        ]
        # Create a dict-like object for the row
        mock_row = {
            'id': 1,
            'food_id': 1,
            'quantity': 150,
            'intake_date': date.today(),
            'meal_type': 'breakfast',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        mock_execute.return_value = Mock(
            fetchone=Mock(return_value=mock_row),
            rowcount=1
        )
        
        with patch('redis_client.invalidate_nutrition_cache'):
            result = update_log(mock_request)
            data = json.loads(result.get_data(as_text=True))
            assert data['code'] == 200
    
    def test_update_log_missing_id(self, app_context, mock_request, mock_jwt_identity):
        """Test log update without ID"""
        mock_jwt_identity.return_value = 'testuser'
        mock_request.get_json.return_value = {'quantity': 150}
        result = update_log(mock_request)
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 400


class TestDeleteLog:
    """Test delete_log function"""
    
    def test_delete_log_success(self, app_context, mock_request, mock_jwt_identity, mock_query, mock_execute):
        """Test successful log deletion"""
        mock_jwt_identity.return_value = 'testuser'
        mock_request.get_json.return_value = {'id': 1}
        mock_query.return_value = [{'id': 1}]
        mock_execute.return_value = Mock(fetchone=Mock(return_value={
            'id': 1,
            'intake_date': date.today(),
            'created_at': datetime.now()
        }))
        
        with patch('redis_client.invalidate_nutrition_cache'):
            result = delete_log(mock_request)
            data = json.loads(result.get_data(as_text=True))
            assert data['code'] == 200
    
    def test_delete_log_missing_id(self, app_context, mock_request, mock_jwt_identity):
        """Test log deletion without ID"""
        mock_jwt_identity.return_value = 'testuser'
        mock_request.get_json.return_value = {}
        result = delete_log(mock_request)
        data = json.loads(result.get_data(as_text=True))
        assert data['code'] == 400


class TestGet7DayHistory:
    """Test get_7_day_history function"""
    
    def test_get_7_day_history_success(self, app_context, mock_jwt_identity, mock_query):
        """Test successful 7-day history retrieval"""
        mock_jwt_identity.return_value = 'testuser'
        mock_query.side_effect = [
            [{'id': 1}],  # User ID query
            [{  # Profile query
                'username': 'testuser',
                'age': 30,
                'sex': 'male',
                'height_cm': 180,
                'weight_kg': 75,
                'activity_level': 'moderate',
                'goal': 'maintain'
            }]
        ]
        
        with patch('functions.get_daily_nutrition') as mock_nutrition, \
             patch('redis_client.cache_get') as mock_cache_get, \
             patch('redis_client.cache_set') as mock_cache_set:
            mock_cache_get.return_value = None  # No cache
            mock_nutrition.return_value = {
                'calories': 2000,
                'protein': 100,
                'carbs': 250,
                'fat': 65
            }
            result = get_7_day_history()
            data = json.loads(result.get_data(as_text=True))
            assert data['code'] == 200
            assert 'history' in data['data']
            assert len(data['data']['history']) == 7
            assert 'daily_needs' in data['data']


class TestSearchFoodInUsda:
    """Test search_food_in_usda function"""
    
    @patch('functions.requests.post')
    @patch('functions.config')
    def test_search_food_success(self, mock_config, mock_post):
        """Test successful food search"""
        mock_config.get.return_value = 'test_api_key'
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'foods': [{
                'description': 'Apple',
                'foodNutrients': [
                    {'nutrientId': 1008, 'value': 52, 'unitName': 'KCAL'},
                    {'nutrientId': 1003, 'value': 0.3, 'unitName': 'G'},
                    {'nutrientId': 1005, 'value': 14, 'unitName': 'G'},
                    {'nutrientId': 1004, 'value': 0.2, 'unitName': 'G'}
                ]
            }]
        }
        mock_post.return_value = mock_response
        
        result = search_food_in_usda('Apple')
        assert result is not None
        assert result['name'] == 'Apple'
        assert 'calories' in result
    
    @patch('functions.requests.post')
    @patch('functions.config')
    def test_search_food_not_found(self, mock_config, mock_post):
        """Test food search with no results"""
        mock_config.get.return_value = 'test_api_key'
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'foods': []}
        mock_post.return_value = mock_response
        
        result = search_food_in_usda('NonexistentFood')
        assert result is None
    
    @patch('functions.requests.post')
    @patch('functions.config')
    def test_search_food_api_error(self, mock_config, mock_post):
        """Test food search with API error"""
        mock_config.get.return_value = 'test_api_key'
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        result = search_food_in_usda('Apple')
        assert result is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

