from django.db import models

class ChartOfAccount(models.Model):
    ACCOUNT_TYPES = (
        ('ASSET', 'Aset'),
        ('LIABILITY', 'Kewajiban'),
        ('EQUITY', 'Ekuitas'),
        ('REVENUE', 'Pendapatan'),
        ('EXPENSE', 'Beban'),
    )
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    account_type = models.CharField(choices=ACCOUNT_TYPES, max_length=20)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"[{self.code}] {self.name}"

class JournalEntry(models.Model):
    journal_code = models.CharField(max_length=100, unique=True)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"JE {self.journal_code} - {self.date}"

class JournalItem(models.Model):
    journal = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='items')
    account = models.ForeignKey(ChartOfAccount, on_delete=models.PROTECT, related_name='journal_items')
    debit = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.account.name} (Dr: {self.debit} | Cr: {self.credit})"

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('INCOME', 'Pemasukan'),
        ('EXPENSE', 'Pengeluaran'),
    )
    transaction_code = models.CharField(max_length=100, unique=True)
    date = models.DateField()
    transaction_type = models.CharField(choices=TRANSACTION_TYPES, max_length=20, default='INCOME')
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    
    # Hubungkan ke JournalEntry secara opsional
    journal_entry = models.OneToOneField(JournalEntry, on_delete=models.SET_NULL, blank=True, null=True, related_name='transaction')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"

    def __str__(self):
        return f"TRX {self.transaction_code} - {self.amount}"