from unittest.mock import Mock

import pytest

from career_portal.services import ValidationError
from career_portal.services import build_dashboard_metrics
from career_portal.services import submit_application
from career_portal.services import validate_application_payload
from career_portal.services import validate_opportunity_payload


class FakeRepo:
    def __init__(self):
        self.opportunity = {
            "id": 7,
            "title": "QA Engineer",
            "company": "BlueOrbit Labs",
            "is_active": 1,
        }
        self.saved_application = None

    def get_opportunity(self, opportunity_id):
        if opportunity_id == self.opportunity["id"]:
            return self.opportunity
        return None

    def create_application(self, payload):
        self.saved_application = {**payload, "id": 11}
        return self.saved_application


def test_validate_opportunity_payload_cleans_and_accepts_valid_data():
    payload, errors = validate_opportunity_payload(
        {
            "title": "  QA Engineer  ",
            "company": " BlueOrbit Labs ",
            "location": " Remote ",
            "category": " Quality Engineering ",
            "work_mode": "Remote",
            "salary_range": " EUR 1k - 2k ",
            "summary": "  Build clean automated checks across critical release flows.  ",
        }
    )

    assert errors == {}
    assert payload["title"] == "QA Engineer"
    assert payload["summary"].startswith("Build clean automated checks")


def test_validate_application_payload_rejects_bad_email_and_short_motivation():
    _payload, errors = validate_application_payload(
        {
            "applicant_name": "Ava",
            "applicant_email": "bad-email",
            "portfolio_url": "portfolio.local",
            "motivation": "Too short",
        }
    )

    assert "applicant_email" in errors
    assert "portfolio_url" in errors
    assert "motivation" in errors


def test_build_dashboard_metrics_counts_roles_companies_and_remote_ready():
    metrics = build_dashboard_metrics(
        [
            {"company": "BlueOrbit Labs", "work_mode": "Remote"},
            {"company": "BlueOrbit Labs", "work_mode": "Hybrid"},
            {"company": "Northline Studio", "work_mode": "On-site"},
        ],
        9,
    )

    assert metrics == {
        "live_roles": 3,
        "companies": 2,
        "applications": 9,
        "remote_ready": 2,
    }


def test_submit_application_calls_notifier_with_saved_application():
    repo = FakeRepo()
    alert_sender = Mock()

    application = submit_application(
        repo,
        7,
        {
            "applicant_name": "Mila Hart",
            "applicant_email": "mila@example.com",
            "portfolio_url": "https://portfolio.example.com",
            "motivation": "I ship reliable automated coverage across web and API layers.",
        },
        alert_sender,
    )

    assert application["id"] == 11
    alert_sender.assert_called_once()
    saved_payload = repo.saved_application
    assert saved_payload["applicant_email"] == "mila@example.com"
    assert saved_payload["opportunity_id"] == 7


def test_submit_application_raises_validation_error_for_invalid_payload():
    repo = FakeRepo()

    with pytest.raises(ValidationError):
        submit_application(
            repo,
            7,
            {
                "applicant_name": "",
                "applicant_email": "invalid",
                "portfolio_url": "",
                "motivation": "short",
            },
            Mock(),
        )
