# Automated Lead Generation Agentic System

A standalone Django-based application running in an optimized Docker environment. Uses LangGraph and DuckDuckGo search to discover businesses, extract profiles, qualify them, and save to a SQLite database.

## Setup

1. Copy `.env.example` to `.env` and fill in your `OPENROUTER_API_KEY` and `OPENROUTER_API_BASE`.
2. Build and start the Docker container:
   `docker-compose up --build -d`
3. Run migrations:
   `docker-compose exec web python manage.py migrate`
4. Access the application at `http://localhost:8000`.
