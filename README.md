# 🥗 Nutrition Manager

A full-stack nutrition tracking application that helps users monitor their daily food intake, calculate nutritional needs, and get personalized nutrition advice through an AI-powered chat assistant.

![Tech Stack](https://img.shields.io/badge/Stack-Flask%20%7C%20React%20%7C%20PostgreSQL-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

### 📊 Core Functionality
- **User Authentication**: Secure JWT-based authentication system
- **Profile Management**: Store and update user profile (age, sex, height, weight, activity level, goals)
- **Food Logging**: Track daily food intake with automatic nutrition calculation
- **USDA Integration**: Automatic food lookup from USDA FoodData Central API
- **Daily Nutrition Tracking**: Real-time calculation of calories, protein, carbs, and fat
- **30-Day History**: View nutrition trends over the past month
- **Daily Needs Calculator**: Calculate personalized daily calorie and macro needs using Harris-Benedict formula
- **AI Nutrition Coach**: Chat with an AI assistant powered by Claude/OpenAI for personalized nutrition advice

### 🤖 AI Chat Features
- Get user profile information
- Check today's nutrition intake
- Calculate daily calorie and macro needs
- Receive personalized nutrition recommendations

## 🛠️ Tech Stack

### Backend
- **Python 3.10** - Core language
- **Flask** - Web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Database (hosted on Supabase)
- **Flask-JWT-Extended** - Authentication
- **Flask-CORS** - Cross-origin resource sharing
- **Gevent** - WSGI server
- **Anthropic/OpenAI SDK** - AI chat functionality
- **USDA FoodData Central API** - Food nutrition data

### Frontend
- **React 19** - UI framework
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Tailwind CSS** - Styling
- **Vite** - Build tool

### Infrastructure
- **Google Cloud Run** - Serverless container deployment
- **Supabase** - PostgreSQL database hosting
- **Docker** - Containerization

## 📁 Project Structure

```
nutrition_app/
├── Backend/
│   ├── server.py           # Flask application and routes
│   ├── functions.py        # Business logic and API functions
│   ├── database.py         # Database configuration
│   ├── chat_handler.py     # AI chat endpoint handler
│   ├── mcp_tools.py        # MCP tools for AI chat
│   ├── create_schema.sql   # Database schema
│   ├── Dockerfile          # Docker configuration
│   ├── requirements.txt    # Python dependencies
│   └── config.prd.ini      # Production configuration template
├── my-app/
│   ├── src/
│   │   ├── pages/          # React page components
│   │   ├── components/     # Reusable components
│   │   ├── services/        # API service layer
│   │   └── App.jsx          # Main application component
│   └── package.json        # Node dependencies
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL database (Supabase recommended)
- USDA API key ([Get one here](https://fdc.nal.usda.gov/api-guide.html))
- Anthropic or OpenAI API key

### Backend Setup

1. **Install dependencies**
   ```bash
   cd Backend
   pip install -r requirements.txt
   ```

2. **Configure database**
   - Create a `config.prd.ini` file based on the template
   - Set your database connection details
   - Add your API keys (USDA, Anthropic/OpenAI)

3. **Initialize database**
   - Run `create_schema.sql` in your PostgreSQL database

4. **Run the server**
   ```bash
   python server.py config.prd.ini
   ```

### Frontend Setup

1. **Install dependencies**
   ```bash
   cd my-app
   npm install
   ```

2. **Configure API URL**
   - Update `src/services/api.js` with your backend URL
   - Or set `VITE_API_URL` environment variable

3. **Run development server**
   ```bash
   npm run dev
   ```

## 📡 API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /login` - User login

### Profile
- `GET /my_profile` - Get user profile
- `POST /profile_edit` - Update user profile

### Food Logging
- `POST /insert_log` - Add food intake entry
- `POST /update_log` - Update food intake entry
- `GET /retrieve_log` - Get food intake logs (optional date filter)
- `POST /delete_log` - Delete food intake entry

### Nutrition Data
- `GET /dv_summation` - Get today's nutrition totals
- `GET /daily_needs` - Calculate daily calorie and macro needs
- `GET /history_30days` - Get 30-day nutrition history

### AI Chat
- `POST /api/chat` - Chat with AI nutrition coach

## 🔐 Environment Variables

### Backend
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - Secret key for JWT tokens
- `CORS_ORIGINS` - Allowed CORS origins (comma-separated)
- `USDA_API_KEY` - USDA FoodData Central API key
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` - AI provider API key

### Frontend
- `VITE_API_URL` - Backend API URL

## 🧪 Testing

### Test Registration
```bash
curl -X POST http://localhost:8080/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass",
    "age": 25,
    "sex": "male",
    "height": 175,
    "weight": 70,
    "activity_level": "moderate",
    "goal": "maintain"
  }'
```

### Test Login
```bash
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass"
  }'
```

## 🐳 Docker Deployment

### Build and Run
```bash
cd Backend
docker build -t nutrition-app .
docker run -p 8080:8080 \
  -e DATABASE_URL=your_database_url \
  -e JWT_SECRET_KEY=your_secret_key \
  nutrition-app
```

## ☁️ Cloud Run Deployment

1. **Build and deploy**
   ```bash
   gcloud run deploy nutrition-app \
     --source ./Backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars="DATABASE_URL=...,JWT_SECRET_KEY=..."
   ```

2. **Update frontend API URL** to your Cloud Run service URL

## 📊 Database Schema

- **users**: User profiles and authentication
- **food**: Food items with nutrition data (calories, protein, carbs, fat per 100g)
- **user_intake**: Daily food intake logs

See `Backend/create_schema.sql` for complete schema.

## 🎯 Key Features Explained

### Automatic Food Lookup
When logging food, the system:
1. Searches local database first
2. If not found, queries USDA FoodData Central API
3. Automatically stores new foods in the database
4. Calculates nutrition based on quantity entered

### Daily Needs Calculation
Uses the Harris-Benedict equation to calculate:
- **BMR** (Basal Metabolic Rate)
- **TDEE** (Total Daily Energy Expenditure) based on activity level
- **Macro targets**: Protein (1.6g/kg), Fat (25% of calories), Carbs (remaining)

### AI Nutrition Coach
Powered by Claude or GPT, the chat assistant can:
- Access user profile data
- Check current nutrition intake
- Calculate personalized needs
- Provide nutrition advice and recommendations

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License.

## 👨‍💻 Author

Built with ❤️ for better nutrition tracking

---

**Note**: Remember to set up your API keys and database credentials before running the application.



