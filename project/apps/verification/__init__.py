from flask import Blueprint

verify_blueprint = Blueprint('verification', __name__, url_prefix='/verification')

from . import views
