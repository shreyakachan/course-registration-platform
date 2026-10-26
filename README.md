# Automated Course Registration Platform with Jenkins and Docker CI/CD

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-black.svg)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy%202.0-red.svg)](https://www.sqlalchemy.org/)
[![SQLite](https://img.shields.io/badge/Database-SQLite3-lightgrey.svg)](https://www.sqlite.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![Jenkins](https://img.shields.io/badge/CI%2FCD-7--Stage%20Pipeline-D24939.svg)](https://www.jenkins.io/)
[![pytest](https://img.shields.io/badge/Tests-25%20Passed-brightgreen.svg)](https://docs.pytest.org/)

---

## 1. Abstract

Modern higher-education institutions require dependable, fault-tolerant software delivery systems to handle course enrollment spikes without service degradation or manual deployment errors. The **Automated Course Registration Platform** is a full-stack, enterprise-grade academic portal built with Python, Flask, SQLAlchemy, and Bootstrap 5, backed by an automated 7-stage Continuous Integration and Continuous Deployment (CI/CD) pipeline powered by Jenkins, Docker, and GitHub. The platform enforces strict role-based access control (RBAC), database-level seat capacity constraints, atomic transactions, and zero-downtime container rollouts with persistent storage and automated health verification.

---

## 2. Problem Statement

Manual deployment and testing workflows in university IT environments suffer from:
1. **Human Error**: Forgotten database migrations, missing environment variables, and unexecuted test suites cause frequent production outages.
2. **Overbooking & Concurrency Bugs**: Inadequate database constraints allow students to bypass course seat limits or register duplicate enrollments.
3. **Data Loss During Upgrades**: Naive container updates discard local database states, erasing student registrations.
4. **Slow Feedback Loops**: Developers discover syntax or business logic bugs hours or days after commits rather than within seconds.

---

## 3. Objectives & Proposed Solution

### Objectives
- Automate testing, image packaging, and deployment from Git commit to production.
- Provide a robust role-based portal for students (enrollment, dashboards, drops) and administrators (curriculum CRUD, capacity management, audit logs).
- Maintain 100% database persistence across container destruction and upgrades.
- Enforce automated quality gates: reject any build that fails unit, integration, or security tests.

### Proposed Solution
An end-to-end DevOps pipeline where every GitHub push triggers a 7-stage Jenkins declarative pipeline. The pipeline runs an isolated 25-test pytest suite, packages a secure non-root Docker container running Gunicorn, mounts a persistent SQLite Docker volume, and polls an HTTP `/health` probe before finalizing deployment.

---

## 4. System & CI/CD Architecture

```
+----------------------------------------------------------------------------------------------------+
|                                      END-TO-END CI/CD WORKFLOW                                     |
+----------------------------------------------------------------------------------------------------+

   [ Developer Machine ]
             |
             | (git push origin main)
             v
   [ GitHub Repository ]
             |
             | (Webhook trigger / SCM Polling: H/5 * * * *)
             v
+----------------------------------------------------------------------------------------------------+
|                                        JENKINS CI/CD SERVER                                        |
|                                                                                                    |
|  [Stage 1: Checkout]  ===>  [Stage 2: Dependencies]  ===>  [Stage 3: Automated Pytest Suite]       |
|  Clones Git repository      Prepares isolated venv         Executes 25 Unit/Integration Tests      |
|                             Installs requirements                         |                        |
|                                                              +------------+                        |
|                                                              | (Pass)            | (Fail)          |
|                                                              v                   v                 |
|                                                    [Stage 4: Docker Build]  [HALT PIPELINE]        |
|                                                    Builds image with        Stop immediately;      |
|                                                    commit/build tag         No deployment occurs   |
|                                                              |                                     |
|                                                              v                                     |
|                                                    [Stage 5: Deploy Container]                     |
|                                                    Safely stops old container;                     |
|                                                    Mounts 'course_registration_data' volume        |
|                                                              |                                     |
|                                                              v                                     |
|                                                    [Stage 6: Verify Health]                        |
|                                                    Probes http://localhost:5000/health (retries)   |
|                                                              |                                     |
|                                                              v                                     |
|                                                    [Stage 7: Report Status]                        |
|                                                    Logs deployment telemetry & metrics             |
+----------------------------------------------------------------------------------------------------+
                                                               |
                                                               v
                                           +---------------------------------------+
                                           |        DOCKER HOST ENVIRONMENT        |
                                           |                                       |
                                           |   [ Course Registration Container ]   |
                                           |     - Gunicorn WSGI Server (0.0.0.0)  |
                                           |     - Python 3.11-slim (Non-root)     |
                                           |     - Port 5000:5000                  |
                                           |                   |                   |
                                           |                   v                   |
                                           |   [ Persistent Docker Volume ]        |
                                           |     course_registration_data          |
                                           |     `-> /app/data/course_app.db       |
                                           +---------------------------------------+
```

---

## 5. Technology Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.11 & Flask 3.1 | Lightweight, modular micro-framework with Blueprint routing |
| **Database ORM** | SQLAlchemy 2.0 & Flask-SQLAlchemy | Typed models, atomic transactions, relationship management |
| **Database Engine** | SQLite 3 | Embedded zero-configuration SQL database with persistent volumes |
| **Authentication** | Flask-Login & Werkzeug | Salted PBKDF2 password hashing, secure session cookies |
| **Form Validation** | Flask-WTF & WTForms | Server-side CSRF validation, email normalization, field limits |
| **Frontend UI** | HTML5, CSS3, Bootstrap 5.3, Jinja2 | Responsive SaaS university theme (Navy/Indigo/Slate) |
| **Automated Testing** | pytest 9.1 & Flask Test Client | 25 automated tests with isolated temporary SQLite DBs |
| **WSGI Server** | Gunicorn 23.0 | Production HTTP multi-worker server for Linux containers |
| **Containerization** | Docker & Docker Compose | Multi-stage image build, non-root user, persistent volume |
| **CI/CD Automation** | Jenkins Declarative Pipeline | 7-stage automated build, test, deploy, and health verification |
| **Version Control** | Git & GitHub | Distributed version control and automated SCM triggers |

---

## 6. Database Schema & Business Constraints

```
+---------------------------------+          +--------------------------------------+
|             users               |          |               courses                |
+---------------------------------+          +--------------------------------------+
| id            : INTEGER (PK)    |          | id          : INTEGER (PK)           |
| name          : VARCHAR(100)    |          | code        : VARCHAR(20) (UQ, IDX)  |
| email         : VARCHAR(120)(UQ)|          | title       : VARCHAR(150)           |
| password_hash : VARCHAR(256)    |          | category    : VARCHAR(60)            |
| role          : VARCHAR(20)     |          | instructor  : VARCHAR(100)           |
| created_at    : DATETIME        |          | credits     : INTEGER                |
+---------------------------------+          | duration    : VARCHAR(50)            |
               |                             | capacity    : INTEGER                |
               | 1                           | created_at  : DATETIME               |
               |                             +--------------------------------------+
               | N                                              | 1
               v                                                v N
+-----------------------------------------------------------------------------------+
|                                   registrations                                   |
+-----------------------------------------------------------------------------------+
| id            : INTEGER (PK)                                                      |
| student_id    : INTEGER (FK -> users.id, ON DELETE CASCADE, IDX)                  |
| course_id     : INTEGER (FK -> courses.id, ON DELETE CASCADE, IDX)                |
| status        : VARCHAR(20) ('ENROLLED', 'CANCELLED')                             |
| registered_at : DATETIME                                                          |
| UNIQUE CONSTRAINT: (student_id, course_id)                                        |
+-----------------------------------------------------------------------------------+
```

### Core Business Rules
1. **Duplicate Prevention**: A student cannot enroll in the same course twice (`uq_student_course` unique constraint).
2. **Seat Limit Enforcement**: A student cannot register for a course with 0 available seats.
3. **Capacity Boundary**: An administrator cannot reduce course capacity below current active enrollments.
4. **Safe Deletion**: An administrator cannot delete a course that has active enrolled students.
5. **Seat Release on Cancellation**: Dropping a course marks status as `CANCELLED` and immediately releases the reserved seat back to the course pool.
6. **Role Isolation**: Only administrators can access `/admin/*` routes; students attempting access receive HTTP 403 Forbidden.

---

## 7. Folder Structure

```
DEVOPS/
├── app.py                      # Application factory & Jinja context processors
├── config.py                   # Development, Testing, Production configurations
├── extensions.py               # SQLAlchemy, LoginManager, CSRFProtect instances
├── requirements.txt            # Locked project dependencies
├── Dockerfile                  # Production container definition (python:3.11-slim, Gunicorn)
├── docker-compose.yml          # Container composition with named volume persistence
├── Jenkinsfile                 # 7-stage declarative CI/CD pipeline
├── .dockerignore               # Optimized Docker build context exclusions
├── .gitignore                  # Git exclusions (caches, .db, .venv)
├── models/
│   ├── __init__.py             # Model exports
│   ├── user.py                 # User model (UserMixin, hashing, RBAC)
│   ├── course.py               # Course model (real-time capacity properties)
│   └── registration.py         # Registration model (unique constraints, cancel)
├── forms/
│   ├── __init__.py             # Form exports
│   ├── auth_forms.py           # LoginForm, RegisterForm, ProfileForm
│   ├── course_forms.py         # CourseForm with capacity validation
│   └── registration_forms.py   # EmptyForm for CSRF on POST actions
├── routes/
│   ├── __init__.py             # Blueprint registrations
│   ├── main.py                 # Landing page & /health probe
│   ├── auth.py                 # Login, register, logout, profile
│   ├── courses.py              # Catalog, filters, search, detail, enroll
│   ├── student.py              # Student dashboard & registration management
│   ├── admin.py                # Admin control center, course CRUD, audit logs
│   └── errors.py               # Custom 403, 404, 500 error handlers
├── services/
│   ├── __init__.py             # Service exports
│   └── seed_service.py         # Idempotent database seeder (courses & accounts)
├── utils/
│   ├── __init__.py             # Utility exports
│   └── decorators.py           # @admin_required security decorator
├── templates/
│   ├── base.html               # Master layout, navy navigation, flash alerts
│   ├── index.html              # Landing page with live database statistics
│   ├── auth/                   # Login, register, profile templates
│   ├── courses/                # Course catalog & detail templates
│   ├── student/                # Student dashboard & enrollments templates
│   ├── admin/                  # Admin dashboard, course form, audit log
│   └── errors/                 # Custom 403, 404, 500 pages
├── static/
│   ├── css/style.css           # Modern university design system tokens
│   └── js/main.js              # Alert auto-dismiss & confirmation handlers
├── tests/
│   ├── __init__.py             # Test package marker
│   ├── conftest.py             # Isolated DB fixtures and role clients
│   ├── test_app.py             # Full student journey integration test
│   ├── test_auth.py            # Authentication, registration, RBAC tests
│   ├── test_courses.py         # Catalog search, filter, detail tests
│   ├── test_registration.py    # Seat limits, duplicate prevention, drops
│   ├── test_admin.py           # Admin CRUD, capacity boundaries, audit logs
│   └── test_health.py          # /health HTTP 200 & 500 failure detection
└── README.md                   # Comprehensive engineering documentation
```

---

## 8. Complete Local Setup & Execution

### Prerequisites
- Python 3.9+ (`python --version`)
- Git (`git --version`)

### Step 1: Create Virtual Environment & Install Dependencies
**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**Linux / macOS (Bash):**
```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Step 2: Run Application Locally
```bash
python app.py
```

Open your browser to:
- **Home Portal**: `http://localhost:5000`
- **Course Catalog**: `http://localhost:5000/courses/`
- **Sign In**: `http://localhost:5000/login`
- **Health Verification API**: `http://localhost:5000/health`

### Pre-Seeded Demo Credentials
| Role | Email | Password | Privileges |
| :--- | :--- | :--- | :--- |
| **Student** | `student@university.edu` | `Student123!` | Browse courses, enroll, view dashboard, drop courses |
| **Admin** | `admin@university.edu` | `Admin123!` | Create/edit courses, manage capacity, audit all enrollments |

---

## 9. Running Automated Tests with Pytest

Execute the complete 25-test automated test suite:

```bash
python -m pytest -v
```

### Verified Test Results
```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1
rootdir: C:\Users\...\DEVOPS
collected 25 items

tests/test_admin.py::test_admin_dashboard_renders_kpis PASSED            [  4%]
tests/test_admin.py::test_admin_can_create_new_course PASSED             [  8%]
tests/test_admin.py::test_admin_capacity_cannot_be_reduced_below_enrolled_count PASSED [ 12%]
tests/test_admin.py::test_admin_cannot_delete_course_with_active_enrollments PASSED [ 16%]
tests/test_admin.py::test_admin_can_delete_course_without_enrollments PASSED [ 20%]
tests/test_admin.py::test_admin_registrations_view_shows_records PASSED  [ 24%]
tests/test_app.py::test_full_student_journey PASSED                      [ 28%]
tests/test_auth.py::test_valid_login_succeeds PASSED                     [ 32%]
tests/test_auth.py::test_invalid_login_fails PASSED                      [ 36%]
tests/test_auth.py::test_logout_clears_session PASSED                    [ 40%]
tests/test_auth.py::test_unauthenticated_cannot_access_protected_routes PASSED [ 44%]
tests/test_auth.py::test_student_cannot_access_admin_dashboard PASSED    [ 48%]
tests/test_auth.py::test_student_registration_and_duplicate_prevention PASSED [ 52%]
tests/test_courses.py::test_course_catalog_renders_courses PASSED        [ 56%]
tests/test_courses.py::test_course_catalog_search_and_filter PASSED      [ 60%]
tests/test_courses.py::test_course_detail_page_renders_accurately PASSED [ 64%]
tests/test_courses.py::test_nonexistent_course_returns_404 PASSED        [ 68%]
tests/test_health.py::test_home_page_renders_successfully PASSED         [ 72%]
tests/test_health.py::test_health_endpoint_healthy PASSED                [ 76%]
tests/test_health.py::test_health_endpoint_reports_unhealthy_when_database_fails PASSED [ 80%]
tests/test_registration.py::test_successful_course_registration PASSED   [ 84%]
tests/test_registration.py::test_duplicate_registration_rejected PASSED  [ 88%]
tests/test_registration.py::test_registration_rejected_when_course_full PASSED [ 92%]
tests/test_registration.py::test_cancellation_releases_seat PASSED       [ 96%]
tests/test_registration.py::test_unauthorized_cancellation_rejected PASSED [100%]

====================== 25 passed in 18.93s =======================
```

> **Zero Test Pollution**: Tests utilize a temporary SQLite database (`tempfile.mkstemp()`). Each test function executes within an isolated transaction and removes the temporary database upon teardown.

---

## 10. Docker & Docker Compose Operations

### Option A: Using Docker Compose (Recommended)
```bash
# Build and launch application in background
docker compose up -d --build

# View real-time container logs
docker compose logs -f

# Inspect container health
docker ps

# Gracefully stop without losing student registrations
docker compose down
```

### Option B: Using Docker CLI Directly
```bash
# 1. Build image
docker build -t course-registration-platform:latest .

# 2. Create named persistent volume
docker volume create course_registration_data

# 3. Launch container with volume mount
docker run -d \
  --name course-registration-container \
  --restart unless-stopped \
  -p 5000:5000 \
  -v course_registration_data:/app/data \
  -e DATA_DIR=/app/data \
  -e FLASK_CONFIG=production \
  -e SECRET_KEY=production-secure-university-key-2026 \
  course-registration-platform:latest
```

---

## 11. Jenkins CI/CD Pipeline Setup

### 11.1 Required Jenkins Plugins
Navigate to **Manage Jenkins > Plugins > Available Plugins** and install:
1. **Pipeline** (`workflow-aggregator`)
2. **Git Plugin** (`git`)
3. **JUnit Plugin** (`junit`)
4. **AnsiColor** (`ansicolor`)

### 11.2 Host Permissions for Docker
On Linux/Ubuntu Jenkins controllers:
```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

### 11.3 Create the Pipeline Job
1. Open Jenkins (`http://localhost:8080`).
2. Click **New Item** > Name: `Course-Registration-Platform` > Select **Pipeline** > Click **OK**.
3. Under **Build Triggers**, enable **Poll SCM** with schedule: `H/5 * * * *`.
4. Under **Pipeline**:
   - Definition: **Pipeline script from SCM**
   - SCM: **Git**
   - Repository URL: `https://github.com/<YOUR_USERNAME>/course-registration-platform.git`
   - Branch: `*/main`
   - Script Path: `Jenkinsfile`
5. Click **Save**.

---

## 12. Step-by-Step Demonstration of Automated Deployment

Follow this exact scenario during viva or practical evaluation to prove that automated CI/CD deployment works:

### Phase 1: Initial Baseline Deployment
1. In Jenkins, click **Build Now**.
2. Watch all 7 stages turn green:
   - *1. Checkout GitHub Source*
   - *2. Validate Python Project and Install Dependencies*
   - *3. Run Automated Tests* (25/25 passed)
   - *4. Build Docker Image*
   - *5. Deploy New Application Version*
   - *6. Verify Application Health* (HTTP 200)
   - *7. Report Final Build Status*
3. Open `http://localhost:5000` in your browser.
4. Notice initial title: **`Course Registration Portal`**.
5. Log in as student (`student@university.edu` / `Student123!`) and enroll in a course.

### Phase 2: Demonstrate the Automated Quality Gate (Test Failure Abort)
1. Intentionally break a test in `tests/test_health.py` (e.g. change expected status to 999).
2. Commit and push:
   ```bash
   git add tests/test_health.py
   git commit -m "test: simulate failing test"
   git push origin main
   ```
3. Jenkins detects the push and runs Stage 3.
4. **Observation**: Stage 3 fails! The pipeline terminates immediately.
5. **Result**: Stages 4, 5, 6, and 7 are skipped. The live container remains running and undamaged!

### Phase 3: Demonstrate Automatic Title Update Deployment
1. Revert the test fix.
2. In `templates/index.html` (line 15), change:
   ```html
   <h1 class="display-6 fw-bold text-white mb-2" id="hero-heading">Course Registration Portal</h1>
   ```
   To:
   ```html
   <h1 class="display-6 fw-bold text-white mb-2" id="hero-heading">Student Course Registration System</h1>
   ```
3. Commit and push:
   ```bash
   git add templates/index.html tests/test_health.py
   git commit -m "feat(ui): update portal heading to Student Course Registration System"
   git push origin main
   ```
4. Observe Jenkins automatically trigger the build, pass all 25 tests, build the updated Docker image, replace the container, and verify `/health`.
5. Refresh `http://localhost:5000`:
   - The new heading **`Student Course Registration System`** is live!
   - Log into the student dashboard: **All previously enrolled courses remain completely intact** because the SQLite database volume was preserved!

---

## 13. Troubleshooting Common Issues

| Error | Root Cause | Solution |
| :--- | :--- | :--- |
| **`Permission denied: /var/run/docker.sock`** | Jenkins user lacks socket permissions | Run `sudo usermod -aG docker jenkins && sudo chmod 666 /var/run/docker.sock`. |
| **`Port 5000 is already in use`** | Previous container or process is bound to 5000 | Run `docker stop $(docker ps -q --filter "publish=5000")` or kill PID via `netstat -ano \| findstr :5000`. |
| **`OperationalError: database is locked`** | Unclosed connections in SQLite | Handled cleanly in our Application Factory using scoped SQLAlchemy session teardowns. |
| **`Health probe timeout`** | Container took longer than start period | Increase `start_period` in Dockerfile or increase retries in Stage 6 of `Jenkinsfile`. |

---

## 14. Screenshot Checklist for Project Report

- [ ] **Jenkins Pipeline Stage View**: All 7 stages showing green execution status.
- [ ] **Pytest Terminal Output**: 25 passed tests with execution timings.
- [ ] **Home Page Portal**: Hero banner with live database statistics cards.
- [ ] **Course Catalog View**: Course cards with real-time seat capacity progress bars.
- [ ] **Student Dashboard**: Enrolled courses count, registered credits, and course list.
- [ ] **Course Detail & Enrollment**: Enrollment button with CSRF token.
- [ ] **Duplicate Enrollment Warning**: Yellow flash alert blocking duplicate course registration.
- [ ] **Course Full Alert**: Red flash alert blocking registration when seats reach capacity.
- [ ] **Admin Control Center**: KPI summary cards and recent student registration feed.
- [ ] **Admin Course Edit**: Validation error preventing capacity reduction below enrolled students.
- [ ] **Health API Endpoint**: Browser showing `{"status":"healthy","database":"connected"}`.
- [ ] **Docker CLI**: `docker ps` displaying active container and port mapping.
