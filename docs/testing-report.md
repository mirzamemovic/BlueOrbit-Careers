# Testing Report

## 1. Project overview

This project implements a career opportunity management web application called **BlueOrbit Careers**. The application allows users to publish job opportunities, submit applications, and interact with the system through both a visual dashboard and REST API endpoints.

## 2. Technical stack

- Python 3.13
- Flask for the web application and REST endpoints
- SQLite for persistence
- Pytest for automated testing
- `unittest.mock` for mocks and patches

## 3. Functional scope

The application supports:

- Opportunity creation through the dashboard
- Opportunity creation through the REST API
- Candidate applications through the dashboard
- Candidate applications through the REST API
- Opportunity and application listing

## 4. Architecture summary

The implementation is split into clear layers:

- `views.py` handles HTML page routes and form submissions
- `api.py` handles JSON REST endpoints
- `services.py` centralizes validation and workflow logic
- `repositories.py` manages database queries
- `db.py` initializes schema and seed data
- `notifier.py` represents an external notification dependency that can be mocked

This structure was chosen so the same business logic can be exercised through both the UI and the API, which also improves testability.

## 5. Testing strategy

The test plan follows the assignment requirement to cover unit, integration, system, and REST API testing.

### Unit tests

Unit tests focus on isolated behavior in `services.py`:

- Input validation for opportunity creation
- Input validation for applications
- Dashboard metric generation
- Submission workflow behavior with a mocked notifier

These tests ensure business rules work independently of the database or Flask request cycle.

### Integration tests

Integration tests validate that the repository layer works correctly with the SQLite database:

- Opportunity persistence
- Application persistence
- Joined data retrieval between applications and opportunities
- Correct application counts on roles

These tests verify that the database schema and repository queries behave correctly together.

### System tests

System tests use Flask's test client to simulate end-to-end browser-like flows:

- Load the homepage and verify branding and initial content
- Publish a role through the dashboard form
- Submit an application through the dashboard form

These tests cover the application from route to template rendering to persistence.

### REST API tests

REST API tests validate endpoint behavior and response handling:

- List opportunities
- Create opportunities
- Submit applications
- Return 404 for missing roles
- Return 400 for invalid payloads

This confirms API reliability, validation, and error handling.

## 6. Mocks and patches

The assignment explicitly requires the use of mocks and patches. The project includes that in two ways:

- A mocked notifier is used in unit tests to confirm application submission triggers the expected dependency call
- A patched notifier is used in API tests so the endpoint logic can be tested without relying on a real messaging service

This isolates business behavior from external side effects and keeps the tests deterministic.

## 7. Design choices

The interface was intentionally designed to match the requested style:

- Main colors are black and blue
- Cards, inputs, and buttons use rounded shapes
- Text is kept concise
- The layout uses glass panels, blue glow accents, and a modern dashboard structure

## 8. Challenges and solutions

### Challenge: keeping the app easy to test

Solution:
The business rules were moved into a dedicated service layer so the same workflow could be tested through direct unit tests, HTML routes, and API routes.

### Challenge: covering several testing types without overcomplicating the stack

Solution:
Flask with a structured repository and service layer made it possible to cover all required test categories cleanly while keeping the project lightweight and understandable.

### Challenge: handling external behavior in tests

Solution:
A notifier abstraction was introduced so mocks and patches could be used in a meaningful way during application submission testing.

## 9. Expected outcomes

The completed solution demonstrates:

- A functioning Python web application
- A REST API designed with testing in mind
- Clear separation of concerns
- Automated coverage for all required testing levels
- Documentation suitable for submission alongside the source code

## 10. Verified execution result

The automated suite was executed successfully on **June 3, 2026** and all tests passed.

- Total tests passed: 22
- Covered areas: unit, integration, system, and REST API testing
- Mock and patch scenarios: included and verified
- JWT protection for mutating REST requests: included and verified

## 11. How to execute

Run the application:

```bash
python app.py
```

Run all tests:

```bash
python -m pytest
```

Run by category:

```bash
python -m pytest tests/unit
python -m pytest tests/integration
python -m pytest tests/system
```

## 12. Deliverables checklist

- Web application source code
- REST API implementation
- Automated test suite
- Mock and patch usage
- Documentation and report
- Postman collection and environment
- Screenshots of passing pytest/Postman runs for final submission
