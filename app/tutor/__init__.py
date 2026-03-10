from flask import Blueprint
tutor_bp = Blueprint('tutor', __name__)
from app.tutor import routes
