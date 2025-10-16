<div align="center">
    <h1>KodeJudge: Modern Online Code Execution Engine</h1>
    <p>A powerful, scalable online code judge system with multi-language support, sandboxed execution, and clean architecture following SOLID principles.</p>
    <img src="https://img.shields.io/github/last-commit/klpod221/kode-judge?style=for-the-badge&color=74c7ec&labelColor=111827" alt="Last Commit">
    <img src="https://img.shields.io/github/stars/klpod221/kode-judge?style=for-the-badge&color=facc15&labelColor=111827" alt="GitHub Stars">
    <img src="https://img.shields.io/github/repo-size/klpod221/kode-judge?style=for-the-badge&color=a78bfa&labelColor=111827" alt="Repo Size">
    <img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge&color=34d399&labelColor=111827" alt="License">
</div>

## 📝 Description

**KodeJudge** is a modern online code execution engine inspired by Judge0. It provides a robust platform for executing code in multiple programming languages with secure sandboxing using Isolate. Built with FastAPI and following SOLID principles, it offers a clean, maintainable, and scalable architecture perfect for educational platforms, coding competitions, and automated testing systems.

## ✨ Features

- 🚀 **Multi-Language Support** - Execute code in Python, C, C++, Java, JavaScript, and more
- 🔒 **Secure Sandboxing** - Isolate-based sandboxing for safe code execution
- ⚡ **Async Processing** - RQ (Redis Queue) for asynchronous job processing
- 🔄 **Concurrent Workers** - Configurable number of workers for parallel execution
- 🏗️ **Clean Architecture** - SOLID principles with Repository and Service patterns
- 🐳 **Docker-based** - Fully containerized with Docker Compose
- 📊 **RESTful API** - FastAPI with automatic OpenAPI documentation
- 💾 **Persistent Storage** - PostgreSQL database with async support
- 📦 **Base64 Support** - Handle encoded source code and I/O
- 🔄 **Batch Operations** - Submit and retrieve multiple submissions at once
- ⏱️ **Wait Mode** - Optional synchronous execution with immediate results
- 🔍 **Health Checks** - Comprehensive monitoring endpoints for all system components

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/klpod221/kode-judge.git
   cd kode-judge
   ```

2. **Start the services:**
   ```bash
   docker compose up --build
   ```

3. **Run database migrations:**
   ```bash
   docker compose run --rm server alembic upgrade head
   docker compose run --rm server python -m app.scripts.seed  # Seed initial data
   ```

4. **Access the API:**
   - API Documentation: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`
   - API Root: `http://localhost:8000`

### Configuration

Environment variables can be configured in `.env` file:

```env
# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=kode_judge
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PREFIX=kodejudge

# Worker
WORKER_CONCURRENCY=4  # Number of concurrent workers (default: 4)
```

## 📚 API Usage

### Create a Submission

```bash
curl -X POST "http://localhost:8000/submissions/" \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "print(\"Hello, World!\")",
    "language_id": 1,
    "stdin": ""
  }'
```

### Get Submission Result

```bash
curl "http://localhost:8000/submissions/{submission_id}"
```

### List All Languages

```bash
curl "http://localhost:8000/languages/"
```

### Health Check

```bash
# Overall health
curl "http://localhost:8000/health/"

# Database health
curl "http://localhost:8000/health/database"

# Redis health
curl "http://localhost:8000/health/redis"

# Workers health
curl "http://localhost:8000/health/workers"

# System information
curl "http://localhost:8000/health/info"

# Simple ping
curl "http://localhost:8000/health/ping"
```

### Batch Submissions

```bash
curl -X POST "http://localhost:8000/submissions/batch" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "source_code": "print(1 + 1)",
      "language_id": 1
    },
    {
      "source_code": "console.log(2 + 2)",
      "language_id": 2
    }
  ]'
```

For more examples, visit the interactive API documentation at `/docs`.

## ⚙️ Worker Configuration

### Adjusting Worker Concurrency

KodeJudge supports running multiple workers in parallel to handle high loads. Configure the number of workers using the `WORKER_CONCURRENCY` environment variable:

```env
# .env file
WORKER_CONCURRENCY=8  # Run 8 workers in parallel
```

**Default:** 4 workers

**Recommendations:**
- **Low traffic:** 2-4 workers
- **Medium traffic:** 4-8 workers
- **High traffic:** 8-16 workers
- **Resource consideration:** Each worker requires CPU and memory for code execution

### Monitoring Workers

Check worker status:
```bash
# View worker logs
docker-compose logs -f worker

# Check running workers
docker-compose exec worker rq info --url redis://queue:6379

# Health check via API
curl http://localhost:8000/health/workers
```

## 🔍 Monitoring & Health Checks

KodeJudge provides comprehensive health check endpoints for monitoring system status:

### Available Endpoints

| Endpoint | Description | Response |
|----------|-------------|----------|
| `/health/` | Overall system health | Status of all components |
| `/health/database` | Database connectivity | Connection status & response time |
| `/health/redis` | Redis connectivity | Connection status & response time |
| `/health/workers` | Worker status | Queue size, worker count, failed jobs |
| `/health/info` | System information | Version, uptime, statistics |
| `/health/ping` | Simple availability check | Basic pong response |

### Health Status Values

- `healthy` - All systems operational
- `degraded` - System operational but with issues (high load, failed jobs)
- `unhealthy` - Critical component failure
- `no_workers` - No workers available to process submissions

### Worker Health Metrics

The `/health/workers` endpoint provides detailed metrics:

```json
{
  "queue_name": "kodejudge_submission_queue",
  "queue_size": 5,
  "workers_total": 4,
  "workers_busy": 2,
  "workers_idle": 2,
  "failed_jobs": 0,
  "status": "healthy"
}
```

### Integration with Monitoring Tools

Health check endpoints can be integrated with monitoring tools like:
- **Prometheus** - For metrics collection
- **Grafana** - For visualization
- **UptimeRobot** - For uptime monitoring
- **Datadog** - For comprehensive monitoring

Example Prometheus scrape config:
```yaml
scrape_configs:
  - job_name: 'kodejudge'
    metrics_path: '/health/'
    static_configs:
      - targets: ['localhost:8000']
```

## 🛠️ Development

## 🎯 Supported Languages

- Python 3.x
- JavaScript (Node.js)
- C (GCC)
- C++ (G++)
- Java
- And more...

See `/languages` endpoint for the complete list.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**klpod221** (Bùi Thanh Xuân)

- GitHub: [@klpod221](https://github.com/klpod221)
- Website: [klpod221.com](https://klpod221.com)
- Email: klpod221@gmail.com

## 🙏 Acknowledgments

- Inspired by [Judge0](https://judge0.com/)
- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Sandboxing powered by [Isolate](https://github.com/ioi/isolate)
