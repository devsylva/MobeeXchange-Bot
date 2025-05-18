from django.contrib import admin
from .models import TelegramUser, DepositRequest, WithdrawalRequest

# Register your models here.
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'username', 'first_name', 'last_name', 
                   'balance', 'created_at')
    search_fields = ('telegram_id', 'username', 'first_name', 'last_name')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


class DepositRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'deposit_id', 'transaction_id', 'amount', 
                   'status', 'created_at')
    search_fields = ('user__username', 'deposit_id', 'transaction_id')
    list_filter = ('status', 'user__username')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ('data', 'currency', 'amount', 'address', 
                   'txn_hash', 'created_at', 'status')
    search_fields = ('data', 'currency', 'address')
    list_filter = ('status',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


admin.site.register(TelegramUser, TelegramUserAdmin)
admin.site.register(DepositRequest, DepositRequestAdmin)
admin.site.register(WithdrawalRequest)