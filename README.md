# 🥗 Nutrition Tracker

A full-stack web application for tracking daily nutrition intake, calculating personalized dietary needs, and receiving AI-powered nutrition coaching. Built with modern technologies and deployed on cloud infrastructure.

![Tech Stack](https://img.shields.io/badge/Stack-Flask%20%7C%20React%20%7C%20PostgreSQL-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Live demo
- Link:https://nutrition-manager-tau.vercel.app/login
- Username:test1
- Password:e
## Motivation
- People need an app to track nutrition intake. Nutrition tracking apps on the markets enables basic nutrition tracking and does not provide recommendations. This increase user time to find cuisine that meets the nutrition goal. My solution is therefore nutrition tracking + recommendation feature. 


## ✨ Key Features

- **User Authentication & Profiles**: JWT-based authentication with comprehensive user profile management
- **Food Logging System**: Track daily food intake with automatic nutrition calculation
- **USDA Food Database Integration**: Real-time food lookup and nutrition data retrieval via USDA FoodData Central API
- **Nutrition Analytics**: Real-time calculation of calories, protein, carbs, and fat with 7-day history tracking
- **Personalized Daily Needs Calculator**: TDEE and macro target calculations using Harris-Benedict equation
- **AI Nutrition Coach**: Conversational AI assistant powered by Claude/OpenAI that provides personalized nutrition advice using MCP tools
- **RESTful API**: Scalable backend API with comprehensive error handling and validation

## 🛠️ Tech Stack

### Backend
- **Python 3.10** | **Flask** | **SQLAlchemy** | **PostgreSQL**
- **Flask-JWT-Extended** (Authentication) | **Flask-CORS** (Cross-origin support)
- **Anthropic/OpenAI SDK** (AI integration) | **USDA FoodData Central API**
- **Redis** (Caching - optional) | **Gevent** (WSGI server)
- **Pytest** (Unit testing)

### Frontend
- **React 19** | **React Router** | **Tailwind CSS**
- **Axios** (HTTP client) | **Vite** (Build tool)

### Infrastructure & DevOps
- **Google Cloud Run** (Serverless deployment)
- **Supabase** (PostgreSQL hosting)
- **Docker** (Containerization)
- **Environment-based configuration** (Development, Production, Testing)
- **Upstash** (redis hosting)
  
## 🏗️ Architecture Highlights

- **RESTful API Design**: Clean separation between routes, business logic, and data access layers
- **Database-First Approach**: Optimized PostgreSQL schema with proper indexing and relationships
- **Caching Strategy**: Redis integration for improved performance (gracefully degrades when unavailable)
- **AI Integration**: Model Context Protocol (MCP) tools enabling the AI assistant to access user data and perform calculations
- **Security**: JWT authentication, password hashing, CORS configuration, and input validation
- **Error Handling**: Comprehensive exception handling with appropriate HTTP status codes
- **Testing**: Unit tests with pytest and mocking for isolated component testing

## ☁️ Deployment

Deployed on **Google Cloud Run** with:
- Docker containerization
- Environment-based configuration
- Automatic scaling
- PostgreSQL database on Supabase
- Optional Redis caching

## 🎯 Technical Achievements

- Integrated multiple external APIs (USDA FoodData Central, Anthropic/OpenAI)
- Implemented sophisticated nutrition calculation algorithms (TDEE, macro distribution)
- Built conversational AI interface with tool-enabled context awareness
- Designed scalable database schema with optimized queries
- Created responsive, modern UI with Tailwind CSS
- Implemented comprehensive error handling and caching strategies

## 📝 License

MIT License

---

Built with modern web technologies and best practices for a scalable, maintainable application.
