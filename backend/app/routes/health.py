from flask import Blueprint

health_bp = Blueprint("health", __name__)


@health_bp.get("/")
def index():
    return {"message": "running"}, 200


@health_bp.get("/health")
def health_check():
    return {"status": "ok"}, 200
