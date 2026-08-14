from decimal import Decimal
from django.db.models import Sum
from operations.models import StockSnapshot, InventoryStock
from .models import Item

class MerchandiseInquiryService:
    
    @staticmethod
    def get_global_item_stock_summary(item_id):
        """
        Menampilkan ringkasan stok suatu item secara global:
        - Total di seluruh Warehouse (DC)
        - Total di seluruh Toko (Store)
        - Rincian per site/lokasi
        """
        try:
            item = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            return None
        
        snapshots = StockSnapshot.objects.filter(item=item).select_related('lokasi')
        
        dc_total = Decimal('0.00')
        store_total = Decimal('0.00')
        breakdown = []

        for snap in snapshots:
            site = snap.lokasi
            if site.tipe_site == 'DC':
                dc_total += snap.qty_on_hand
            elif site.tipe_site == 'STORE':
                store_total += snap.qty_on_hand
                
            breakdown.append({
                'kode_site': site.kode_site,
                'nama_site': site.nama_site,
                'tipe_site': site.tipe_site,
                'qty_on_hand': snap.qty_on_hand,
                'last_updated': snap.last_updated
            })

        return {
            'item_code': item.item_code,
            'nama_produk': item.nama_produk,
            'total_dc_stock': dc_total,
            'total_store_stock': store_total,
            'grand_total_stock': dc_total + store_total,
            'breakdown_lokasi': breakdown
        }

    @staticmethod
    def get_warehouse_rack_detail(warehouse_id):
        """
        Melihat rincian stok per rak di gudang tertentu (khusus tim Merchandise/DC).
        """
        return InventoryStock.objects.filter(
            site_id=warehouse_id, 
            rack__isnull=False
        ).select_related('item', 'rack', 'site')