# KodeJudge - Test Cases Documentation

## Table of Contents
- [1. Health Check Endpoints](#1-health-check-endpoints)
- [2. Languages Endpoints](#2-languages-endpoints)
- [3. Submissions Endpoints](#3-submissions-endpoints)
  - [3.1 Create Single Submission](#31-create-single-submission)
  - [3.2 Create Batch Submissions](#32-create-batch-submissions)
  - [3.3 Get Submission](#33-get-submission)
  - [3.4 Get Batch Submissions](#34-get-batch-submissions)
  - [3.5 List Submissions](#35-list-submissions)
  - [3.6 Delete Submission](#36-delete-submission)
- [4. Special Features](#4-special-features)
  - [4.1 Base64 Encoding](#41-base64-encoding)
  - [4.2 Wait Mode](#42-wait-mode)
  - [4.3 Additional Files](#43-additional-files)
  - [4.4 Sandbox Limits](#44-sandbox-limits)
  - [4.5 Expected Output Comparison](#45-expected-output-comparison)

---

## 1. Health Check Endpoints

### 1.1 Overall Health Check

**Endpoint:** `GET /health/`

**Description:** Returns comprehensive health status of all system components.

#### Test Cases:

| Test Case ID | Description | Expected Result | Status Code |
|--------------|-------------|-----------------|-------------|
| HC-001 | Get overall health when all components are healthy | Returns status "healthy" with all components operational | 200 |
| HC-002 | Get overall health when database is down | Returns status "unhealthy" with database status false | 200 |
| HC-003 | Get overall health when Redis is down | Returns status "unhealthy" with Redis status false | 200 |
| HC-004 | Get overall health when no workers available | Returns status "no_workers" | 200 |
| HC-005 | Get overall health with high queue size | Returns status "degraded" if queue size exceeds threshold | 200 |

**Example Request:**
```bash
curl http://localhost:8000/health/
```

**Example Response:**
```json
{
  "status": "healthy",
  "database": {
    "status": true,
    "response_time": 0.005,
    "error": null
  },
  "redis": {
    "status": true,
    "response_time": 0.002,
    "ping": "pong"
    "error": null
  },
  "workers": {
    "queue_name": "kodejudge_submission_queue",
    "queue_size": 0,
    "workers_total": 4,
    "workers_busy": 0,
    "workers_idle": 4,
    "failed_jobs": 0,
    "status": "healthy"
  }
}
```

---

### 1.2 Database Health Check

**Endpoint:** `GET /health/database`

**Description:** Checks database connectivity and response time.

#### Test Cases:

| Test Case ID | Description | Expected Result | Status Code |
|--------------|-------------|-----------------|-------------|
| HC-DB-001 | Check database health when connected | Returns status true with response time | 200 |
| HC-DB-002 | Check database health when disconnected | Returns status false with error message | 200 |
| HC-DB-003 | Check database health with slow query | Returns status true but high response time | 200 |

**Example Request:**
```bash
curl http://localhost:8000/health/database
```

**Example Response:**
```json
{
  "status": true,
  "response_time": 0.003,
  "error": null
}
```

---

### 1.3 Redis Health Check

**Endpoint:** `GET /health/redis`

**Description:** Checks Redis connectivity and response time.

#### Test Cases:

| Test Case ID | Description | Expected Result | Status Code |
|--------------|-------------|-----------------|-------------|
| HC-RD-001 | Check Redis health when connected | Returns status true with response time | 200 |
| HC-RD-002 | Check Redis health when disconnected | Returns status false with error message | 200 |
| HC-RD-003 | Check Redis health with slow connection | Returns status true but high response time | 200 |

**Example Request:**
```bash
curl http://localhost:8000/health/redis
```

**Example Response:**
```json
{
  "status": true,
  "response_time": 0.001,
  "ping": "pong",
  "error": null
}
```

---

### 1.4 Workers Health Check

**Endpoint:** `GET /health/workers`

**Description:** Returns detailed information about RQ workers.

#### Test Cases:

| Test Case ID | Description | Expected Result | Status Code |
|--------------|-------------|-----------------|-------------|
| HC-WK-001 | Check workers when all idle | Returns healthy status with all workers idle | 200 |
| HC-WK-002 | Check workers when some are busy | Returns healthy status with correct busy/idle count | 200 |
| HC-WK-003 | Check workers when queue is full | Returns degraded status with high queue size | 200 |
| HC-WK-004 | Check workers when no workers available | Returns no_workers status | 200 |
| HC-WK-005 | Check workers with failed jobs | Returns degraded status with failed_jobs count | 200 |

**Example Request:**
```bash
curl http://localhost:8000/health/workers
```

**Example Response:**
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

---

### 1.5 System Information

**Endpoint:** `GET /health/info`

**Description:** Returns system information including version and uptime.

#### Test Cases:

| Test Case ID | Description | Expected Result | Status Code |
|--------------|-------------|-----------------|-------------|
| HC-SI-001 | Get system information | Returns API version, Python version, uptime, and statistics | 200 |
| HC-SI-002 | Check uptime calculation | Uptime increases with time | 200 |
| HC-SI-003 | Verify statistics accuracy | Statistics match actual database counts | 200 |

**Example Request:**
```bash
curl http://localhost:8000/health/info
```

**Example Response:**
```json
{
  "api_version": "1.0.0",
  "python_version": "3.13.8",
  "environment": "production",
  "uptime_seconds": 1124.25,
  "supported_languages_count": 5,
  "total_submissions": 0
}
```

---

### 1.6 Simple Ping

**Endpoint:** `GET /health/ping`

**Description:** Simple ping endpoint for basic availability check.

#### Test Cases:

| Test Case ID | Description | Expected Result | Status Code |
|--------------|-------------|-----------------|-------------|
| HC-PNG-001 | Ping the server | Returns "pong" response | 200 |

**Example Request:**
```bash
curl http://localhost:8000/health/ping
```

**Example Response:**
```json
{
  "status": "ok",
  "message": "pong"
}
```

---

## 2. Languages Endpoints

### 2.1 Get All Languages

**Endpoint:** `GET /languages/`

**Description:** Retrieves a list of all programming languages supported by the system.

#### Test Cases:

| Test Case ID | Description | Expected Result | Status Code |
|--------------|-------------|-----------------|-------------|
| LNG-001 | Get all languages when database is populated | Returns list of all languages with id, name, version | 200 |
| LNG-002 | Get all languages when database is empty | Returns empty array | 200 |
| LNG-003 | Verify language data structure | Each language has id, name, and version fields | 200 |

**Example Request:**
```bash
curl http://localhost:8000/languages/
```

**Example Response:**
```json
[
  {
    "id": 1,
    "name": "Python",
    "version": "3.11.5"
  },
  {
    "id": 2,
    "name": "JavaScript",
    "version": "20.9.0"
  },
  {
    "id": 3,
    "name": "C",
    "version": "11.4.0"
  },
  {
    "id": 4,
    "name": "C++",
    "version": "11.4.0"
  },
  {
    "id": 5,
    "name": "Java",
    "version": "17.0.9"
  }
]
```

---

### 2.2 Get Language by ID

**Endpoint:** `GET /languages/{language_id}`

**Description:** Retrieves details of a specific programming language by its ID.

#### Test Cases:

| Test Case ID | Description | Expected Result | Status Code |
|--------------|-------------|-----------------|-------------|
| LNG-ID-001 | Get existing language by valid ID | Returns language details | 200 |
| LNG-ID-002 | Get language with non-existent ID | Returns 404 error | 404 |
| LNG-ID-003 | Get language with invalid ID format (string) | Returns 422 validation error | 422 |
| LNG-ID-004 | Get language with negative ID | Returns 404 error | 404 |
| LNG-ID-005 | Get language with ID = 0 | Returns 404 error | 404 |

**Example Request:**
```bash
curl http://localhost:8000/languages/1
```

**Example Response:**
```json
{
  "id": 1,
  "name": "Python",
  "version": "3.11.5"
}
```

**Error Response (404):**
```json
{
  "detail": "Language not found"
}
```

---

## 3. Submissions Endpoints

### 3.1 Create Single Submission

**Endpoint:** `POST /submissions/`

**Description:** Submits source code for execution in a specified programming language.

#### Test Cases:

| Test Case ID | Description | Expected Result | Status Code |
|--------------|-------------|-----------------|-------------|
| SUB-001 | Create submission with valid Python code | Returns submission ID, code is queued for execution | 201 |
| SUB-002 | Create submission with valid C++ code | Returns submission ID, code is queued for execution | 201 |
| SUB-003 | Create submission with valid Java code | Returns submission ID, code is queued for execution | 201 |
| SUB-004 | Create submission with invalid language_id | Returns 400 error "Language not supported" | 400 |
| SUB-005 | Create submission without source_code | Returns 422 validation error | 422 |
| SUB-006 | Create submission without language_id | Returns 422 validation error | 422 |
| SUB-007 | Create submission with empty source_code | Returns submission ID but may result in compilation error | 201 |
| SUB-008 | Create submission with stdin input | Returns submission ID, stdin is passed to execution | 201 |
| SUB-009 | Create submission with very long source_code (stress test) | Returns submission ID or appropriate error | 201/413 |
| SUB-010 | Create submission with special characters in code | Returns submission ID, code is executed properly | 201 |
| SUB-011 | Create submission with unicode characters | Returns submission ID, unicode is handled correctly | 201 |

**Example Request (Basic):**
```bash
curl -X POST "http://localhost:8000/submissions/" \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "print(\"Hello, World!\")",
    "language_id": 1,
    "stdin": ""
  }'
```

**Example Response (without wait):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Example Request (With stdin):**
```bash
curl -X POST "http://localhost:8000/submissions/" \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "name = input()\nprint(f\"Hello, {name}!\")",
    "language_id": 1,
    "stdin": "John"
  }'
```

**Error Response (Invalid Language):**
```json
{
  "detail": "Language with ID 999 is not supported."
}
```

---

### 3.2 Create Batch Submissions

**Endpoint:** `POST /submissions/batch`

**Description:** Creates multiple submissions at once and enqueues them for execution.

#### Test Cases:

| Test Case ID | Description | Expected Result | Status Code |
|--------------|-------------|-----------------|-------------|
| SUB-BAT-001 | Create batch with 2 valid submissions | Returns array of 2 submission IDs | 201 |
| SUB-BAT-002 | Create batch with 10 valid submissions | Returns array of 10 submission IDs | 201 |
| SUB-BAT-003 | Create batch with mixed languages | Returns array of submission IDs, all queued correctly | 201 |
| SUB-BAT-004 | Create batch with one invalid language_id | Returns 400 error for the invalid submission | 400 |
| SUB-BAT-005 | Create empty batch | Returns empty array | 201 |
| SUB-BAT-006 | Create batch with 100 submissions (stress test) | Returns array of 100 IDs or appropriate error | 201/413 |
| SUB-BAT-007 | Create batch with duplicate submissions | Returns unique submission IDs for each | 201 |
| SUB-BAT-008 | Create batch with Base64 encoded data | Returns submission IDs, data decoded correctly | 201 |

**Example Request:**
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
    },
    {
      "source_code": "#include <iostream>\nint main() { std::cout << 3 + 3; return 0; }",
      "language_id": 4
    }
  ]'
```

**Example Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440002"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440003"
  }
]
```

---

### 3.3 Get Submission

**Endpoint:** `GET /submissions/{submission_id}`

**Description:** Retrieves the current status and result of a specific submission by its UUID.

#### Test Cases:

| Test Case ID | Description | Expected Result | Status Code |
|--------------|-------------|-----------------|-------------|
| SUB-GET-001 | Get pending submission | Returns submission with status PENDING | 200 |
| SUB-GET-002 | Get processing submission | Returns submission with status PROCESSING | 200 |
| SUB-GET-003 | Get finished submission (success) | Returns submission with status FINISHED and stdout | 200 |
| SUB-GET-004 | Get finished submission (compilation error) | Returns submission with status ERROR and compile_output | 200 |
| SUB-GET-005 | Get finished submission (runtime error) | Returns submission with status FINISHED and stderr | 200 |
| SUB-GET-006 | Get non-existent submission | Returns 404 error | 404 |
| SUB-GET-007 | Get submission with invalid UUID format | Returns 422 validation error | 422 |
| SUB-GET-008 | Get submission immediately after creation | Returns submission with status PENDING | 200 |
| SUB-GET-009 | Get submission with Base64 encoding flag | Returns submission with Base64 encoded fields | 200 |
| SUB-GET-010 | Verify all sandbox parameters are returned | Returns all cpu_time_limit, memory_limit, etc. | 200 |
| SUB-GET-011 | Get submission with additional_files | Returns submission with files array | 200 |
| SUB-GET-012 | Get submission with expected_output | Returns submission with expected_output field | 200 |

**Example Request:**
```bash
curl http://localhost:8000/submissions/550e8400-e29b-41d4-a716-446655440000
```

**Example Response (Pending):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "source_code": "print(\"Hello, World!\")",
  "language_id": 1,
  "stdin": null,
  "language": {
    "id": 1,
    "name": "Python",
    "version": "3.11.5"
  },
  "status": "PENDING",
  "stdout": null,
  "stderr": null,
  "compile_output": null,
  "meta": null,
  "created_at": "2025-10-17T10:30:00Z",
  "expected_output": null,
  "cpu_time_limit": 2.0,
  "cpu_extra_time": 0.5,
  "wall_time_limit": 5.0,
  "memory_limit": 128000,
  "max_processes_and_or_threads": 128,
  "max_file_size": 10240,
  "number_of_runs": 1,
  "enable_per_process_and_thread_time_limit": false,
  "enable_per_process_and_thread_memory_limit": false,
  "redirect_stderr_to_stdout": false,
  "enable_network": false
}
```

**Example Response (Finished - Success):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "source_code": "print(\"Hello, World!\")",
  "language_id": 1,
  "stdin": null,
  "language": {
    "id": 1,
    "name": "Python",
    "version": "3.11.5"
  },
  "status": "FINISHED",
  "stdout": "Hello, World!\n",
  "stderr": null,
  "compile_output": null,
  "meta": {
    "time": 0.023,
    "memory": 8192,
    "exit_code": 0
  },
  "created_at": "2025-10-17T10:30:00Z",
  "expected_output": null,
  "cpu_time_limit": 2.0,
  "cpu_extra_time": 0.5,
  "wall_time_limit": 5.0,
  "memory_limit": 128000,
  "max_processes_and_or_threads": 128,
  "max_file_size": 10240,
  "number_of_runs": 1,
  "enable_per_process_and_thread_time_limit": false,
  "enable_per_process_and_thread_memory_limit": false,
  "redirect_stderr_to_stdout": false,
  "enable_network": false
}
```

**Example Response (Error - Compilation):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "source_code": "print(\"Hello World\"",
  "language_id": 1,
  "stdin": null,
  "language": {
    "id": 1,
    "name": "Python",
    "version": "3.11.5"
  },
  "status": "ERROR",
  "stdout": null,
  "stderr": null,
  "compile_output": "SyntaxError: unexpected EOF while parsing",
  "meta": null,
  "created_at": "2025-10-17T10:30:00Z",
  "expected_output": null,
  "cpu_time_limit": 2.0,
  "cpu_extra_time": 0.5,
  "wall_time_limit": 5.0,
  "memory_limit": 128000,
  "max_processes_and_or_threads": 128,
  "max_file_size": 10240,
  "number_of_runs": 1,
  "enable_per_process_and_thread_time_limit": false,
  "enable_per_process_and_thread_memory_limit": false,
  "redirect_stderr_to_stdout": false,
  "enable_network": false
}
```

---

### 3.4 Get Batch Submissions

**Endpoint:** `GET /submissions/batch?ids={uuid1},{uuid2},{uuid3}`

**Description:** Retrieves details for multiple submissions at once.

#### Test Cases:

| Test Case ID | Description | Expected Result | Status Code |
|--------------|-------------|-----------------|-------------|
| SUB-BGET-001 | Get batch with 2 existing submissions | Returns array of 2 submission objects | 200 |
| SUB-BGET-002 | Get batch with 10 existing submissions | Returns array of 10 submission objects | 200 |
| SUB-BGET-003 | Get batch with mix of existing and non-existent IDs | Returns only existing submissions | 200 |
| SUB-BGET-004 | Get batch with all non-existent IDs | Returns empty array | 200 |
| SUB-BGET-005 | Get batch with invalid UUID format | Returns 400 error | 400 |
| SUB-BGET-006 | Get batch with empty ids parameter | Returns empty array | 200 |
| SUB-BGET-007 | Get batch with duplicate IDs | Returns unique submissions | 200 |
| SUB-BGET-008 | Get batch with Base64 encoding flag | Returns submissions with Base64 encoded fields | 200 |
| SUB-BGET-009 | Get batch with mixed statuses | Returns submissions with their current statuses | 200 |

**Example Request:**
```bash
curl "http://localhost:8000/submissions/batch?ids=550e8400-e29b-41d4-a716-446655440001,550e8400-e29b-41d4-a716-446655440002,550e8400-e29b-41d4-a716-446655440003"
```

**Example Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "source_code": "print(1 + 1)",
    "language_id": 1,
    "language": {
      "id": 1,
      "name": "Python",
      "version": "3.11.5"
    },
    "status": "FINISHED",
    "stdout": "2\n",
    "stderr": null,
    "compile_output": null,
    "meta": {
      "time": 0.015,
      "memory": 7168,
      "exit_code": 0
    },
    "created_at": "2025-10-17T10:30:00Z"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "source_code": "console.log(2 + 2)",
    "language_id": 2,
    "language": {
      "id": 2,
      "name": "JavaScript",
      "version": "20.9.0"
    },
    "status": "FINISHED",
    "stdout": "4\n",
    "stderr": null,
    "compile_output": null,
    "meta": {
      "time": 0.042,
      "memory": 15360,
      "exit_code": 0
    },
    "created_at": "2025-10-17T10:30:05Z"
  }
]
```

**Error Response (Invalid UUID):**
```json
{
  "detail": "Invalid UUID format found in 'ids' parameter."
}
```

---

### 3.5 List Submissions

**Endpoint:** `GET /submissions/?page={page}&page_size={page_size}`

**Description:** Retrieves a paginated list of all submissions.

#### Test Cases:

| Test Case ID | Description | Expected Result | Status Code |
|--------------|-------------|-----------------|-------------|
| SUB-LST-001 | List submissions with default pagination (page=1, page_size=10) | Returns first 10 submissions with pagination info | 200 |
| SUB-LST-002 | List submissions with custom page_size (20) | Returns 20 submissions per page | 200 |
| SUB-LST-003 | List submissions page 2 | Returns second page of submissions | 200 |
| SUB-LST-004 | List submissions with page beyond total pages | Returns empty items array | 200 |
| SUB-LST-005 | List submissions with page=0 | Returns 422 validation error (page must be >= 1) | 422 |
| SUB-LST-006 | List submissions with negative page | Returns 422 validation error | 422 |
| SUB-LST-007 | List submissions with page_size > 100 | Returns 422 validation error (max 100) | 422 |
| SUB-LST-008 | List submissions with page_size=1 | Returns 1 submission per page | 200 |
| SUB-LST-009 | List submissions when database is empty | Returns empty items array with total_items=0 | 200 |
| SUB-LST-010 | Verify pagination metadata accuracy | total_pages = ceil(total_items / page_size) | 200 |
| SUB-LST-011 | List submissions with Base64 encoding | Returns submissions with encoded fields | 200 |
| SUB-LST-012 | List submissions ordered by creation date | Returns submissions in chronological order | 200 |

**Example Request:**
```bash
curl "http://localhost:8000/submissions/?page=1&page_size=10"
```

**Example Response:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "source_code": "print('Hello')",
      "language_id": 1,
      "language": {
        "id": 1,
        "name": "Python",
        "version": "3.11.5"
      },
      "status": "FINISHED",
      "stdout": "Hello\n",
      "stderr": null,
      "compile_output": null,
      "meta": {
        "time": 0.020,
        "memory": 8192,
        "exit_code": 0
      },
      "created_at": "2025-10-17T10:30:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "source_code": "print('World')",
      "language_id": 1,
      "language": {
        "id": 1,
        "name": "Python",
        "version": "3.11.5"
      },
      "status": "PENDING",
      "stdout": null,
      "stderr": null,
      "compile_output": null,
      "meta": null,
      "created_at": "2025-10-17T10:31:00Z"
    }
  ],
  "total_items": 25,
  "total_pages": 3,
  "current_page": 1,
  "page_size": 10
}
```

---

### 3.6 Delete Submission

**Endpoint:** `DELETE /submissions/{submission_id}`

**Description:** Deletes a submission by its UUID.

#### Test Cases:

| Test Case ID | Description | Expected Result | Status Code |
|--------------|-------------|-----------------|-------------|
| SUB-DEL-001 | Delete existing pending submission | Submission deleted successfully | 204 |
| SUB-DEL-002 | Delete existing finished submission | Submission deleted successfully | 204 |
| SUB-DEL-003 | Delete non-existent submission | Returns 404 error | 404 |
| SUB-DEL-004 | Delete with invalid UUID format | Returns 422 validation error | 422 |
| SUB-DEL-005 | Delete same submission twice | First succeeds, second returns 404 | 204, 404 |
| SUB-DEL-006 | Delete submission while processing | Submission deleted but job may still complete | 204 |
| SUB-DEL-007 | Verify deletion by getting deleted submission | Returns 404 error | 404 |

**Example Request:**
```bash
curl -X DELETE http://localhost:8000/submissions/550e8400-e29b-41d4-a716-446655440000
```

**Example Response:**
```
(Empty response with status 204)
```

**Error Response (Not Found):**
```json
{
  "detail": "Submission not found"
}
```

---

## 4. Special Features

### 4.1 Base64 Encoding

**Description:** Support for Base64 encoded source code, stdin, and output fields.

#### Test Cases:

| Test Case ID | Description | Expected Result | Status Code |
|--------------|-------------|-----------------|-------------|
| B64-001 | Create submission with Base64 encoded source_code | Decodes and executes correctly | 201 |
| B64-002 | Create submission with Base64 encoded stdin | Decodes and passes to program correctly | 201 |
| B64-003 | Create batch submissions with Base64 encoding | All submissions decoded and queued | 201 |
| B64-004 | Get submission with base64_encoded=true | Returns Base64 encoded stdout, stderr | 200 |
| B64-005 | Get batch submissions with base64_encoded=true | Returns Base64 encoded fields for all | 200 |
| B64-006 | List submissions with base64_encoded=true | Returns Base64 encoded fields for all items | 200 |
| B64-007 | Create submission with invalid Base64 | Returns 400 error "Invalid Base64" | 400 |
| B64-008 | Base64 encode binary data in source_code | Handles binary data correctly | 201 |
| B64-009 | Base64 encode unicode characters | Preserves unicode correctly | 201 |
| B64-010 | Create submission with Base64 additional_files | Files decoded and created correctly | 201 |

**Example Request (Create with Base64):**
```bash
# Base64 of: print("Hello, World!")
curl -X POST "http://localhost:8000/submissions/?base64_encoded=true" \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "cHJpbnQoIkhlbGxvLCBXb3JsZCEiKQ==",
    "language_id": 1,
    "stdin": ""
  }'
```

**Example Request (Get with Base64):**
```bash
curl "http://localhost:8000/submissions/550e8400-e29b-41d4-a716-446655440000?base64_encoded=true"
```

**Example Response (Base64 encoded):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "source_code": "cHJpbnQoIkhlbGxvLCBXb3JsZCEiKQ==",
  "language_id": 1,
  "stdin": null,
  "language": {
    "id": 1,
    "name": "Python",
    "version": "3.11.5"
  },
  "status": "FINISHED",
  "stdout": "SGVsbG8sIFdvcmxkIQo=",
  "stderr": null,
  "compile_output": null,
  "meta": {
    "time": 0.023,
    "memory": 8192,
    "exit_code": 0
  },
  "created_at": "2025-10-17T10:30:00Z"
}
```

---

### 4.2 Wait Mode

**Description:** Optional synchronous execution mode that waits for submission completion.

#### Test Cases:

| Test Case ID | Description | Expected Result | Status Code |
|--------------|-------------|-----------------|-------------|
| WAIT-001 | Create submission with wait=true (fast execution) | Returns full submission with FINISHED status | 201 |
| WAIT-002 | Create submission with wait=true (compilation error) | Returns submission with ERROR status and compile_output | 201 |
| WAIT-003 | Create submission with wait=true (timeout) | Returns 408 timeout error after 15 seconds | 408 |
| WAIT-004 | Create submission with wait=true (long execution) | Waits until completion or timeout | 201/408 |
| WAIT-005 | Create submission with wait=false | Returns submission ID immediately | 201 |
| WAIT-006 | Wait mode with Base64 encoding | Returns encoded fields when complete | 201 |
| WAIT-007 | Wait mode with invalid code | Returns ERROR status with error details | 201 |
| WAIT-008 | Multiple concurrent wait mode requests | All requests handled correctly | 201 |

**Example Request:**
```bash
curl -X POST "http://localhost:8000/submissions/?wait=true" \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "print(\"Hello, World!\")",
    "language_id": 1,
    "stdin": ""
  }'
```

**Example Response (Success):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "source_code": "print(\"Hello, World!\")",
  "language_id": 1,
  "stdin": null,
  "language": {
    "id": 1,
    "name": "Python",
    "version": "3.11.5"
  },
  "status": "FINISHED",
  "stdout": "Hello, World!\n",
  "stderr": null,
  "compile_output": null,
  "meta": {
    "time": 0.023,
    "memory": 8192,
    "exit_code": 0
  },
  "created_at": "2025-10-17T10:30:00Z",
  "expected_output": null,
  "cpu_time_limit": 2.0,
  "cpu_extra_time": 0.5,
  "wall_time_limit": 5.0,
  "memory_limit": 128000,
  "max_processes_and_or_threads": 128,
  "max_file_size": 10240,
  "number_of_runs": 1,
  "enable_per_process_and_thread_time_limit": false,
  "enable_per_process_and_thread_memory_limit": false,
  "redirect_stderr_to_stdout": false,
  "enable_network": false
}
```

**Error Response (Timeout):**
```json
{
  "detail": "Request timed out while waiting for submission to complete."
}
```

---

### 4.3 Additional Files

**Description:** Support for uploading additional files with submissions.

#### Test Cases:

| Test Case ID | Description | Expected Result | Status Code |
|--------------|-------------|-----------------|-------------|
| FILE-001 | Create submission with 1 additional file | File created and accessible during execution | 201 |
| FILE-002 | Create submission with multiple additional files | All files created correctly | 201 |
| FILE-003 | Create submission with additional files (C++ header) | Header file imported successfully | 201 |
| FILE-004 | Create submission with additional files (Python module) | Module imported successfully | 201 |
| FILE-005 | Create submission with 0 additional files | Submission created without files | 201 |
| FILE-006 | Create submission exceeding max file count | Returns 400 error | 400 |
| FILE-007 | Create submission exceeding total file size limit | Returns 400 error | 400 |
| FILE-008 | Additional files with Base64 encoding | Files decoded correctly | 201 |
| FILE-009 | Additional files with special characters in name | File names handled correctly | 201 |
| FILE-010 | Additional files with duplicate names | Last file overwrites or error returned | 201/400 |
| FILE-011 | Get submission with additional files | Returns files in response | 200 |

**Example Request (With Additional Files):**
```bash
curl -X POST "http://localhost:8000/submissions/" \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "from helper import add\nprint(add(2, 3))",
    "language_id": 1,
    "additional_files": [
      {
        "name": "helper.py",
        "content": "def add(a, b):\n    return a + b"
      }
    ]
  }'
```

**Example Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**C++ Example with Header File:**
```bash
curl -X POST "http://localhost:8000/submissions/" \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "#include <iostream>\n#include \"math.h\"\nint main() {\n    std::cout << add(5, 3) << std::endl;\n    return 0;\n}",
    "language_id": 4,
    "additional_files": [
      {
        "name": "math.h",
        "content": "#ifndef MATH_H\n#define MATH_H\nint add(int a, int b) { return a + b; }\n#endif"
      }
    ]
  }'
```

---

### 4.4 Sandbox Limits

**Description:** Configurable execution limits for sandboxed code execution.

#### Test Cases:

| Test Case ID | Description | Expected Result | Status Code |
|--------------|-------------|-----------------|-------------|
| SAND-001 | Create submission with custom cpu_time_limit | Execution respects time limit | 201 |
| SAND-002 | Create submission with custom memory_limit | Execution respects memory limit | 201 |
| SAND-003 | Create submission exceeding cpu_time_limit | Execution terminated, timeout in meta | 201 |
| SAND-004 | Create submission exceeding memory_limit | Execution terminated, memory error in meta | 201 |
| SAND-005 | Create submission with max_processes_and_or_threads=1 | Multi-threading blocked | 201 |
| SAND-006 | Create submission with enable_network=true | Network access allowed | 201 |
| SAND-007 | Create submission with enable_network=false | Network access blocked | 201 |
| SAND-008 | Create submission with redirect_stderr_to_stdout=true | Stderr redirected to stdout | 201 |
| SAND-009 | Create submission with number_of_runs=3 | Code executed 3 times | 201 |
| SAND-010 | Create submission with default limits (null values) | Uses system default limits | 201 |
| SAND-011 | Create submission with very low cpu_time_limit (0.1s) | Quick timeout if exceeded | 201 |
| SAND-012 | Create submission with very high memory_limit | No memory issues | 201 |
| SAND-013 | Verify sandbox parameters in response | All parameters returned correctly | 200 |
| SAND-014 | Create infinite loop with time limit | Execution stopped at limit | 201 |
| SAND-015 | Create memory bomb with memory limit | Execution stopped at limit | 201 |

**Example Request (Custom Limits):**
```bash
curl -X POST "http://localhost:8000/submissions/" \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "import time\ntime.sleep(10)",
    "language_id": 1,
    "cpu_time_limit": 1.0,
    "memory_limit": 64000,
    "wall_time_limit": 2.0
  }'
```

**Example Response (Time Limit Exceeded):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "source_code": "import time\ntime.sleep(10)",
  "language_id": 1,
  "status": "FINISHED",
  "stdout": null,
  "stderr": null,
  "compile_output": null,
  "meta": {
    "time": 1.0,
    "memory": 8192,
    "exit_code": null,
    "signal": "SIGKILL",
    "message": "Time limit exceeded"
  },
  "created_at": "2025-10-17T10:30:00Z",
  "cpu_time_limit": 1.0,
  "cpu_extra_time": 0.5,
  "wall_time_limit": 2.0,
  "memory_limit": 64000
}
```

**Example Request (Enable Network):**
```bash
curl -X POST "http://localhost:8000/submissions/" \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "import requests\nprint(requests.get(\"https://api.github.com\").status_code)",
    "language_id": 1,
    "enable_network": true
  }'
```

**All Configurable Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cpu_time_limit` | float | 2.0 | Maximum CPU time in seconds |
| `cpu_extra_time` | float | 0.5 | Extra time for system operations |
| `wall_time_limit` | float | 5.0 | Maximum wall clock time |
| `memory_limit` | int | 128000 | Maximum memory in KB |
| `max_processes_and_or_threads` | int | 128 | Maximum number of processes/threads |
| `max_file_size` | int | 10240 | Maximum file size in KB |
| `number_of_runs` | int | 1 | Number of times to run the code |
| `enable_per_process_and_thread_time_limit` | bool | false | Enable per-process time limits |
| `enable_per_process_and_thread_memory_limit` | bool | false | Enable per-process memory limits |
| `redirect_stderr_to_stdout` | bool | false | Redirect stderr to stdout |
| `enable_network` | bool | false | Enable network access |

---

### 4.5 Expected Output Comparison

**Description:** Optional field to store expected output for automatic comparison.

#### Test Cases:

| Test Case ID | Description | Expected Result | Status Code |
|--------------|-------------|-----------------|-------------|
| EXP-001 | Create submission with expected_output | Field stored in database | 201 |
| EXP-002 | Create submission without expected_output | Field is null | 201 |
| EXP-003 | Get submission with expected_output | Field returned in response | 200 |
| EXP-004 | Create submission with expected_output matching actual | Can be compared in worker | 201 |
| EXP-005 | Create submission with expected_output not matching actual | Can be compared in worker | 201 |
| EXP-006 | Expected output with whitespace differences | Stored as-is, comparison logic in worker | 201 |
| EXP-007 | Expected output with newline differences | Stored as-is, comparison logic in worker | 201 |
| EXP-008 | Expected output with unicode | Unicode preserved correctly | 201 |
| EXP-009 | Expected output with Base64 encoding | Decoded if base64_encoded flag set | 201 |
| EXP-010 | Very long expected_output | Stored correctly | 201 |

**Example Request:**
```bash
curl -X POST "http://localhost:8000/submissions/" \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "print(2 + 2)",
    "language_id": 1,
    "expected_output": "4\n"
  }'
```

**Example Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "source_code": "print(2 + 2)",
  "language_id": 1,
  "language": {
    "id": 1,
    "name": "Python",
    "version": "3.11.5"
  },
  "status": "FINISHED",
  "stdout": "4\n",
  "stderr": null,
  "compile_output": null,
  "expected_output": "4\n",
  "meta": {
    "time": 0.018,
    "memory": 8192,
    "exit_code": 0,
    "output_matches": true
  },
  "created_at": "2025-10-17T10:30:00Z"
}
```

---

## 5. Error Scenarios

### Common Error Cases

| Error Code | Scenario | Expected Response |
|------------|----------|-------------------|
| 400 | Invalid language_id | `{"detail": "Language with ID X is not supported."}` |
| 400 | Invalid Base64 encoding | `{"detail": "Invalid Base64 encoding in source_code/stdin"}` |
| 400 | Invalid UUID format in batch get | `{"detail": "Invalid UUID format found in 'ids' parameter."}` |
| 400 | Exceeding file size limits | `{"detail": "Total size of additional files exceeds limit"}` |
| 400 | Exceeding file count limits | `{"detail": "Number of additional files exceeds limit"}` |
| 404 | Submission not found | `{"detail": "Submission not found"}` |
| 404 | Language not found | `{"detail": "Language not found"}` |
| 408 | Wait mode timeout | `{"detail": "Request timed out while waiting for submission to complete."}` |
| 422 | Missing required field | `{"detail": [{"loc": [...], "msg": "field required", "type": "value_error.missing"}]}` |
| 422 | Invalid field type | `{"detail": [{"loc": [...], "msg": "value is not a valid integer", "type": "type_error.integer"}]}` |
| 422 | Validation error | `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}` |
| 500 | Internal server error | `{"detail": "Internal server error"}` |
| 503 | Service unavailable | `{"detail": "Service temporarily unavailable"}` |

---

## 6. Performance & Load Testing

### Performance Test Cases

| Test Case ID | Description | Expected Result |
|--------------|-------------|-----------------|
| PERF-001 | Submit 100 submissions simultaneously | All submissions queued successfully within 5 seconds |
| PERF-002 | Submit 1000 submissions over 1 minute | System handles load without errors |
| PERF-003 | Get 100 submissions simultaneously | All requests return within 2 seconds |
| PERF-004 | Process submissions with 4 workers | Submissions processed in parallel |
| PERF-005 | Process submissions with 1 worker | Submissions processed sequentially |
| PERF-006 | Large source code (1MB) | Submission handled correctly |
| PERF-007 | Very long execution time (near limit) | Execution completes or times out properly |
| PERF-008 | Concurrent wait mode requests | All requests handled without blocking |
| PERF-009 | Batch create 100 submissions | All submissions created within 3 seconds |
| PERF-010 | List submissions with large dataset (10000+) | Pagination works efficiently |

---

## 7. Integration Test Scenarios

### End-to-End Workflows

#### Workflow 1: Simple Code Execution
1. Get available languages
2. Create submission with Python code
3. Poll submission status until FINISHED
4. Verify output matches expected result

#### Workflow 2: Batch Processing
1. Create batch of 10 submissions with different languages
2. Get batch submission IDs
3. Wait for all to complete
4. Get batch results
5. Verify all processed correctly

#### Workflow 3: Error Handling
1. Create submission with invalid code
2. Wait for completion
3. Verify ERROR status
4. Check compile_output contains error message

#### Workflow 4: Resource Limits
1. Create submission with tight time limit
2. Submit code with sleep/infinite loop
3. Verify execution terminated at limit
4. Check meta contains timeout info

#### Workflow 5: File Upload
1. Create submission with additional files
2. Source code imports/includes additional file
3. Verify execution uses the file
4. Check output is correct

#### Workflow 6: Base64 Workflow
1. Encode source code and stdin to Base64
2. Create submission with base64_encoded=true
3. Get submission with base64_encoded=true
4. Decode and verify output

#### Workflow 7: Health Monitoring
1. Check overall health
2. Check individual components
3. Verify all components healthy
4. Get system info
5. Monitor worker queue

---

## 8. Security Test Cases

| Test Case ID | Description | Expected Result |
|--------------|-------------|-----------------|
| SEC-001 | Submit code with file system access | Access restricted by sandbox |
| SEC-002 | Submit code with network access (disabled) | Network blocked |
| SEC-003 | Submit code with fork bomb | Process limit prevents system crash |
| SEC-004 | Submit code with memory bomb | Memory limit prevents system crash |
| SEC-005 | Submit code trying to access parent directories | Access denied |
| SEC-006 | Submit malicious code with shell commands | Sandboxing prevents execution |
| SEC-007 | Submit code with SQL injection in stdin | Input handled safely |
| SEC-008 | Submit code with XSS in source_code | Output sanitized |
| SEC-009 | Submit very large files | Size limits enforced |
| SEC-010 | Submit code reading /etc/passwd | Access denied by sandbox |

---

## 9. Regression Test Cases

| Test Case ID | Description | Priority |
|--------------|-------------|----------|
| REG-001 | All basic CRUD operations work | High |
| REG-002 | All languages execute correctly | High |
| REG-003 | Pagination works correctly | Medium |
| REG-004 | Base64 encoding/decoding works | Medium |
| REG-005 | Wait mode timeout works | Medium |
| REG-006 | Additional files feature works | Medium |
| REG-007 | Sandbox limits enforced | High |
| REG-008 | Batch operations work | Medium |
| REG-009 | Health checks return accurate data | Low |
| REG-010 | Error messages are clear and helpful | Low |

---

## 10. Test Data

### Sample Code Snippets

#### Python (language_id: 1)
```python
# Hello World
print("Hello, World!")

# With stdin
name = input()
print(f"Hello, {name}!")

# Mathematical
print(2 + 2)

# Error
print("Missing closing quote
```

#### JavaScript (language_id: 2)
```javascript
// Hello World
console.log("Hello, World!");

// With input (from stdin via Node.js)
const readline = require('readline');
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

rl.on('line', (name) => {
  console.log(`Hello, ${name}!`);
  rl.close();
});

// Mathematical
console.log(2 + 2);
```

#### C (language_id: 3)
```c
// Hello World
#include <stdio.h>

int main() {
    printf("Hello, World!\n");
    return 0;
}

// With input
#include <stdio.h>

int main() {
    char name[100];
    scanf("%s", name);
    printf("Hello, %s!\n", name);
    return 0;
}
```

#### C++ (language_id: 4)
```cpp
// Hello World
#include <iostream>

int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}

// With input
#include <iostream>
#include <string>

int main() {
    std::string name;
    std::cin >> name;
    std::cout << "Hello, " << name << "!" << std::endl;
    return 0;
}
```

#### Java (language_id: 5)
```java
// Hello World
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}

// With input
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        String name = scanner.nextLine();
        System.out.println("Hello, " + name + "!");
        scanner.close();
    }
}
```

---

## 11. Automation Guidelines

### Recommended Test Automation Tools
- **API Testing:** Postman, Newman, REST Assured, Pytest
- **Load Testing:** JMeter, Locust, k6
- **Security Testing:** OWASP ZAP, Burp Suite
- **Monitoring:** Prometheus, Grafana

### Test Execution Priority
1. **Smoke Tests** (Run first, quick validation)
   - Health check ping
   - Get languages
   - Create and get simple submission

2. **Critical Path Tests** (Core functionality)
   - All submission CRUD operations
   - Wait mode
   - Batch operations

3. **Extended Tests** (Full coverage)
   - All test cases in this document

### CI/CD Integration
- Run smoke tests on every commit
- Run critical path tests on PR
- Run full test suite nightly
- Run load tests weekly

---

## Conclusion

This document covers comprehensive test cases for the KodeJudge system, including:
- ✅ Health check endpoints (6 endpoints, 20+ test cases)
- ✅ Language endpoints (2 endpoints, 8 test cases)
- ✅ Submission endpoints (6 endpoints, 100+ test cases)
- ✅ Special features (Base64, Wait mode, Files, Sandbox, Expected output)
- ✅ Error scenarios
- ✅ Performance testing
- ✅ Security testing
- ✅ Integration workflows

**Total Test Cases:** 200+

For automated testing implementation, prioritize critical path tests and gradually expand coverage based on system usage and identified issues.
