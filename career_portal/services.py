import re


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(Exception):
    def __init__(self, errors):
        super().__init__("Validation failed.")
        self.errors = errors


class NotFoundError(Exception):
    pass


def compact_text(value):
    return " ".join((value or "").split())


def validate_opportunity_payload(raw_data):
    payload = {
        "title": compact_text(raw_data.get("title")),
        "company": compact_text(raw_data.get("company")),
        "location": compact_text(raw_data.get("location")),
        "category": compact_text(raw_data.get("category")),
        "work_mode": compact_text(raw_data.get("work_mode")),
        "salary_range": compact_text(raw_data.get("salary_range")),
        "summary": compact_text(raw_data.get("summary")),
    }

    errors = {}
    for field in ("title", "company", "location", "category", "work_mode", "summary"):
        if not payload[field]:
            errors[field] = f"{field.replace('_', ' ').title()} is required."

    if payload["summary"] and len(payload["summary"]) < 24:
        errors["summary"] = "Summary should be at least 24 characters."

    if payload["salary_range"] and len(payload["salary_range"]) > 32:
        errors["salary_range"] = "Salary range should stay short and readable."

    if payload["work_mode"] and payload["work_mode"] not in {"Remote", "Hybrid", "On-site"}:
        errors["work_mode"] = "Work mode must be Remote, Hybrid, or On-site."

    return payload, errors


def validate_application_payload(raw_data):
    payload = {
        "applicant_name": compact_text(raw_data.get("applicant_name")),
        "applicant_email": compact_text(raw_data.get("applicant_email")).lower(),
        "portfolio_url": compact_text(raw_data.get("portfolio_url")),
        "motivation": compact_text(raw_data.get("motivation")),
    }

    errors = {}

    if not payload["applicant_name"]:
        errors["applicant_name"] = "Applicant name is required."

    if not payload["applicant_email"] or not EMAIL_PATTERN.match(payload["applicant_email"]):
        errors["applicant_email"] = "A valid email is required."

    if payload["portfolio_url"] and not payload["portfolio_url"].startswith(("http://", "https://")):
        errors["portfolio_url"] = "Portfolio URL must start with http:// or https://."

    if not payload["motivation"] or len(payload["motivation"]) < 16:
        errors["motivation"] = "Motivation should be at least 16 characters."

    return payload, errors


def build_dashboard_metrics(opportunities, application_total):
    live_roles = len(opportunities)
    companies = len({item["company"] for item in opportunities})
    remote_ready = sum(1 for item in opportunities if item["work_mode"] in {"Remote", "Hybrid"})

    return {
        "live_roles": live_roles,
        "companies": companies,
        "applications": application_total,
        "remote_ready": remote_ready,
    }


def create_opportunity(repo, raw_data):
    payload, errors = validate_opportunity_payload(raw_data)
    if errors:
        raise ValidationError(errors)
    return repo.create_opportunity(payload)


def submit_application(repo, opportunity_id, raw_data, alert_sender):
    opportunity = repo.get_opportunity(opportunity_id)
    if opportunity is None or not opportunity["is_active"]:
        raise NotFoundError("Opportunity not found.")

    payload, errors = validate_application_payload(raw_data)
    if errors:
        raise ValidationError(errors)

    application = repo.create_application(
        {
            **payload,
            "opportunity_id": opportunity_id,
        }
    )
    alert_sender(application, opportunity)
    return application
