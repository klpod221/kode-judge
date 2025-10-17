<div align="center">
    <h1>KodeJudge: Modern Online Code Execution Engine</h1>
    <p>A powerful, scalable online code judge system with multi-language support, sandboxed execution, and clean architecture following SOLID principles.</p>
    <img src="https://img.shields.io/github/last-commit/klpod221/kode-judge?style=for-the-badge&color=74c7ec&labelColor=111827" alt="Last Commit">
    <img src="https://img.shields.io/github/stars/klpod221/kode-judge?style=for-the-badge&color=facc15&labelColor=111827" alt="GitHub Stars">
    <img src="https://img.shields.io/github/repo-size/klpod221/kode-judge?style=for-the-badge&color=a78bfa&labelColor=111827" alt="Repo Size">
    <img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge&color=34d399&labelColor=111827" alt="License">
</div>

## 📝 Description

**KodeJudge** is a modern, high-performance online code execution engine inspired by Judge0. It provides a robust and secure platform for executing code in multiple programming languages with Isolate-based sandboxing. Perfect for educational platforms, coding competitions, online assessments, and automated testing systems.

> You can find the project demo on [KodeJudge Demo](https://kodejudge.klpod221.com)

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
   docker compose exec server alembic upgrade head # Create database schema
   docker compose exec server python -m app.scripts.seed # Seed initial data
   ```

4. **Access the API:**
   - API Documentation: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`
   - API Root: `http://localhost:8000`

### Configuration

Create a `.env` file based on `.env.example`:

```env
# Database Configuration
POSTGRES_HOST=db
POSTGRES_USER=kodejudge
POSTGRES_PASSWORD=yourpasswordhere
POSTGRES_DB=kodejudge
POSTGRES_PORT=5432

# Redis Configuration
REDIS_HOST=queue
REDIS_PORT=6379
REDIS_PREFIX=kodejudge

# Worker Configuration
WORKER_CONCURRENCY=4                            # Number of concurrent workers

# Sandbox Execution Limits
SANDBOX_CPU_TIME_LIMIT=2.0                      # CPU time in seconds
SANDBOX_CPU_EXTRA_TIME=0.5                      # Extra CPU time buffer in seconds
SANDBOX_WALL_TIME_LIMIT=5.0                     # Wall clock time in seconds
SANDBOX_MEMORY_LIMIT=128000                     # Memory limit in KB (128MB)
SANDBOX_MAX_PROCESSES=128                       # Maximum processes/threads
SANDBOX_MAX_FILE_SIZE=10240                     # Max file size in KB (10MB)
SANDBOX_NUMBER_OF_RUNS=1                        # Default number of runs

# Sandbox Optional Features
SANDBOX_ENABLE_PER_PROCESS_TIME_LIMIT=false
SANDBOX_ENABLE_PER_PROCESS_MEMORY_LIMIT=false
SANDBOX_REDIRECT_STDERR_TO_STDOUT=false
SANDBOX_ENABLE_NETWORK=false

# Additional Files Configuration
SANDBOX_MAX_ADDITIONAL_FILES=10                 # Max number of additional files
SANDBOX_MAX_ADDITIONAL_FILES_SIZE=2048          # Total size in KB (2MB)

# Rate Limiting Configuration
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=20                        # Max requests per minute
RATE_LIMIT_PER_HOUR=100                         # Max requests per hour
RATE_LIMIT_STRATEGY=fixed-window                # fixed-window or sliding-window
```

## 📚 API Usage

Visit the API documentation at `http://localhost:8000/docs` for detailed information on available endpoints, request/response formats, and examples. Or use the ReDoc interface at `http://localhost:8000/redoc` for an alternative view.

## ⚙️ Worker Configuration

### Adjusting Worker Concurrency

KodeJudge supports running multiple workers in parallel to handle high submission loads efficiently. Configure the number of workers using the `WORKER_CONCURRENCY` environment variable:

```env
# .env file
WORKER_CONCURRENCY=8  # Run 8 workers in parallel
```

**Default:** 4 workers

**Recommendations:**
- **Low traffic (< 10 submissions/min):** 2-4 workers
- **Medium traffic (10-50 submissions/min):** 4-8 workers
- **High traffic (50+ submissions/min):** 8-16 workers
- **Resource consideration:** Each worker requires CPU and memory for code execution. Monitor system resources to find optimal worker count.

### Monitoring Workers

**Check worker status via API:**
```bash
curl http://localhost:8000/health/workers
```

**Check worker status via CLI:**
```bash
# View worker logs
docker compose logs -f worker

# Check running workers and queue info
docker compose exec worker rq info --url redis://queue:6379

# Monitor queue size
docker compose exec worker python -m app.db_utils --check-queue
```

**Worker Metrics:**
- Queue name: The name of the Redis queue being used
- Queue size: Number of jobs waiting in the queue
- Workers total: Total number of worker processes
- Workers busy: Number of workers currently processing jobs
- Workers idle: Number of idle workers available for new jobs
- Failed jobs: Number of jobs that have failed during processing
- Status: Overall status of the worker system (e.g., healthy, degraded)

## 🎯 Supported Languages

KodeJudge supports multiple programming languages with pre-configured compilation and execution commands:

| Language | Version | ID |
|----------|---------|------|
| Python | 3.x | 1 |
| JavaScript (Node.js) | Latest | 2 |
| C (GCC) | Latest | 3 |
| C++ (G++) | Latest | 4 |
| Java | Latest | 5 |

To see the complete list with detailed configuration:
```bash
curl "http://localhost:8000/languages/"
```

### Adding New Languages

Languages can be added through the database seeding script at `server/app/scripts/seed.py`. Each language requires:
- **Name** and **version**
- **Source file extension**
- **Compile command** (if applicable)
- **Run command**

## 🤝 Contributing

Contributions are welcome! Whether it's bug fixes, new features, documentation improvements, or language support, your help is appreciated.

### How to Contribute

1. **Fork the repository**
   ```bash
   git clone https://github.com/klpod221/kode-judge.git
   cd kode-judge
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make your changes**
   - Follow the existing code style
   - Add tests for new features
   - Update documentation as needed

4. **Test your changes**
   ```bash
   docker compose up --build
   # Run tests
   docker compose exec server pytest
   ```

5. **Commit your changes**
   ```bash
   git commit -m "Add: amazing feature description"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```

7. **Open a Pull Request**
   - Provide a clear description of the changes
   - Reference any related issues

### Development Guidelines

- Write clean, readable code following SOLID principles
- Use meaningful variable and function names
- Add comments for complex logic
- Write tests for new features
- Update documentation for API changes
- Follow existing project structure and patterns

### Areas for Contribution

- 🌐 **Language Support**: Add new programming languages
- 🔒 **Security**: Improve sandboxing and security features
- 📊 **Monitoring**: Enhanced metrics and logging
- 🧪 **Testing**: Increase test coverage
- 📚 **Documentation**: Improve guides and examples
- 🎨 **Features**: New submission options or API endpoints

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🌟 Acknowledgments

- **[Judge0](https://judge0.com/)** - Inspiration for this project
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[Isolate](https://github.com/ioi/isolate)** - Sandbox for secure code execution
- **[RQ (Redis Queue)](https://python-rq.org/)** - Simple job queue for Python
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - Python SQL toolkit and ORM
- **[PostgreSQL](https://www.postgresql.org/)** - Powerful open-source database
- **[Redis](https://redis.io/)** - In-memory data structure store

## 👤 Author

**klpod221** (Bùi Thanh Xuân)

- 🌐 Website: [klpod221.com](https://klpod221.com)
- 💻 GitHub: [@klpod221](https://github.com/klpod221)
- 📧 Email: klpod221@gmail.com

## 📞 Support

If you have any questions or need help, feel free to:
- Open an issue on [GitHub](https://github.com/klpod221/kode-judge/issues)
- Contact via email: klpod221@gmail.com
- Visit my website: [klpod221.com](https://klpod221.com)

---

<div align="center">
    <p>Made with ❤️ by klpod221</p>
    <p>⭐ Star this repository if you find it helpful!</p>
</div>
