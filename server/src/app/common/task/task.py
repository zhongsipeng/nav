# from celery import shared_task

# from ...core.extensions import db
# from ...model.entities import Collect
# from ..icon_download import get_favicon_as_base64


# @shared_task(rate_limit="6/m")
# def example_task():
#     print("This is an example task.")


# @shared_task()
# def update_icon(id):
#     data = Collect.query.get(id)
#     if data and data.type == "bookmark":
#         data.icon = get_favicon_as_base64(data.url)
#         if data.icon:
#             db.session.commit()
