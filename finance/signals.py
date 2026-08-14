from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaction, JournalEntry, JournalItem, ChartOfAccount

@receiver(post_save, sender=Transaction)
def create_transaction_journal(sender, instance, created, **kwargs):
    if created and not instance.journal_entry:
        # 1. Buat Header Jurnal Otomatis
        je = JournalEntry.objects.create(
            journal_code=f"JE-{instance.transaction_code}",
            date=instance.date,
            description=f"Auto-journal for transaction: {instance.description or instance.transaction_code}"
        )
        instance.journal_entry = je
        instance.save(update_fields=['journal_entry'])

        # 2. Tentukan Akun Debet & Kredit Berdasarkan Tipe Transaksi
        # Pastikan Anda sudah membuat Chart of Account dengan kode '1101' (Kas), '4101' (Pendapatan), dan '5101' (Beban) di admin
        if instance.transaction_type == 'INCOME':
            cash_account = ChartOfAccount.objects.filter(code='1101').first()
            revenue_account = ChartOfAccount.objects.filter(code='4101').first()
            
            if cash_account and revenue_account:
                JournalItem.objects.create(journal=je, account=cash_account, debit=instance.amount, credit=0)
                JournalItem.objects.create(journal=je, account=revenue_account, debit=0, credit=instance.amount)

        elif instance.transaction_type == 'EXPENSE':
            expense_account = ChartOfAccount.objects.filter(code='5101').first()
            cash_account = ChartOfAccount.objects.filter(code='1101').first()
            
            if expense_account and cash_account:
                JournalItem.objects.create(journal=je, account=expense_account, debit=instance.amount, credit=0)
                JournalItem.objects.create(journal=je, account=cash_account, debit=0, credit=instance.amount)