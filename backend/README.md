# FlowRisk Backend

FastAPI backend for FlowRisk application with Firebase authentication and SQLAlchemy.

## Local Development Setup

### Prerequisites
- Python 3.11 or higher
- SQLite (for local development)

### Installation

1. **Create and activate virtual environment:**

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

**Important:** Do NOT run `pip install -e .` - this is not a packaged module. Use `requirements.txt` as the single source of truth for dependencies.

3. **Set up local environment:**

The `.env` file is already configured for local SQLite development:
```
ENVIRONMENT=local
DATABASE_URL=sqlite:///./flowrisk.db
```

4. **Run database migrations:**

```bash
# Run from backend/ directory
alembic upgrade head
```

5. **Start the development server:**

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check (public)
- `GET /v1/me` - Get current user (requires Firebase authentication)

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Check current migration status
alembic current
```

## Production Deployment

For production, update `.env` with PostgreSQL connection:
```
DATABASE_URL=postgresql+psycopg://user:password@host:5432/dbname
```
