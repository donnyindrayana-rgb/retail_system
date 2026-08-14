from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.db.models import Sum, Q, Value
from django.db.models.functions import Coalesce
from unfold.admin import ModelAdmin
from .models import (
    WarehouseRack,
    InventoryStock,
    GoodsReceiving,
    GoodsReceivingItem,
    StoreInventorySetting,
    SalesHeader,
    SalesItem,
    StockTransfer,
    StockTransferItem,
    StoreRequisition,
    StoreRequisitionDetail,
    DamageGoods,
    StockSnapshot,
)
from .services import calculate_and_generate_replenishment
from merchandise.models import Item, PurchaseOrderItem
from core.models import SiteLocation


# --- MIXIN PEMBATASAN AKSES TOKO VS PUSAT ---
class RoleBasedSiteAccessAdminMixin:
    """
    Mixin untuk memfilter data operasional secara otomatis berdasarkan site user.
    Merchandiser / Superuser melihat semua. Staff Toko hanya melihat site mereka.
    """
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.groups.filter(name='Merchandiser').exists():
            return qs
        
        if hasattr(request.user, 'site_access'):
            assigned_site = request.user.site_access.assigned_site
            if hasattr(qs.model, 'lokasi'):
                return qs.filter(lokasi=assigned_site)
            elif hasattr(qs.model, 'location'):
                return qs.filter(location=assigned_site)
            elif hasattr(qs.model, 'lokasi_tujuan'):
                return qs.filter(lokasi_tujuan=assigned_site)
            elif hasattr(qs.model, 'site'):
                return qs.filter(site=assigned_site)
            elif hasattr(qs.model, 'store_location'):
                return qs.filter(store_location=assigned_site)
        return qs.none()


# --- CUSTOM ADMIN VIEW UNTUK UNIFIED STOCK INQUIRY & REPLENISHMENT ---
class UnifiedStockInquiryAdmin(ModelAdmin):
    """
    Dashboard interaktif untuk memantau end-to-end stok, in-transit, retur, dan open PO.
    """
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'unified-stock-inquiry/',
                self.admin_site.admin_view(self.stock_inquiry_dashboard_view),
                name='operations_stocksnapshot_unified_inquiry'
            ),
        ]
        return custom_urls + urls

    def stock_inquiry_dashboard_view(self, request):
        user = request.user
        is_merchandiser = user.is_superuser or user.groups.filter(name='Merchandiser').exists()
        
        # Tentukan batasan site berdasarkan user yang login
        allowed_sites = None
        selected_site_id = request.GET.get('site_id')
        
        if not is_merchandiser:
            if hasattr(user, 'site_access'):
                allowed_sites = [user.site_access.assigned_site]
            else:
                allowed_sites = []
        else:
            if selected_site_id:
                allowed_sites = SiteLocation.objects.filter(id=selected_site_id)
            else:
                allowed_sites = SiteLocation.objects.all()

        # Ambil parameter pencarian item / supplier
        search_query = request.GET.get('q', '')
        items_qs = Item.objects.select_related('sub_category', 'supplier').all()
        if search_query:
            items_qs = items_qs.filter(
                Q(item_code__icontains=search_query) | 
                Q(nama_produk__icontains=search_query) |
                Q(barcode_internal__icontains=search_query)
            )

        # Batasi jumlah baris per halaman atau ambil limit
        items_qs = items_qs[:100] 

        report_rows = []
        for item in items_qs:
            # 1. Stok Gudang (DC)
            dc_qs = StockSnapshot.objects.filter(item=item, lokasi__tipe_site='DC')
            if not is_merchandiser and allowed_sites:
                dc_qs = dc_qs.filter(lokasi__in=allowed_sites)
            soh_warehouse = dc_qs.aggregate(total=Coalesce(Sum('qty_on_hand'), Value(0, output_field=models.DecimalField())))['total']

            # 2. Stok Toko-toko
            store_qs = StockSnapshot.objects.filter(item=item, lokasi__tipe_site='STORE')
            if allowed_sites:
                store_qs = store_qs.filter(lokasi__in=allowed_sites)
            soh_store = store_qs.aggregate(total=Coalesce(Sum('qty_on_hand'), Value(0, output_field=models.DecimalField())))['total']

            # 3. Open Purchase Order (Ke Supplier belum diterima)
            po_qs = PurchaseOrderItem.objects.filter(item=item, po__status__in=['APPROVED', 'SUBMITTED', 'PARTIAL'])
            if not is_merchandiser and allowed_sites:
                po_qs = po_qs.filter(po__lokasi_tujuan__in=allowed_sites)
            open_po = po_qs.aggregate(total=Coalesce(Sum('qty_order'), Value(0, output_field=models.IntegerField())))['total']

            # 4. Retur / Damage Goods (Belum di-receive gudang)
            damage_qs = DamageGoods.objects.filter(item=item, is_written_off=False)
            if allowed_sites:
                damage_qs = damage_qs.filter(location__in=allowed_sites)
            pending_return = damage_qs.aggregate(total=Coalesce(Sum('quantity'), Value(0, output_field=models.DecimalField())))['total']

            report_rows.append({
                'item_code': item.item_code,
                'nama_produk': item.nama_produk,
                'supplier': item.supplier.nama_perusahaan if item.supplier else '-',
                'soh_warehouse': soh_warehouse,
                'soh_store': soh_store,
                'open_po': open_po,
                'pending_return': pending_return,
                'total_availability': soh_warehouse + soh_store + open_po
            })

        all_sites = SiteLocation.objects.all() if is_merchandiser else []

        context = {
            **self.admin_site.each_context(request),
            'title': _('Unified Stock Inquiry & Replenishment Hub'),
            'report_rows': report_rows,
            'all_sites': all_sites,
            'is_merchandiser': is_merchandiser,
            'search_query': search_query,
            'selected_site_id': selected_site_id,
        }
        return render(request, 'admin/operations/stocksnapshot/unified_stock_inquiry.html', context)


# --- REGISTRASI MODEL OPERASIONAL ---

if admin.site.is_registered(StockSnapshot):
    admin.site.unregister(StockSnapshot)

@admin.register(StockSnapshot)
class StockSnapshotAdmin(UnifiedStockInquiryAdmin, RoleBasedSiteAccessAdminMixin):
    """
    Menjadikan Unified Stock Inquiry sebagai halaman utama (changelist) 
    untuk model StockSnapshot agar otomatis tampil di sidebar Django Unfold.
    """
    pass


@admin.register(WarehouseRack)
class WarehouseRackAdmin(ModelAdmin, RoleBasedSiteAccessAdminMixin):
    list_display = ('kode_rak', 'warehouse', 'zona', 'keterangan')
    list_filter = ('warehouse', 'zona')
    search_fields = ('kode_rak', 'zona', 'warehouse__nama_site')


@admin.register(InventoryStock)
class InventoryStockAdmin(ModelAdmin, RoleBasedSiteAccessAdminMixin):
    list_display = ('site', 'item', 'rack', 'quantity')
    list_filter = ('site', 'rack')
    search_fields = ('site__nama_site', 'item__nama_produk', 'item__item_code', 'rack__kode_rak')


class GoodsReceivingItemInline(admin.TabularInline):
    model = GoodsReceivingItem
    extra = 1


@admin.register(GoodsReceiving)
class GoodsReceivingAdmin(ModelAdmin, RoleBasedSiteAccessAdminMixin):
    list_display = ('no_gr', 'purchase_order', 'warehouse', 'tanggal_terima', 'diterima_oleh', 'status')
    list_filter = ('status', 'warehouse')
    search_fields = ('no_gr', 'purchase_order__no_po', 'diterima_oleh')
    inlines = [GoodsReceivingItemInline]


@admin.register(StoreInventorySetting)
class StoreInventorySettingAdmin(ModelAdmin, RoleBasedSiteAccessAdminMixin):
    list_display = ('store', 'item', 'minimum_stock', 'shelf_capacity', 'target_days_stock', 'is_active')
    list_filter = ('store', 'is_active')
    search_fields = ('store__nama_site', 'item__nama_produk', 'item__item_code')


class SalesItemInline(admin.TabularInline):
    model = SalesItem
    extra = 0


@admin.register(SalesHeader)
class SalesHeaderAdmin(ModelAdmin, RoleBasedSiteAccessAdminMixin):
    list_display = ('lokasi', 'no_transaksi_lokal', 'tanggal_transaksi', 'net_sales')
    list_filter = ('lokasi', 'tanggal_transaksi')
    search_fields = ('no_transaksi_lokal', 'lokasi__nama_site')
    inlines = [SalesItemInline]


class StoreRequisitionDetailInline(admin.TabularInline):
    model = StoreRequisitionDetail
    extra = 1


@admin.register(StoreRequisition)
class StoreRequisitionAdmin(ModelAdmin, RoleBasedSiteAccessAdminMixin):
    list_display = ('requisition_code', 'store_location', 'requested_by', 'status', 'created_at')
    list_filter = ('status', 'store_location')
    search_fields = ('requisition_code', 'store_location__nama_site')
    inlines = [StoreRequisitionDetailInline]
    
    actions = ['generate_replenishment_action']

    @admin.action(description='Generate Auto-Replenishment untuk Toko Terpilih')
    def generate_replenishment_action(self, request, queryset):
        success_count = 0
        for requisition in queryset:
            location = requisition.store_location
            if location.tipe_site == 'STORE':
                _, message = calculate_and_generate_replenishment(location, request.user)
                if message:
                    success_count += 1
            
        self.message_user(request, f"Berhasil memproses replenishment otomatis untuk {success_count} toko.")


@admin.register(StoreRequisitionDetail)
class StoreRequisitionDetailAdmin(ModelAdmin):
    list_display = ('requisition', 'item', 'quantity_requested', 'quantity_approved')
    search_fields = ('requisition__requisition_code', 'item__nama_produk')


class StockTransferItemInline(admin.TabularInline):
    model = StockTransferItem
    extra = 1


@admin.register(StockTransfer)
class StockTransferAdmin(ModelAdmin, RoleBasedSiteAccessAdminMixin):
    list_display = ('transfer_code', 'source_location', 'destination_location', 'transfer_type', 'status', 'is_completed', 'created_at')
    list_filter = ('transfer_type', 'status', 'is_completed')
    search_fields = ('transfer_code',)
    inlines = [StockTransferItemInline]


@admin.register(DamageGoods)
class DamageGoodsAdmin(ModelAdmin, RoleBasedSiteAccessAdminMixin):
    list_display = ('location', 'item', 'quantity', 'is_written_off', 'reported_at')
    list_filter = ('is_written_off', 'location')
    search_fields = ('item__nama_produk', 'location__nama_site')