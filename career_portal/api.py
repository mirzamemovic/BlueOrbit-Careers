import re

from flask import Blueprint, request
from flask_jwt_extended import create_access_token, jwt_required
from flask_restful import Api, Resource

from .db import db
from .models import ApplicationModel, CompanyModel, JobModel, UserModel
from .notifier import send_application_alert
from .repositories import CareerRepository
from .services import NotFoundError, ValidationError, create_opportunity, submit_application


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_STATUSES = {"New", "Reviewed", "Interview", "Rejected", "Accepted"}


def _payload():
    return request.get_json(silent=True) or {}


def _compact_text(value):
    return " ".join(str(value or "").split())


def _required(data, fields):
    return {field: f"{field} is required." for field in fields if not _compact_text(data.get(field))}


def _bad_request(details):
    return {"error": "Validation failed.", "details": details}, 400


def _not_found(resource):
    return {"error": f"{resource} not found."}, 404


def _parse_salary(value):
    if value in (None, ""):
        return None
    try:
        salary = float(value)
    except (TypeError, ValueError):
        raise ValueError("salary must be a number.")
    if salary < 0:
        raise ValueError("salary must be zero or greater.")
    return salary


def _validate_company_payload(data, partial=False):
    errors = {} if partial else _required(data, ("name", "description"))
    payload = {}

    for field in ("name", "description"):
        if field in data:
            payload[field] = " ".join(str(data.get(field) or "").split())
            if not payload[field]:
                errors[field] = f"{field} is required."

    if payload.get("name"):
        query = CompanyModel.query.filter_by(name=payload["name"])
        existing = query.first()
        if existing and existing.id != data.get("id"):
            errors["name"] = "Company name already exists."

    return payload, errors


def _validate_job_payload(data, partial=False):
    required = ("title", "description", "company_id", "location")
    errors = {} if partial else _required(data, required)
    payload = {}

    for field in ("title", "description", "location", "category", "work_mode", "salary_range"):
        if field in data:
            payload[field] = " ".join(str(data.get(field) or "").split())
            if field in required and not payload[field]:
                errors[field] = f"{field} is required."

    if "company_id" in data:
        try:
            payload["company_id"] = int(data["company_id"])
        except (TypeError, ValueError):
            errors["company_id"] = "company_id must be an integer."
        else:
            if db.session.get(CompanyModel, payload["company_id"]) is None:
                errors["company_id"] = "Company not found."

    if "salary" in data:
        try:
            payload["salary"] = _parse_salary(data["salary"])
        except ValueError as exc:
            errors["salary"] = str(exc)

    return payload, errors


def _validate_application_payload(data, partial=False):
    required = ("candidate_name", "email", "job_id")
    errors = {} if partial else _required(data, required)
    payload = {}

    for field in ("candidate_name", "email", "status", "resume_link"):
        if field in data:
            payload[field] = " ".join(str(data.get(field) or "").split())
            if field in required and not payload[field]:
                errors[field] = f"{field} is required."

    if payload.get("email"):
        payload["email"] = payload["email"].lower()
        if not EMAIL_PATTERN.match(payload["email"]):
            errors["email"] = "A valid email is required."

    if payload.get("status") and payload["status"] not in VALID_STATUSES:
        errors["status"] = "Status must be New, Reviewed, Interview, Rejected, or Accepted."

    if "job_id" in data:
        try:
            payload["job_id"] = int(data["job_id"])
        except (TypeError, ValueError):
            errors["job_id"] = "job_id must be an integer."
        else:
            if db.session.get(JobModel, payload["job_id"]) is None:
                errors["job_id"] = "Job not found."

    if payload.get("resume_link") and not payload["resume_link"].startswith(("http://", "https://")):
        errors["resume_link"] = "resume_link must start with http:// or https://."

    return payload, errors


class RegisterResource(Resource):
    def post(self):
        data = _payload()
        errors = _required(data, ("username", "password"))
        username = _compact_text(data.get("username"))
        password = str(data.get("password") or "")

        if username and UserModel.query.filter_by(username=username).first():
            errors["username"] = "Username already exists."
        if password and len(password) < 6:
            errors["password"] = "Password must be at least 6 characters."
        if errors:
            return _bad_request(errors)

        user = UserModel(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.to_dict(), 201


class LoginResource(Resource):
    def post(self):
        data = _payload()
        errors = _required(data, ("username", "password"))
        username = _compact_text(data.get("username"))
        if errors:
            return _bad_request(errors)

        user = UserModel.query.filter_by(username=username).first()
        if user is None or not user.check_password(data["password"]):
            return {"error": "Invalid username or password."}, 401

        return {"access_token": create_access_token(identity=str(user.id)), "user": user.to_dict()}, 200


class CompaniesResource(Resource):
    def get(self):
        return {"items": [company.to_dict() for company in CompanyModel.query.order_by(CompanyModel.id).all()]}

    @jwt_required()
    def post(self):
        data, errors = _validate_company_payload(_payload())
        if errors:
            return _bad_request(errors)

        company = CompanyModel(**data)
        db.session.add(company)
        db.session.commit()
        return company.to_dict(), 201


class CompanyResource(Resource):
    def get(self, company_id):
        company = db.session.get(CompanyModel, company_id)
        if company is None:
            return _not_found("Company")
        return company.to_dict(include_jobs=True)

    @jwt_required()
    def put(self, company_id):
        company = db.session.get(CompanyModel, company_id)
        if company is None:
            return _not_found("Company")

        data = {**_payload(), "id": company_id}
        payload, errors = _validate_company_payload(data, partial=True)
        if errors:
            return _bad_request(errors)

        for key, value in payload.items():
            setattr(company, key, value)
        db.session.commit()
        return company.to_dict()

    @jwt_required()
    def delete(self, company_id):
        company = db.session.get(CompanyModel, company_id)
        if company is None:
            return _not_found("Company")

        db.session.delete(company)
        db.session.commit()
        return {"message": "Company deleted."}


class JobsResource(Resource):
    def get(self):
        jobs = JobModel.query.order_by(JobModel.id).all()
        return {"items": [job.to_dict() for job in jobs]}

    @jwt_required()
    def post(self):
        payload, errors = _validate_job_payload(_payload())
        if errors:
            return _bad_request(errors)

        job = JobModel(**payload)
        db.session.add(job)
        db.session.commit()
        return job.to_dict(), 201


class JobResource(Resource):
    def get(self, job_id):
        job = db.session.get(JobModel, job_id)
        if job is None:
            return _not_found("Job")
        return job.to_dict(include_applications=True)

    @jwt_required()
    def put(self, job_id):
        job = db.session.get(JobModel, job_id)
        if job is None:
            return _not_found("Job")

        payload, errors = _validate_job_payload(_payload(), partial=True)
        if errors:
            return _bad_request(errors)

        for key, value in payload.items():
            setattr(job, key, value)
        db.session.commit()
        return job.to_dict()

    @jwt_required()
    def delete(self, job_id):
        job = db.session.get(JobModel, job_id)
        if job is None:
            return _not_found("Job")

        db.session.delete(job)
        db.session.commit()
        return {"message": "Job deleted."}


class ApplicationsResource(Resource):
    def get(self):
        applications = ApplicationModel.query.order_by(ApplicationModel.id).all()
        return {"items": [application.to_dict() for application in applications]}

    @jwt_required()
    def post(self):
        payload, errors = _validate_application_payload(_payload())
        if errors:
            return _bad_request(errors)

        application = ApplicationModel(**payload)
        db.session.add(application)
        db.session.commit()
        return application.to_dict(), 201


class ApplicationResource(Resource):
    def get(self, application_id):
        application = db.session.get(ApplicationModel, application_id)
        if application is None:
            return _not_found("Application")
        return application.to_dict()

    @jwt_required()
    def put(self, application_id):
        application = db.session.get(ApplicationModel, application_id)
        if application is None:
            return _not_found("Application")

        payload, errors = _validate_application_payload(_payload(), partial=True)
        if errors:
            return _bad_request(errors)

        for key, value in payload.items():
            setattr(application, key, value)
        db.session.commit()
        return application.to_dict()

    @jwt_required()
    def delete(self, application_id):
        application = db.session.get(ApplicationModel, application_id)
        if application is None:
            return _not_found("Application")

        db.session.delete(application)
        db.session.commit()
        return {"message": "Application deleted."}


class LegacyOpportunitiesResource(Resource):
    def get(self):
        return {"items": CareerRepository().list_opportunities()}

    @jwt_required()
    def post(self):
        try:
            opportunity = create_opportunity(CareerRepository(), _payload())
        except ValidationError as exc:
            return _bad_request(exc.errors)
        return opportunity, 201


class LegacyOpportunityResource(Resource):
    def get(self, opportunity_id):
        opportunity = CareerRepository().get_opportunity(opportunity_id)
        if opportunity is None:
            return {"error": "Opportunity not found."}, 404
        return opportunity


class LegacyApplicationsResource(Resource):
    def get(self):
        return {"items": CareerRepository().list_applications()}


class LegacyApplyResource(Resource):
    @jwt_required()
    def post(self, opportunity_id):
        try:
            application = submit_application(CareerRepository(), opportunity_id, _payload(), send_application_alert)
        except ValidationError as exc:
            return _bad_request(exc.errors)
        except NotFoundError as exc:
            return {"error": str(exc)}, 404
        return application, 201


def create_api_blueprint(name="api"):
    blueprint = Blueprint(name, __name__)
    api = Api(blueprint)

    api.add_resource(RegisterResource, "/register")
    api.add_resource(LoginResource, "/login")
    api.add_resource(CompaniesResource, "/companies", "/company")
    api.add_resource(CompanyResource, "/company/<int:company_id>")
    api.add_resource(JobsResource, "/jobs", "/job")
    api.add_resource(JobResource, "/job/<int:job_id>")
    api.add_resource(ApplicationsResource, "/applications", "/application")
    api.add_resource(ApplicationResource, "/application/<int:application_id>")

    api.add_resource(LegacyOpportunitiesResource, "/opportunities")
    api.add_resource(LegacyOpportunityResource, "/opportunities/<int:opportunity_id>")
    api.add_resource(LegacyApplicationsResource, "/legacy-applications")
    api.add_resource(LegacyApplyResource, "/opportunities/<int:opportunity_id>/apply")
    return blueprint


api_bp = create_api_blueprint()
