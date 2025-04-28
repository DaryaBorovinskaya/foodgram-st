# Пример из проекта api_final_yatube

# from django.urls import include, path
# from api.views import CommentViewSet, GroupViewSet, 
# PostViewSet, FollowViewSet
# from rest_framework import routers


# router = routers.DefaultRouter()
# router.register(r'groups', GroupViewSet)
# router.register(r'posts', PostViewSet)
# router.register(r'follow', FollowViewSet)

# urlpatterns = [
#     path("", include(router.urls)),
#     path(
#         "posts/<int:post_id>/comments/",
#         CommentViewSet.as_view({"get": "list", "post": "create"}),
#         name="post_comments",
#     ),
#     path(
#         "posts/<int:post_id>/comments/<int:pk>/",
#         CommentViewSet.as_view(
#             {"get": "retrieve", "put": "update", "delete": "destroy",
#              "patch": "partial_update"}
#         ),
#         name="post_comment_detail",
#     ),
#     path('', include('djoser.urls')),
#     path('', include('djoser.urls.jwt')),
# ]
