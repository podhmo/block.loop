block.loop
----------------------------------------

a experimental approach, creating pyramid's view via method chain.

sample ::

    from block.loop import view_loop, ViewFromLoop
    from .schema import UserSchema
    from .models import User

    loop = (view_oop()
     .add(get_model(model=User)), 
     .add(schema_validation(schema=UserSchema)), 
     .add(update_user))
    update_user_view = view_config(route_name="user.update", request_method="POST")(ViewFromLoop(loop))

