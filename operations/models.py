from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from core.models import SiteLocation
from merchandise.models import Item, Supplier, PurchaseOrder


# --- MASTER RAK GUDANG (UNTUK PUTAWAY) ---
class WarehouseRack(models.Model):
    warehouse = models.ForeignKey(
        SiteLocation, 
        on_delete=models.CASCADE, 
        related_name='racks', 
        limit_choices_to={'tipe_site': 'DC'},
        help_text='Gudang/DC tempat rak ini berada'
    )
    kode_rak = models.CharField(max_length=50, unique=True, help_text='Contoh: RACK-A1-01-03')
    zona = models.CharField(max_length=50, null=True, blank=True, help_text='Contoh: Zona A (Fast Moving)')
    keterangan = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Master Rak Gudang'
        verbose_name_plural = 'Master Rak Gudang'

    def save(self, *args, **kwargs):
        if self.kode_rak:
            self.kode_rak = self.kode_rak.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.kode_rak} ({self.warehouse.nama_site})'


# --- INVENTORY STOCK (STOK FISIK PER SITE DAN RAK) ---
class InventoryStock(models.Model):
    site = models.ForeignKey(
        SiteLocation, 
        on_delete=models.CASCADE, 
        related_name='inventory_stocks',
        help_text='Lokasi Site (DC atau Toko)'
    )
    item = models.ForeignKey(
        Item, 
        on_delete=models.CASCADE, 
        related_name='inventory_stocks'
    )
    rack = models.ForeignKey(
        WarehouseRack, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='inventory_stocks',
        help_text='Rak penyimpanan (Opsional jika di Toko)'
    )
    quantity = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text='Jumlah kuantitas stok fisik aktual'
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Inventory Stock (Stok Rak/Site)'
        verbose_name_plural = 'Inventory Stock (Stok Rak/Site)'

    def __str__(self):
        rack_info = f' - Rak {self.rack.kode_rak}' if self.rack else ''
        return f'{self.site.nama_site}{rack_info} | {self.item.nama_produk}: {self.quantity}'


# --- GOODS RECEIVING & PUTAWAY (PENERIMAAN BARANG DARI SUPPLIER DI GUDANG) ---
class GoodsReceiving(models.Model):
    STATUS_GR = [
        ('PENDING', 'Pending (Menunggu Diterima)'),
        ('RECEIVED', 'Received (Barang Masuk)'),
        ('PUTAWAY_DONE', 'Putaway Completed (Masuk Rak)'),
        ('RETURNED', 'Returned to Supplier (Retur Keluar)'),
    ]

    no_gr = models.CharField(max_length=50, unique=True, help_text='Nomor Goods Receiving / Surat Jalan Masuk')
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name='goods_receivings')
    warehouse = models.ForeignKey(SiteLocation, on_delete=models.PROTECT, limit_choices_to={'tipe_site': 'DC'}, help_text='Gudang Penerima')
    tanggal_terima = models.DateTimeField(default=timezone.now)
    diterima_oleh = models.CharField(max_length=100, null=True, blank=True)
    catatan = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, default='PENDING', choices=STATUS_GR)

    class Meta:
        verbose_name = 'Goods Receiving (Penerimaan PO)'
        verbose_name_plural = 'Goods Receiving (Penerimaan PO)'

    def __str__(self):
        return f'GR #{self.no_gr} - PO: {self.purchase_order.no_po}'


class GoodsReceivingItem(models.Model):
    goods_receiving = models.ForeignKey(GoodsReceiving, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    qty_po = models.PositiveIntegerField(default=0)
    qty_received = models.PositiveIntegerField(default=0)
    rak_tujuan = models.ForeignKey(
        WarehouseRack, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='received_items',
        help_text='Alamat rak penyimpanan (Putaway)'
    )

    def __str__(self):
        return f'{self.item.nama_produk} - Diterima: {self.qty_received}'


# --- RETUR KE SUPPLIER DARI GUDANG ---
class SupplierReturn(models.Model):
    STATUS_RETUR = [
        ('DRAFT', 'Draft'),
        ('APPROVED', 'Disetujui'),
        ('SHIPPED', 'Dikirim ke Supplier'),
        ('COMPLETED', 'Selesai / Nota Kredit Diterbitkan'),
    ]
    no_retur = models.CharField(max_length=50, unique=True)
    warehouse = models.ForeignKey(SiteLocation, on_delete=models.PROTECT, limit_choices_to={'tipe_site': 'DC'})
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='supplier_returns')
    tanggal_retur = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, default='DRAFT', choices=STATUS_RETUR)
    keterangan = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Retur ke Supplier (Warehouse)'
        verbose_name_plural = 'Retur ke Supplier (Warehouse)'

    def __str__(self):
        return f'RETUR #{self.no_retur} - {self.supplier.nama_perusahaan}'


class SupplierReturnItem(models.Model):
    supplier_return = models.ForeignKey(SupplierReturn, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    qty_retur = models.PositiveIntegerField(default=0)
    alasan = models.CharField(max_length=255, help_text='Contoh: Barang Rusak / Expired / Cacat Produksi')


# --- PENGATURAN STOK & REPLENISHMENT TOKO ---
class StoreInventorySetting(models.Model):
    store = models.ForeignKey(
        SiteLocation, on_delete=models.CASCADE, related_name='inventory_settings', limit_choices_to={'tipe_site': 'STORE'}
    )
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name='store_settings'
    )
    minimum_stock = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00')
    )
    shelf_capacity = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00')
    ) 
    target_days_stock = models.IntegerField(default=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('store', 'item')
        verbose_name = 'Pengaturan Stok Toko'
        verbose_name_plural = 'Pengaturan Stok Toko'

    def __str__(self):
        return f'{self.store.nama_site} - {self.item.nama_produk} (Max Shelf: {self.shelf_capacity})'


# --- KONSOLIDASI STOK (MONITORING SISA STOK LOKASI) ---
class StockSnapshot(models.Model):
    lokasi = models.ForeignKey(
        SiteLocation, on_delete=models.CASCADE, related_name='stocks'
    )
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name='stocks'
    )
    qty_on_hand = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Sisa Stok Fisik Aktif',
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('lokasi', 'item')
        verbose_name = 'Konsolidasi Stok Lokasi'
        verbose_name_plural = 'Konsolidasi Stok Lokasi'

    def __str__(self):
        return f'{self.lokasi.kode_site} - {self.item.item_code}: {self.qty_on_hand}'


# --- KONSOLIDASI PENJUALAN (SALES DARI TOKO) ---
class SalesHeader(models.Model):
    lokasi = models.ForeignKey(
        SiteLocation, on_delete=models.PROTECT, related_name='sales', limit_choices_to={'tipe_site': 'STORE'}
    )
    no_transaksi_lokal = models.CharField(
        max_length=50, help_text='Nomor Struk Kasir Lokal Toko'
    )
    tanggal_transaksi = models.DateTimeField()
    total_belanja = models.DecimalField(max_digits=12, decimal_places=2)
    diskon_total = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00')
    )
    net_sales = models.DecimalField(max_digits=12, decimal_places=2)
    created_at_backoffice = models.DateTimeField(
        auto_now_add=True, help_text='Waktu data ditarik/diterima di pusat'
    )

    class Meta:
        unique_together = ('lokasi', 'no_transaksi_lokal')
        verbose_name = 'Konsolidasi Penjualan (Header)'
        verbose_name_plural = 'Konsolidasi Penjualan (Header)'

    def __str__(self):
        return f'{self.lokasi.kode_site} - {self.no_transaksi_lokal}'


class SalesItem(models.Model):
    sales_header = models.ForeignKey(
        SalesHeader, on_delete=models.CASCADE, related_name='items'
    )
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    harga_satuan = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)


# --- OPERASIONAL LOGISTIK & CABANG (REQUISITION, TRANSFER, DAMAGE, GONDOLA) ---
class StoreRequisition(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Disetujui Gudang'),
        ('REJECTED', 'Ditolak'),
        ('COMPLETED', 'Selesai Dikirim'),
    )
    requisition_code = models.CharField(max_length=100, unique=True)
    store_location = models.ForeignKey(
        SiteLocation, on_delete=models.CASCADE, related_name='requisitions', limit_choices_to={'tipe_site': 'STORE'}
    )
    requested_by = models.ForeignKey(User, on_delete=models.PROTECT)
    status = models.CharField(
        choices=STATUS_CHOICES, default='PENDING', max_length=20
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'REQ {self.requisition_code} - {self.store_location.nama_site}'


class StoreRequisitionDetail(models.Model):
    requisition = models.ForeignKey(
        StoreRequisition, on_delete=models.CASCADE, related_name='details'
    )
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity_requested = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_approved = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00')
    )

    def __str__(self):
        return f'{self.item.nama_produk} (Req: {self.quantity_requested})'


class StockTransfer(models.Model):
    TRANSFER_TYPES = (
        ('WH_TO_STORE', 'Gudang ke Toko (Replenishment)'),
        ('STORE_TO_STORE', 'Antar Toko'),
        ('STORE_TO_WH', 'Toko ke Gudang (Retur Toko)'),
    )
    TRANSFER_STATUS = (
        ('PICKING', 'Picking (Pengambilan di Rak)'),
        ('TRANSIT', 'In Transit (Dalam Pengiriman)'),
        ('RECEIVED', 'Received (Diterima)'),
    )

    transfer_code = models.CharField(max_length=100, unique=True)
    source_location = models.ForeignKey(
        SiteLocation, on_delete=models.PROTECT, related_name='outgoing_transfers'
    )
    destination_location = models.ForeignKey(
        SiteLocation, on_delete=models.PROTECT, related_name='incoming_transfers'
    )
    transfer_type = models.CharField(choices=TRANSFER_TYPES, max_length=30)
    status = models.CharField(choices=TRANSFER_STATUS, default='PICKING', max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f'TRF {self.transfer_code} [{self.get_transfer_type_display()}]'


class StockTransferItem(models.Model):
    transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    qty_sent = models.PositiveIntegerField(default=0)
    qty_received = models.PositiveIntegerField(default=0)
    rack_source = models.ForeignKey(
        WarehouseRack, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text='Asal rak gudang untuk proses picking'
    )


# --- MANAJEMEN GONDOLA & DAMAGE DI TOKO ---
class StoreGondolaRack(models.Model):
    store = models.ForeignKey(SiteLocation, on_delete=models.CASCADE, related_name='gondola_racks', limit_choices_to={'tipe_site': 'STORE'})
    kode_gondola = models.CharField(max_length=50, help_text='Contoh: GONDOLA-A1-03')
    keterangan = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.store.nama_site} - {self.kode_gondola}'


class DamageGoods(models.Model):
    location = models.ForeignKey(SiteLocation, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    reported_at = models.DateTimeField(auto_now_add=True)
    is_written_off = models.BooleanField(default=False)

    def __str__(self):
        return f'DAMAGE: {self.item.nama_produk} at {self.location.nama_site} ({self.quantity})'