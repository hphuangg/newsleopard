# Backend API

A FastAPI application with PostgreSQL database, Docker support, and comprehensive testing setup.

## Features

- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Robust relational database
- **Docker**: Containerized deployment
- **Testing**: Comprehensive test suite with pytest
- **API Documentation**: Auto-generated Swagger/ReDoc docs

## Quick Start

### Using Docker (Recommended)

1. Clone the repository
2. Navigate to the backend directory
3. Start the application:

```bash
docker-compose up -d
```

The API will be available at: http://localhost:8000

### Local Development

1. Create and activate virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
cp .env.example .env
```

4. Start PostgreSQL database (ensure it's running on localhost:5432)

5. Run the application:

```bash
uvicorn app.main:app --reload
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Run tests with:

```bash
pytest
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   └── items.py
│   │       └── api.py
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   └── database.py
│   ├── models/
│   ├── schemas/
│   ├── crud/
│   ├── tests/
│   │   └── test_main.py
│   └── main.py
├── docker/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Environment Variables

See `.env.example` for all available configuration options.

## API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check

### Items (Sample CRUD)
- `GET /api/v1/items/` - List all items
- `GET /api/v1/items/{item_id}` - Get specific item
- `POST /api/v1/items/` - Create new item
- `DELETE /api/v1/items/{item_id}` - Delete item