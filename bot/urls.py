from django.urls import path
from django.conf import settings
from . import views

urlpatterns = [
    path(settings.TELEGRAM_WEBHOOK_PATH, views.telegram_webhook, name="webhook"),
    path('create-deposit/<int:telegram_id>/<int:amount>/<str:bank_code>/', views.create_deposit_view, name="create_deposit"),
]