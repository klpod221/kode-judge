# Kode Judge

Kode Judge is a scalable, containerized online code judge system. It supports multiple programming languages, real-time code execution, and is designed for educational or competitive programming platforms.

## Features
- Multi-language code execution
- RESTful API (FastAPI)
- Asynchronous task processing (Celery)
- Docker-based sandboxing for code safety
- PostgreSQL database
- Easy to extend and maintain

## Project Structure
```
server/   # FastAPI backend, API, DB models, migrations
worker/   # Celery worker for code execution
postgres_data/ # PostgreSQL data volume
```

## Getting Started
1. Clone the repository:
   ```zsh
   git clone <your-repo-url>
   cd kode-judge
   ```
2. Start the services:
   ```zsh
   docker-compose up --build
   ```
3. API available at: `http://localhost:8000/docs`

## Requirements
- Docker & Docker Compose
- Python 3.10+

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
