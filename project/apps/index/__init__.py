from flask import Blueprint

index_buleprint = Blueprint('index', __name__)

from . import views
