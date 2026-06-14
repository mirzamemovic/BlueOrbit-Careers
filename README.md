# BlueOrbit Careers

BlueOrbit Careers is a Flask career opportunity management application for the Software Testing course assignment. It includes a small HTML dashboard plus a JWT-protected REST API for users, companies, jobs, and applications.

## Technology Stack

- Python 3.13
- Flask
- Flask-RESTful
- Flask-JWT-Extended
- Flask-SQLAlchemy
- SQLite
- Pytest

## Project Structure

```text
career_portal/
  __init__.py
  api.py
  db.py
  models.py
  repositories.py
  services.py
  schema.sql
  templates/
  static/
tests/
  unit/
  integration/
docs/
app.py
BlueOrbit_Careers.postman_collection.json
BlueOrbit_Careers.postman_environment.json
requirements.txt
```

## Installation

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Database Initialization

The application uses SQLite. Tables are created automatically on startup with `db.create_all()`.

By default, the local database is created at:

```text
instance/blueorbit.sqlite3
```

No manual migration command is required for a clean run.

## Run the Application

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

Health check:

```text
GET /health
```

## Authentication

Register:

```text
POST /register
```

Login:

```text
POST /login
```

The login response returns an `access_token`. Send it on protected POST, PUT, and DELETE requests:

```text
Authorization: Bearer <access_token>
```

GET endpoints are public.

## REST API

Users:

- `POST /register`
- `POST /login`

Companies:

- `GET /companies`
- `GET /company/<id>`
- `POST /company`
- `PUT /company/<id>`
- `DELETE /company/<id>`

Jobs:

- `GET /jobs`
- `GET /job/<id>`
- `POST /job`
- `PUT /job/<id>`
- `DELETE /job/<id>`

Applications:

- `GET /applications`
- `GET /application/<id>`
- `POST /application`
- `PUT /application/<id>`
- `DELETE /application/<id>`

The older dashboard API routes under `/api/opportunities` are still available for compatibility, but mutating requests also require JWT.

## Model Extension

`JobModel` was extended with a required `location` field. The field is included in:

- SQLAlchemy model
- SQLite schema reference
- API validation
- JSON serializers
- request payloads
- unit tests
- integration tests
- Postman tests

## Run Tests

Run all tests:

```powershell
python -m pytest
```

Run only unit tests:

```powershell
python -m pytest tests/unit
```

Run only integration tests:

```powershell
python -m pytest tests/integration
```

Run only system tests:

```powershell
python -m pytest tests/system
```

The test app uses an isolated SQLite database in `tests_runtime/`.

## Postman Testing

Import these files into Postman:

- `BlueOrbit_Careers.postman_collection.json`
- `BlueOrbit_Careers.postman_environment.json`

Select the `BlueOrbit Careers Local` environment and run the collection in order.

The collection:

- registers a user
- logs in and stores the JWT with `pm.environment.set("jwt_token", ...)`
- creates, reads, updates, and deletes companies
- creates, reads, updates, and deletes jobs
- verifies the `location` field
- creates, reads, updates, and deletes applications
- verifies single-resource detail endpoints
- verifies protected write requests fail without a JWT
- checks status codes, response time, and JSON fields

## API Behavior

- Database tables are created automatically when `create_app()` runs.
- POST, PUT, and DELETE REST operations require JWT authentication.
- Validation errors return `400 Bad Request`.
- Missing records return `404 Not Found`.
- Missing or invalid tokens return `401 Unauthorized`.
- The existing dashboard behavior was preserved while adding the assignment API.
