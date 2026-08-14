from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import ChartOfAccount, JournalEntry, JournalItem, Transaction

@admin.register(ChartOfAccount)
class ChartOfAccountAdmin(ModelAdmin):
    list_display = ('code', 'name', 'account_type', 'is_active')
    search_fields = ('code', 'name')
    list_filter = ('account_type', 'is_active')

@admin.register(JournalEntry)
class JournalEntryAdmin(ModelAdmin):
    list_display = ('journal_code', 'date', 'created_at')
    search_fields = ('journal_code', 'description')
    list_filter = ('date',)

@admin.register(JournalItem)
class JournalItemAdmin(ModelAdmin):
    list_display = ('journal', 'account', 'debit', 'credit')
    search_fields = ('journal__journal_code', 'account__name')
    list_filter = ('account__account_type',)

@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = ('transaction_code', 'date', 'amount', 'created_at')
    search_fields = ('transaction_code', 'description')
    list_filter = ('date',)