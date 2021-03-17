from .views import (
    user_login_endpoint,
)
from django.urls import path


urlpatterns = [
    path('login', user_login_endpoint),
]