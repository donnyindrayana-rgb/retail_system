# merchandise/admin.py
from django.contrib import admin
from django.db import models
from django.shortcuts import render
from django.urls import path
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from operations.models import DamageGoods, StockSnapshot
from .models import (
    Category,
    Dept,
    Divisi,
    Item,
    PurchaseOrder,
    PurchaseOrderItem,
    SubCategory,
    Supplier,
)


# ==========================================
# 1. CATEGORY MANAGEMENT GROUP
# ==========================================

@admin.register(Divisi)
class DivisiAdmin(ModelAdmin):
    list_display = ('kode_divisi', 'nama_divisi')
    search_fields = ('kode_divisi', 'nama_divisi')
    ordering = ('kode_divisi',)


@admin.register(Dept)
class DeptAdmin(ModelAdmin):
    list_display = ('kode_dept', 'nama_dept', 'divisi')
    list_filter = ('divisi',)
    search_fields = ('kode_dept', 'nama_dept')
    ordering = ('kode_dept',)


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('kode_category', 'nama_category', 'dept')
    list_filter = ('dept__divisi', 'dept')
    search_fields = ('kode_category', 'nama_category')
    ordering = ('kode_category',)


@admin.register(SubCategory)
class SubCategoryAdmin(ModelAdmin):
    list_display = ('kode_sub', 'nama_sub', 'category')
    list_filter = ('category__dept__divisi', 'category')
    search_fields = ('kode_sub', 'nama_sub')
    ordering = ('kode_sub',)


# ==========================================
# 2. MASTER SUPPLIER & ITEM
# ==========================================

@admin.register(Supplier)
class SupplierAdmin(ModelAdmin):
    list_display = (
        'kode_supplier',
        'nama_perusahaan',
        'kontak_person',
        'telepon',
        'top_days',
        'sistem_pesanan',
    )
    search_fields = (
        'kode_supplier',
        'nama_perusahaan',
        'kontak_person',
        'email',
    )
    list_filter = ('sistem_pesanan', 'top_days')
    ordering = ('kode_supplier',)

    fieldsets = [
        (_('1. INFORMASI UTAMA'), {
            'fields': ('kode_supplier', 'nama_perusahaan', 'alamat'),
        }),
        (_('2. INFORMASI KONTAK'), {
            'fields': ('kontak_person', 'telepon', 'email'),
        }),
        (_('3. LEGALITAS & KOMERSIAL'), {
            'fields': ('npwp_pkp_nib', 'top_days', 'sistem_pesanan'),
        }),
    ]


@admin.register(Item)
class ItemAdmin(ModelAdmin):
    list_display = (
        'item_code',
        'barcode_pcs_1',
        'nama_produk',
        'article_supplier_code',
        'get_stok_gudang',
        'get_stok_toko',
        'get_stok_retur',
        'get_total_stok',
        'sub_category',
        'supplier',
        'satuan',
        'harga_jual_non_ppn',
        'gross_margin_display',
        'status_store',
    )
    search_fields = (
        'item_code',
        'barcode_pcs_1',
        'barcode_pcs_2',
        'barcode_ctn',
        'nama_produk',
        'article_supplier_code',
    )
    list_filter = ('status_store', 'satuan', 'sub_category', 'supplier')
    ordering = ('item_code',)

    readonly_fields = (
        'item_code',
        'plu_code',
        'net_cost',
        'harga_beli_non_ppn',
        'harga_beli_ppn',
        'harga_jual_non_ppn',
        'harga_jual_ppn',
        'gross_margin_persen',
        'net_cost_display',
        'created_at',
        'updated_at',
    )

    fieldsets = [
        (_('1. IDENTIFIKASI & KLASIFIKASI UTAMA'), {
            'fields': ('item_code', 'plu_code', 'sub_category', 'supplier', 'status_store'),
        }),
        (_('2. MANAJEMEN BARCODE BERJENJANG (MULTI-BARCODE)'), {
            'fields': (
                ('barcode_pcs_1', 'barcode_pcs_2'),
                ('barcode_inner', 'isi_inner'),
                ('barcode_ctn', 'isi_carton'),
            ),
            'description': _('BARCODE PCS 1 & 2 UNTUK MENGANTISIPASI 2 VARIAN BARCODE FISIK DARI PABRIK (MISAL KEMASAN REGULER & KEMASAN PROMO).'),
        }),
        (_('3. REFERENSI ARTIKEL SUPPLIER (UNTUK FAKTUR & PO)'), {
            'fields': ('article_supplier_code', 'article_supplier_name'),
            'description': _('DIGUNAKAN SAAT PENCOCOKAN PO DAN FAKTUR TAGIHAN SUPPLIER AGAR AKURAT.'),
        }),
        (_('4. HIERARKI NAMA PRODUK'), {
            'fields': ('nama_produk', 'short_nama'),
        }),
        (_('5. SATUAN & KONVERSI KEMASAN'), {
            'fields': ('satuan',),
        }),
        (_('6. STRUKTUR HARGA & DISKON SUPPLIER'), {
            'fields': (
                'base_price',
                'diskon_1',
                'diskon_2',
                'diskon_3',
                'net_cost_display',
                'harga_beli_non_ppn',
                'ppn_beli_persen',
                'harga_beli_ppn',
            ),
        }),
        (_('7. HARGA JUAL & PROFITABILITAS'), {
            'fields': (
                'harga_jual',
                'harga_jual_non_ppn',
                'ppn_jual_persen',
                'harga_jual_ppn',
                'gross_margin_persen',
            ),
        }),
        (_('8. INTEGRASI PROMOSI'), {
            'fields': ('harga_promo', 'promo_mulai', 'promo_berakhir'),
        }),
    ]

    @admin.display(description=_('NET COST (OTOMATIS)'))
    def net_cost_display(self, obj):
        return f"Rp {obj.net_cost:,.2f}" if obj.net_cost is not None else "Rp 0.00"

    @admin.display(description=_('GROSS MARGIN (%)'))
    def gross_margin_display(self, obj):
        return f"{obj.gross_margin_persen:.2f}%" if obj.gross_margin_persen is not None else "0.00%"

    @admin.display(description=_('STOK GUDANG (DC)'))
    def get_stok_gudang(self, obj):
        return (
            StockSnapshot.objects.filter(item=obj, lokasi__tipe_site='WAREHOUSE')
            .aggregate(total=models.Sum('qty_on_hand'))['total'] or 0
        )

    @admin.display(description=_('STOK TOKO-TOKO'))
    def get_stok_toko(self, obj):
        return (
            StockSnapshot.objects.filter(item=obj, lokasi__tipe_site='STORE')
            .aggregate(total=models.Sum('qty_on_hand'))['total'] or 0
        )

    @admin.display(description=_('STOK RETUR/DAMAGE'))
    def get_stok_retur(self, obj):
        return (
            DamageGoods.objects.filter(item=obj)
            .aggregate(total=models.Sum('quantity'))['total'] or 0
        )

    @admin.display(description=_('TOTAL KESELURUHAN'))
    def get_total_stok(self, obj):
        return self.get_stok_gudang(obj) + self.get_stok_toko(obj)


# ==========================================
# 3. PURCHASE ORDER MANAGEMENT
# ==========================================

class PurchaseOrderItemInline(TabularInline):
    model = PurchaseOrderItem
    extra = 1
    readonly_fields = ('subtotal',)


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(ModelAdmin):
    list_display = (
        'no_po',
        'tipe_po',
        'supplier',
        'lokasi_tujuan',
        'tanggal_po',
        'status',
        'total_amount',
    )
    list_filter = ('tipe_po', 'status', 'tanggal_po')
    search_fields = ('no_po', 'supplier__nama_perusahaan')
    inlines = [PurchaseOrderItemInline]
    readonly_fields = ('no_po', 'total_amount')
    actions = ['generate_replenishment_action']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'replenishment-list/',
                self.admin_site.admin_view(self.replenishment_dashboard_view),
                name='merchandise_purchaseorder_replenishment_list',
            ),
        ]
        return custom_urls + urls

    def replenishment_dashboard_view(self, request):
        suppliers = Supplier.objects.all()
        context = {
            **self.admin_site.each_context(request),
            'title': _('DAFTAR SUPPLIER UNTUK PO REPLENISHMENT'),
            'suppliers': suppliers,
        }
        return render(
            request,
            'admin/merchandise/purchaseorder/replenishment_dashboard.html',
            context,
        )

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        supplier_id = request.GET.get('supplier_id')
        if supplier_id:
            initial['supplier'] = supplier_id
            initial['tipe_po'] = 'REPLENISHMENT'
        return initial

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.tipe_po == 'REPLENISHMENT':
            obj.generate_replenishment_items()

    @admin.action(description=_('GENERATE ULANG ITEM UNTUK PO REPLENISHMENT TERPILIH'))
    def generate_replenishment_action(self, request, queryset):
        count = 0
        for po in queryset:
            if po.tipe_po == 'REPLENISHMENT':
                po.generate_replenishment_items()
                count += 1

        self.message_user(
            request,
            _(f'BERHASIL MEN-GENERATE ITEM REPLENISHMENT UNTUK {count} PURCHASE ORDER.'),
        )


# ==========================================
# 4. INQUIRY GLOBAL STOK
# ==========================================

@admin.register(StockSnapshot)
class GlobalStockSnapshotAdmin(ModelAdmin):
    list_display = (
        'item',
        'lokasi',
        'get_tipe_site',
        'qty_on_hand',
        'last_updated',
    )
    list_filter = ('lokasi__tipe_site', 'lokasi', 'item__sub_category')
    search_fields = (
        'item__item_code',
        'item__nama_produk',
        'lokasi__nama_site',
    )
    readonly_fields = ('lokasi', 'item', 'qty_on_hand', 'last_updated')

    @admin.display(description=_('TIPE LOKASI'))
    def get_tipe_site(self, obj):
        return obj.lokasi.get_tipe_site_display()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False