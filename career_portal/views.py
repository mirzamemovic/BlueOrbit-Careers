from flask import Blueprint, flash, redirect, render_template, request, url_for

from .db import get_db
from .notifier import send_application_alert
from .repositories import CareerRepository
from .services import NotFoundError
from .services import ValidationError
from .services import build_dashboard_metrics
from .services import create_opportunity
from .services import submit_application


web_bp = Blueprint("web", __name__)


def _repo():
    return CareerRepository(get_db())


def _api_reference():
    return [
        {"method": "GET", "path": "/api/opportunities"},
        {"method": "POST", "path": "/api/opportunities"},
        {"method": "GET", "path": "/api/applications"},
        {"method": "POST", "path": "/api/opportunities/<id>/apply"},
    ]


def _context():
    repo = _repo()
    opportunities = repo.list_opportunities()
    recent_applications = repo.list_recent_applications()
    metrics = build_dashboard_metrics(opportunities, repo.count_applications())
    return {
        "opportunities": opportunities,
        "recent_applications": recent_applications,
        "metrics": metrics,
        "api_reference": _api_reference(),
    }


@web_bp.get("/")
def index():
    return render_template("index.html", **_context())


@web_bp.post("/opportunities")
def create_opportunity_route():
    repo = _repo()
    anchor = "launch"
    try:
        opportunity = create_opportunity(repo, request.form)
    except ValidationError as exc:
        flash(next(iter(exc.errors.values())), "error")
    else:
        flash("Role launched.", "success")
        anchor = f"opportunity-{opportunity['id']}"

    return redirect(url_for("web.index", _anchor=anchor))


@web_bp.post("/opportunities/<int:opportunity_id>/apply")
def apply_route(opportunity_id):
    repo = _repo()
    anchor = f"opportunity-{opportunity_id}"
    try:
        submit_application(repo, opportunity_id, request.form, send_application_alert)
    except ValidationError as exc:
        flash(next(iter(exc.errors.values())), "error")
    except NotFoundError as exc:
        flash(str(exc), "error")
    else:
        flash("Application received.", "success")
        anchor = "activity"

    return redirect(url_for("web.index", _anchor=anchor))
