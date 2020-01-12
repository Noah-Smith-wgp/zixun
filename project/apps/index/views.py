from . import index_buleprint


@index_buleprint.route('/')
def index():
    return 'index~~'
