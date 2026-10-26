# Automated Application Deployment Using Jenkins and Docker
### Course Registration Web App — Complete End-to-End CI/CD Pipeline

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.0-black.svg)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite3-lightgrey.svg)](https://www.sqlite.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![Jenkins](https://img.shields.io/badge/CI%2FCD-Jenkins%20Pipeline-D24939.svg)](https://www.jenkins.io/)
[![pytest](https://img.shields.io/badge/Testing-pytest%20v9-green.svg)](https://docs.pytest.org/)

---

## 1. Project Overview & Problem Statement

In traditional software delivery, manual testing, container building, and server deployments are error-prone, slow, and frequently cause production outages.

This project delivers a **production-ready, automated Continuous Integration and Continuous Deployment (CI/CD) pipeline** for a Python Flask application (**Course Registration Web App**). The pipeline guarantees that:
1. Every code change pushed to GitHub triggers an automated build.
2. Code is validated with unit and integration tests using `pytest`.
3. If any test fails, deployment is **immediately aborted**, preventing faulty code from reaching production.
4. Only verified code is packaged into an optimized Docker container and launched with Gunicorn.
5. Persistent SQLite storage ensures student registrations survive container restarts and upgrades.
6. Automated health verification probes the `/health` endpoint before declaring the deployment successful.

---

## 2. Architecture & CI/CD Workflow

```
+----------------------------------------------------------------------------------------------------+
|                                    CI / CD PIPELINE ARCHITECTURE                                   |
+----------------------------------------------------------------------------------------------------+

   [ Developer Machine ]
             |
             | (git push)
             v
   [ GitHub Repository ]
             |
             | (Webhook / SCM Polling)
             v
   +---------------------------------------------------------------------------------------+
   |                                   JENKINS CI/CD SERVER                                |
   |                                                                                       |
   |   [Stage 1: Checkout]  ===>  [Stage 2: Dependencies]  ===>  [Stage 3: Pytest Suite]    |
   |   Pulls latest code          Creates venv & installs       Runs isolated unit &       |
   |                              Flask, Gunicorn, pytest       integration tests          |
   |                                                                    |                  |
   |                                                    +---------------+                  |
   |                                                    | (Pass)            | (Fail)       |
   |                                                    v                   v              |
   |                                          [Stage 4: Docker Build]  [STOP PIPELINE]     |
   |                                          Builds Docker image      Mark build failed   |
   |                                                    |                                  |
   |                                                    v                                  |
   |                                          [Stage 5: Safe Deploy]                       |
   |                                          Replaces container &                         |
   |                                          attaches volume                              |
   |                                                    |                                  |
   |                                                    v                                  |
   |                                          [Stage 6: Health Verify]                     |
   |                                          Polls http://localhost:5000/health           |
   +---------------------------------------------------------------------------------------+
                                                        |
                                                        v
                                    +---------------------------------------+
                                    |        DOCKER HOST ENVIRONMENT        |
                                    |                                       |
                                    |   [ Course Registration Container ]   |
                                    |     - Gunicorn WSGI Server (0.0.0.0)  |
                                    |     - Flask Web Application           |
                                    |     - Port 5000:5000                  |
                                    |                   |                   |
                                    |                   v                   |
                                    |   [ Persistent Docker Volume ]        |
                                    |     course_registration_data          |
                                    |     `-> /app/data/course_app.db       |
                                    +---------------------------------------+
```

---

## 3. Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.11 & Flask 3.1 | Web application routing, validation, and API |
| **WSGI Server** | Gunicorn 23.0 | Production HTTP WSGI server for Docker |
| **Database** | SQLite 3 | Embedded SQL database for courses & enrollments |
| **Frontend UI** | HTML5, CSS3, Bootstrap 5.3, Jinja2 | Modern responsive UI, cards, badges & alerts |
| **Automated Testing** | pytest 9.1 | Automated test execution with isolated temp DBs |
| **Containerization** | Docker & Docker Compose | Multi-stage image build and volume persistence |
| **CI/CD Automation** | Jenkins (Declarative Pipeline) | 6-stage automated build, test, deploy & health check |
| **Version Control** | Git & GitHub | Source code tracking and pipeline triggers |

---

## 4. Project Directory Structure

```
DEVOPS/
├── app.py                      # Flask application factory, database initialization & routes
├── requirements.txt            # Python dependencies (Flask, Gunicorn, pytest, requests)
├── Dockerfile                  # Production container definition (python:3.11-slim, healthcheck)
├── docker-compose.yml          # Docker Compose specification with persistent named volume
├── Jenkinsfile                 # Declarative 6-stage CI/CD pipeline definition
├── .dockerignore               # Files excluded from Docker image build context
├── .gitignore                  # Files excluded from Git version control
├── static/
│   └── css/
│       └── style.css           # Custom design system tokens, card hover effects & badges
├── templates/
│   ├── base.html               # Shared layout, navigation bar, and flash alert containers
│   ├── index.html              # Course catalog, live seat availability, registration form
│   └── registrations.html      # Table of registered students with timestamps & badges
├── tests/
│   ├── __init__.py             # Test package identifier
│   └── test_app.py             # 7 pytest test cases with isolated temporary SQLite databases
└── README.md                   # Comprehensive documentation, setup guide & demonstration manual
```

---

## 5. Application Features & Rules

1. **Course Catalog**: Home page (`/`) displays available courses, instructors, descriptions, total seats, and real-time remaining seats.
2. **Dynamic Badging**: Course cards display real-time status badges (e.g., `Available`, `Only X Seats Left`, or `FULL`).
3. **Student Registration Form**: Validates student name, email, and course selection.
4. **Duplicate Prevention**: Rejects duplicate registrations if the same email attempts to register for the same course more than once.
5. **Seat Limit Enforcement**: Blocks registrations when a course has 0 available seats left.
6. **Registered Students View**: Dedicated `/registrations` page displaying student names, emails, enrolled courses, and enrollment timestamps.
7. **Health API Endpoint**: `/health` returns HTTP 200 and `{"status": "healthy", "service": "course-registration-app", "version": "1.0.0", "database": "connected"}`.
8. **Automatic Database Seeding**: Pre-populates 4 sample courses (`DEV101`, `PY202`, `SEC303`, `K8S404`) on startup if the database is uninitialized.

---

## 6. Step-by-Step Local Setup & Execution (Without Docker)

### Prerequisites
- Python 3.9+ installed (`python --version`)
- Git installed (`git --version`)

### 1. Create and Activate Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**On Linux / macOS (Bash):**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Project Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Run the Flask Web Application Locally
```bash
python app.py
```
*Output:*
```
Starting Course Registration Web App on http://0.0.0.0:5000
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
```

Open your browser and navigate to:
- **Home & Registration**: [http://localhost:5000](http://localhost:5000)
- **Registered Students**: [http://localhost:5000/registrations](http://localhost:5000/registrations)
- **Health Check API**: [http://localhost:5000/health](http://localhost:5000/health)

---

## 7. Running Automated Tests with Pytest

To execute the test suite across all 7 automated test scenarios:

```bash
python -m pytest -v
```

### Expected Output:
```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1
rootdir: C:\Users\...\DEVOPS
collected 7 items

tests/test_app.py::test_home_page_status_and_content PASSED              [ 14%]
tests/test_app.py::test_health_endpoint_healthy PASSED                   [ 28%]
tests/test_app.py::test_successful_registration PASSED                   [ 42%]
tests/test_app.py::test_duplicate_registration_rejected PASSED           [ 57%]
tests/test_app.py::test_registration_rejected_when_course_full PASSED    [ 71%]
tests/test_app.py::test_invalid_form_submissions PASSED                  [ 85%]
tests/test_app.py::test_registrations_page_empty_and_populated PASSED    [100%]

============================== 7 passed in 1.00s ==============================
```

> **Note on Test Isolation**: Each test automatically instantiates a fresh temporary SQLite database (`tempfile.mkstemp()`). No production or local database data is modified during test runs.

---

## 8. Docker & Docker Compose Setup

### Option A: Using Docker CLI Directly
```bash
# 1. Build the Docker image
docker build -t course-registration-app:latest .

# 2. Create the persistent Docker volume
docker volume create course_registration_data

# 3. Run the container
docker run -d \
  --name course-registration-container \
  --restart unless-stopped \
  -p 5000:5000 \
  -v course_registration_data:/app/data \
  course-registration-app:latest

# 4. View container status & health
docker ps

# 5. Check container logs
docker logs -f course-registration-container
```

### Option B: Using Docker Compose
```bash
# Build and start container in the background
docker compose up -d --build

# View container logs
docker compose logs -f

# Stop container without losing data
docker compose down
```

### Verify Container Health
```bash
curl -i http://localhost:5000/health
```
*HTTP Response:*
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "database": "connected",
  "service": "course-registration-app",
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## 9. Jenkins CI/CD Pipeline Setup

### 9.1 Required Jenkins Plugins
Ensure the following plugins are installed under **Manage Jenkins > Plugins > Available Plugins**:
1. **Pipeline** (workflow-aggregator)
2. **Git Plugin** (git)
3. **JUnit Plugin** (junit - to display test reports)
4. **AnsiColor** (ansicolor - for colored terminal logs)

### 9.2 Jenkins Host Permissions & Docker Access
If Jenkins runs on Linux/Ubuntu, grant the `jenkins` user access to the Docker daemon:
```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```
*(On Windows Jenkins, ensure Docker Desktop is running and accessible from PowerShell).*

### 9.3 Create the Pipeline Job in Jenkins
1. Open Jenkins at `http://localhost:8080`.
2. Click **New Item**.
3. Enter item name: `Course-Registration-CI-CD`.
4. Select **Pipeline** and click **OK**.
5. In the Job Configuration:
   - Check **GitHub project** and enter your repository URL (e.g., `https://github.com/your-username/course-registration-ci-cd`).
   - Under **Build Triggers**, check **Poll SCM** with schedule: `H/5 * * * *` (polls GitHub every 5 minutes).
   - Under **Pipeline**, select **Pipeline script from SCM**.
   - SCM: **Git**
   - Repository URL: `https://github.com/your-username/course-registration-ci-cd.git`
   - Branch Specifier: `*/main` (or `*/master`)
   - Script Path: `Jenkinsfile`
6. Click **Save**.

---

## 10. GitHub Integration & Automatic Trigger Setup

### Step 1: Initialize Git and Commit All Files Locally
Run these exact commands in your project directory:

```bash
# 1. Initialize local Git repository
git init

# 2. Add all files
git add .

# 3. Create initial commit
git commit -m "feat: Initial commit of Course Registration Web App with tests and Jenkinsfile"

# 4. Set default branch to main
git branch -M main
```

### Step 2: Push to GitHub
1. Go to [GitHub](https://github.com) and click **New Repository**.
2. Name it `course-registration-ci-cd` (leave README unchecked as we already have one).
3. Connect and push your local repository:

```bash
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/course-registration-ci-cd.git
git push -u origin main
```

### Step 3: Configure GitHub Webhook (Optional for Instant Triggers)
If your Jenkins server is publicly accessible (or via tools like `ngrok`):
1. In your GitHub repository, click **Settings > Webhooks > Add webhook**.
2. **Payload URL**: `http://<YOUR_JENKINS_HOST>:8080/github-webhook/`
3. **Content type**: `application/json`
4. Which events? Select: **Just the push event**.
5. Click **Add webhook**.

> *Note*: If Jenkins is running on a private localhost without a public domain, the **Poll SCM** (`H/5 * * * *`) trigger configured in the `Jenkinsfile` will automatically detect new commits every 5 minutes without needing an external webhook!

---

## 11. Demonstrating Automatic Deployment (College Practical Guide)

Follow this exact walkthrough to demonstrate automatic deployment during an evaluation or college presentation:

### Step 1: Run First Build in Jenkins
1. Go to your `Course-Registration-CI-CD` project in Jenkins.
2. Click **Build Now**.
3. Watch the Stage View execute all 6 stages with green checkmarks:
   - *1. Checkout Source Code*
   - *2. Prepare Test Environment*
   - *3. Run Automated Tests* (7/7 passed)
   - *4. Build Docker Image*
   - *5. Deploy Application Container*
   - *6. Verify Deployment Health*
4. Open `http://localhost:5000` to show the running application.

### Step 2: Demonstrate the Test Safety Gate (Failure Prevention)
1. Intentionally break a test in `tests/test_app.py` (e.g., change `assert response.status_code == 200` to `500`).
2. Commit and push:
   ```bash
   git add tests/test_app.py
   git commit -m "test: simulate broken test"
   git push origin main
   ```
3. Jenkins triggers the build.
4. **Result**: Stage 3 (*Run Automated Tests*) fails! The pipeline halts immediately.
5. **Observation**: Stages 4, 5, and 6 are **SKIPPED**. The live application at `http://localhost:5000` remains completely unaffected and unharmed!

### Step 3: Demonstrate Automatic Deployment with UI Update
1. Revert the test fix.
2. Open `templates/index.html` and change the portal subtitle from:
   ```html
   <h1 class="display-6 fw-bold text-navy mb-2">Automated Course Registration Portal</h1>
   ```
   To:
   ```html
   <h1 class="display-6 fw-bold text-navy mb-2">Automated Course Registration Portal (v2.0 - Auto Deployed)</h1>
   ```
3. Commit and push:
   ```bash
   git add templates/index.html tests/test_app.py
   git commit -m "feat(ui): update portal heading to v2.0"
   git push origin main
   ```
4. Watch Jenkins detect the change, pass all tests, rebuild the Docker image, safely swap the container, and verify health.
5. Refresh `http://localhost:5000` in your browser: The new title is live, and all previously registered students remain intact in SQLite!

---

## 12. Common Errors and Troubleshooting

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **`docker: command not found` in Jenkins** | Jenkins user cannot access Docker CLI | Ensure Docker is on PATH and run `sudo usermod -aG docker jenkins && sudo systemctl restart jenkins`. |
| **`Permission denied: /var/run/docker.sock`** | Socket file permissions | Run `sudo chmod 666 /var/run/docker.sock`. |
| **Port 5000 already in use** | Another app or container is bound to port 5000 | Find and kill the process: `docker stop $(docker ps -q --filter "publish=5000")` or on Windows: `netstat -ano \| findstr :5000`. |
| **Health check timed out** | Container took longer than expected to start | Increase `MAX_RETRIES` in `Jenkinsfile` stage 6 or check `docker logs course-registration-container`. |
| **Database locked error** | Simultaneous write locks in SQLite | Handled cleanly in `app.py` with scoped session teardowns and `PRAGMA foreign_keys = ON;`. |

---

## 13. Suggested Screenshots for Project Report

1. **Jenkins Pipeline Stage View**: Showing all 6 stages colored green.
2. **Pytest Execution Terminal**: Displaying 7 passed tests.
3. **Application Home Page**: Showing course cards with live seat counts and badges.
4. **Duplicate Registration Warning**: Red/yellow alert demonstrating constraint validation.
5. **Course Full Notification**: Error message when attempting to register for a filled course.
6. **Enrolled Students Table**: Showing registered students and course codes.
7. **Health API JSON Output**: Browser showing `{"status":"healthy", "database":"connected"}`.
8. **Docker Container CLI Output**: `docker ps` showing container name and mapped port 5000.
