from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from functools import partial
import sqlalchemy as sa
from .models import (
    DBSession,
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
