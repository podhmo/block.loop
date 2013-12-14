from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config
from functools import partial
from sqlalchemy.exc import DBAPIError
import sqlalchemy as sa
from .models import (
    DBSession,
    MyModel,
    User
    )

from block.loop import view_loop, ViewFromLoopForLazy

def create_model(c, model=None):
    obj = model()
    for k, v in c.request.POST.items():
        setattr(obj, k, v)
    c.obj = obj

def add_session(c, name="obj"):
    DBSession.add(getattr(c, name))

def get_model_list(c, model=None, order_by=None):
    models = DBSession.query(model)
    if order_by is not None:
        models = models.order_by(order_by)
    c.models = models

def success_redirect(c, message=None, route_name=None):
    c.request.session.flash(message.format(obj=c.obj))
    return HTTPFound(c.request.route_url(route_name))

def add_form(c, form):
    c.form = form.format(action=c.request.current_route_path(), method="POST") #fixme

loop = (view_loop()
        .add(partial(create_model, model=User))
        .add(partial(add_session))
        .add(partial(success_redirect, message="user: {obj.name} is created.", route_name="user.create"))
)
user_create = view_config(route_name="user.create", request_method="POST", renderer='input.mako')(ViewFromLoopForLazy(loop, "create_user"))

user_form = """
<form action="{action}" method="{method}">
  <input name="name" type="text" value=""/>
  <input type="submit"/>
</form>
"""

loop = (view_loop() 
        .add(partial(get_model_list, model=User, order_by=sa.asc(User.name)))
        .add(partial(add_form, form=user_form))
)
user_create_input = view_config(route_name="user.create", request_method="GET", renderer='input.mako')(ViewFromLoopForLazy(loop, "create_user_input"))



@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    try:
        one = DBSession.query(MyModel).filter(MyModel.name == 'one').first()
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    return {'one': one, 'project': 'sample'}

conn_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to run the "initialize_sample_db" script
    to initialize your database tables.  Check your virtual 
    environment's "bin" directory for this script and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""

