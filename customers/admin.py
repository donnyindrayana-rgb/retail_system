from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    # Menyusun field ke dalam card/fieldsets yang terstruktur
    fieldsets = (
        ("Informasi Personal & Kontak", {
            "fields": (
                "name",
                ("phone", "email"),  # Field dalam tuple akan tampil sejajar dalam satu baris
            ),
        }),
        ("Alamat Pengiriman / Domisili", {
            "fields": (
                "address",
            ),
        }),
    )
    
    list_display = ("name", "phone", "email")
    search_fields = ("name", "phone", "email")