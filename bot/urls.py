from django.urls import path
from django.conf import settings
from . import views

urlpatterns = [
    path(settings.TELEGRAM_WEBHOOK_PATH, views.telegram_webhook, name="webhook"),
    path('create-deposit/<int:telegram_id>/<int:amount>/<str:bank_code>/<str:token>/', views.create_deposit_view, name="create_deposit"),
    path('create-withdraw/<int:telegram_id>/<str:currency>/<int:amount>/<str:address>/<int:network_id>/<str:token>/', views.create_withdrawal_view, name="create_withdraw"),
]