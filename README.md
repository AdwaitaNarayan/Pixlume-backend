# Pixlume Backend API

This is the backend API for **Pixlume**, a high-resolution photography platform. It is built using [FastAPI](https://fastapi.tiangolo.com/), uses SQLAlchemy with [Alembic](https://alembic.sqlalchemy.org/en/latest/) for database migrations, and exposes endpoints for managing photos and admin functionalities.

## Tech Stack

*   **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
*   **Database ORM:** SQLAlchemy (Async)
*   **Database Migrations:** Alembic
*   **Python Version:** Python 3.8+ recommended

## Project Structure

```text
Pixlume-backend/
├── alembic/              # Database migration scripts
├── app/
│   ├── database/         # Database connection and session setup
│   ├── models/           # SQLAlchemy ORM models
│   ├── routes/           # API endpoints (routers for /photos, /admin)
│   ├── schemas/          # Pydantic schemas for data validation
│   ├── services/         # Business logic
│   └── main.py           # FastAPI application initialization
├── .env.example          # Example environment variables
├── alembic.ini           # Alembic configuration
└── requirements.txt      # Python dependencies
```

## Setup Instructions

### 1. Clone the repository

If you haven't already, clone the repository and navigate to the backend directory:

```bash
cd Pixlume-backend
```

### 2. Set up a Virtual Environment

It is highly recommended to use a virtual environment to manage dependencies:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

Install the required Python packages using `pip`:

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

1.  Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
2.  Open the `.env` file and configure your database connection string and any other required variables.

### 5. Run Database Migrations

Before running the application, ensure your database schema is up-to-date using Alembic:

```bash
alembic upgrade head
```

## Running the Application

You can start the development server using `uvicorn`:

```bash
uvicorn app.main:app --reload
```

The API will be available at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

### API Documentation

FastAPI automatically generates interactive API documentation. Once the server is running, you can access:
*   **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
*   **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## CORS Configuration

Currently, CORS is configured in `app/main.py` to allow the Next.js frontend (or any local development origin) to interact with the API:
*   `http://localhost:3000`
*   `http://127.0.0.1:3000`
