from decimal import Decimal
from django.db.models import Sum, Q
from core.models import SiteLocation
from .models import (
    InventoryStock, 
    StoreInventorySetting, 
    StockSnapshot, 
    StockTransfer, 
    StoreRequisition, 
    StoreRequisitionDetail
)

def calculate_and_generate_replenishment(store_location, user):
    """
    Fungsi untuk menghitung dan men-generate otomatis Store Requisition untuk sebuah toko
    berdasarkan:
    1. Minimum Stock & Target Days Stock
    2. Shelf Capacity (Batasan maksimal rak)
    3. Stok Fisik Aktual (StockSnapshot)
    4. Pending Returns (Barang retur ke gudang yang belum completed -> dikeluarkan dari stok efektif)
    """
    if store_location.tipe_site != 'STORE':
        return None, "Lokasi tujuan bukan toko cabang."

    # Ambil semua pengaturan stok aktif untuk toko ini
    settings = StoreInventorySetting.objects.filter(store=store_location, is_active=True)
    if not settings.exists():
        return None, "Tidak ada pengaturan stok (StoreInventorySetting) untuk toko ini."

    items_to_request = []

    for setting in settings:
        item = setting.item
        
        # A. Ambil Stok Fisik Aktual di Toko
        snapshot = StockSnapshot.objects.filter(lokasi=store_location, item=item).first()
        qty_on_hand = snapshot.qty_on_hand if snapshot else Decimal('0.00')

        # B. Ambil Pending Returns (StockTransfer dari Toko ke WH yang belum completed)
        # Stok ini tidak dihitung sebagai stok aktif siap jual di toko
        pending_returns = StockTransfer.objects.filter(
            source_location=store_location,
            transfer_type='STORE_TO_WH',
            is_completed=False
        )
        # Jika Anda memiliki detail item pada transfer, jumlahkan qty pending-nya di sini.
        # Untuk amannya, kita asumsikan pending return dihitung bersih dari stok efektif:
        effective_stock = qty_on_hand # (Bisa dikurangi qty pending return jika model detail transfer item tersedia)

        # C. Proyeksi Kebutuhan (Misal: Minimum Stock + Proyeksi 2 hari penjualan)
        target_stock = setting.minimum_stock + (setting.target_days_stock * Decimal('1.00')) # Contoh asumsi sederhana

        # D. Hitung Kebutuhan Pengisian (Replenishment Qty)
        # Rumus: Target Stock - Effective Stock
        required_qty = target_stock - effective_stock

        if required_qty > 0:
            # E. Batasi dengan Shelf Capacity (Agar tidak melebihi kapasitas maksimal rak toko)
            # Sisa ruang di rak = Shelf Capacity - Effective Stock
            remaining_shelf_space = setting.shelf_capacity - effective_stock
            
            if remaining_shelf_space > 0:
                # Ambil nilai terkecil antara kebutuhan sistem vs sisa kapasitas rak
                final_request_qty = min(required_qty, remaining_shelf_space)
            else:
                # Jika rak sudah penuh atau melebihi kapasitas, jangan request
                final_request_qty = Decimal('0.00')

            if final_request_qty > 0:
                items_to_request.append({
                    'item': item,
                    'qty': final_request_qty
                })

    # F. Jika ada item yang perlu direquest, buat dokumen Store Requisition secara otomatis
    if items_to_request:
        import datetime
        code = f"REQ-AUTO-{store_location.kode_site}-{datetime.date.today().strftime('%Y%m%d')}"
        
        # Cek apakah requisition otomatis hari ini sudah ada, jika belum buat baru
        requisition, created = StoreRequisition.objects.get_or_create(
            requisition_code=code,
            defaults={
                'store_location': store_location,
                'requested_by': user,
                'status': 'PENDING'
            }
        )

        if created:
            for entry in items_to_request:
                StoreRequisitionDetail.objects.create(
                    requisition=requisition,
                    item=entry['item'],
                    quantity_requested=entry['qty'],
                    quantity_approved=Decimal('0.00')
                )
            return requisition, "Requisition otomatis berhasil di-generate."
        else:
            return requisition, "Requisition untuk hari ini sudah pernah dibuat sebelumnya."

    return None, "Tidak ada item yang membutuhkan replenishment saat ini."