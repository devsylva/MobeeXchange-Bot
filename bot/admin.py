from django.contrib import admin
from .models import TelegramUser, CryptoAddress, FAQ, Transaction

# Register your models here.
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'username', 'first_name', 'last_name', 
                   'balance', 'created_at')
    search_fields = ('telegram_id', 'username', 'first_name', 'last_name')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


admin.site.register(TelegramUser, TelegramUserAdmin)
admin.site.register(CryptoAddress)
admin.site.register(FAQ)
admin.site.register(Transaction)