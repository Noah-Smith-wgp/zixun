from flask import Blueprint

verify_buleprint = Blueprint('verification', __name__, url_prefix='/verification')

from . import views
