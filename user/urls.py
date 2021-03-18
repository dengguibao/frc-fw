from .views import (
    user_login_endpoint,
    set_user_endpoint,
    change_password_endpoint
)
from django.urls import path


urlpatterns = [
    path('login', user_login_endpoint),
    path('changePassword', change_password_endpoint),
    path('user', set_user_endpoint),
]