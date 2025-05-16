from django.urls import path
from django.conf import settings
from . import views

urlpatterns = [
    path(settings.TELEGRAM_WEBHOOK_PATH, views.telegram_webhook, name="webhook"),
]