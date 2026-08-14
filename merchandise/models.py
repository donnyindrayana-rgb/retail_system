from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import SiteLocation


# ==========================================
# 1. HIRARKI MERCHANDISE
# ==========================================

class Divisi(models.Model):
    kode_divisi = models.CharField(max_length=1, unique=True, blank=True)
    nama_divisi = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Divisi'
        verbose_name_plural = 'Divisi'

    def save(self, *args, **kwargs):
        if self.nama_divisi:
            self.nama_divisi = self.nama_divisi.upper()
        if self.kode_divisi:
            self.kode_divisi = self.kode_divisi.upper()

        if not self.kode_divisi:
            last_obj = Divisi.objects.all().order_by('id').last()
            next_num = (last_obj.id + 1) if last_obj else 1
            self.kode_divisi = str(next_num)[-1]
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.kode_divisi} - {self.nama_divisi}'


class Dept(models.Model):
    divisi = models.ForeignKey(Divisi, on_delete=models.CASCADE, related_name='departments')
    kode_dept = models.CharField(max_length=2, unique=True, blank=True)
    nama_dept = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Department'
        verbose_name_plural = 'Department'

    def save(self, *args, **kwargs):
        if self.nama_dept:
            self.nama_dept = self.nama_dept.upper()
        if self.kode_dept:
            self.kode_dept = self.kode_dept.upper()

        if not self.kode_dept and self.divisi and self.divisi.kode_divisi:
            last_obj = Dept.objects.filter(divisi=self.divisi).order_by('id').last()
            next_num = (last_obj.id + 1) if last_obj else 1
            self.kode_dept = f'{self.divisi.kode_divisi}{next_num % 10}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.kode_dept} - {self.nama_dept}'


class Category(models.Model):
    dept = models.ForeignKey(Dept, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)
    kode_category = models.CharField(max_length=50, unique=True, null=True, blank=True)
    nama_category = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def save(self, *args, **kwargs):
        if self.nama_category:
            self.nama_category = self.nama_category.upper()
        if self.kode_category:
            self.kode_category = self.kode_category.upper()

        if not self.kode_category and self.dept and self.dept.kode_dept:
            last_obj = Category.objects.filter(dept=self.dept).order_by('id').last()
            next_num = (last_obj.id + 1) if last_obj else 1
            self.kode_category = f'{self.dept.kode_dept}{next_num % 10}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.kode_category or "-"} - {self.nama_category or "-"}'


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories', null=True, blank=True)
    kode_sub = models.CharField(max_length=10, unique=True, null=True, blank=True)
    nama_sub = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        verbose_name = 'Sub-Category'
        verbose_name_plural = 'Sub-Category'

    def save(self, *args, **kwargs):
        if self.nama_sub:
            self.nama_sub = self.nama_sub.upper()
        if self.kode_sub:
            self.kode_sub = self.kode_sub.upper()

        if not self.kode_sub and self.category and self.category.kode_category:
            last_obj = SubCategory.objects.filter(category=self.category).order_by('id').last()
            next_num = (last_obj.id + 1) if last_obj else 1
            self.kode_sub = f'{self.category.kode_category}{next_num % 10}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.kode_sub or "-"} - {self.nama_sub or "-"}'


# ==========================================
# 2. MASTER SUPPLIER & ITEM
# ==========================================

class Supplier(models.Model):
    kode_supplier = models.CharField(max_length=20, unique=True, null=True, blank=True)
    nama_perusahaan = models.CharField(max_length=150, null=True, blank=True)
    alamat = models.TextField(null=True, blank=True)
    kontak_person = models.CharField(max_length=100, null=True, blank=True)
    telepon = models.CharField(max_length=30, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    npwp_pkp_nib = models.CharField(max_length=100, null=True, blank=True)
    top_days = models.IntegerField(default=30)
    sistem_pesanan = models.CharField(
        max_length=50, null=True, blank=True,
        choices=[('Direct Delivery', 'Direct Delivery'), ('Warehouse Supply', 'Warehouse Supply')]
    )

    class Meta:
        verbose_name = 'Master Supplier'
        verbose_name_plural = 'Master Supplier'

    def __str__(self):
        return f'{self.kode_supplier or "-"} - {self.nama_perusahaan or "-"}'


class Item(models.Model):
    sub_category = models.ForeignKey(
        SubCategory, on_delete=models.CASCADE, related_name='items',
        null=True, blank=True, verbose_name="Sub Kategori"
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name='items',
        null=True, blank=True, verbose_name="Supplier Utama"
    )

    # Identifikasi Dasar & Barcode Berjenjang
    item_code = models.CharField(max_length=50, unique=True, null=True, blank=True, db_index=True, verbose_name="Kode Internal")
    plu_code = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="PLU Code")

    barcode_pcs_1 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Barcode PCS (Utama)")
    barcode_pcs_2 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Barcode PCS (Alternatif/Promo)")
    barcode_inner = models.CharField(max_length=100, blank=True, null=True, verbose_name="Barcode Innerpack")
    barcode_ctn = models.CharField(max_length=100, blank=True, null=True, verbose_name="Barcode Carton (CTN)")

    # Konversi Kemasan
    isi_inner = models.IntegerField(default=1, verbose_name="Isi per Innerpack")
    isi_carton = models.IntegerField(default=1, verbose_name="Isi per Carton")

    # Nama & Artikel Supplier
    nama_produk = models.CharField(max_length=255, null=True, blank=True, verbose_name="Nama Produk Internal")
    short_nama = models.CharField(max_length=100, null=True, blank=True, verbose_name="Nama Singkat (Struk)")
    article_supplier_code = models.CharField(max_length=100, null=True, blank=True, verbose_name="Kode Artikel Supplier")
    article_supplier_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="Nama Artikel Supplier")

    # Satuan Dasar
    satuan = models.CharField(max_length=20, default='PCS', verbose_name="Satuan Dasar")

    # 1. Harga Beli & 2. Diskon Persentase
    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Harga Beli (Base Price)")
    diskon_1 = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Diskon 1 (%)")
    diskon_2 = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Diskon 2 (%)")
    diskon_3 = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Diskon 3 (%)")
    net_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False, verbose_name="Net Cost")

    # 4. Setting PPN Pembelian
    harga_beli_non_ppn = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    ppn_beli_persen = models.DecimalField(max_digits=5, decimal_places=2, default=11.00, verbose_name="PPN Beli (%)")
    harga_beli_ppn = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)

    # 3. Harga Jual & Profitabilitas
    harga_jual = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Harga Jual Normal")
    harga_jual_non_ppn = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    ppn_jual_persen = models.DecimalField(max_digits=5, decimal_places=2, default=11.00, verbose_name="PPN Jual (%)")
    harga_jual_ppn = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    gross_margin_persen = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), editable=False)

    # 3. Pengaturan Harga Promo (Dipisah pengelolaannya)
    harga_promo = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Harga Promo")
    promo_mulai = models.DateField(null=True, blank=True, verbose_name="Periode Promo Mulai")
    promo_berakhir = models.DateField(null=True, blank=True, verbose_name="Periode Promo Berakhir")

    # 6. Status Item & Status Store
    STATUS_ITEM_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('DISCONTINUE', 'Discontinue'),
        ('SUSPENDED', 'Suspended')
    ]
    status_item = models.CharField(max_length=30, default='ACTIVE', choices=STATUS_ITEM_CHOICES, verbose_name="Status Item")

    STATUS_STORE_CHOICES = (
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('DISCONTINUED', 'Discontinued'),
    )
    status_store = models.CharField(
        max_length=20,
        choices=STATUS_STORE_CHOICES,
        default='ACTIVE',
        verbose_name=_('Status Store')
    )

    # 5. Store Availability (Toko tempat item diizinkan untuk dijual)
    store_aktif_penjualan = models.ManyToManyField(
        SiteLocation,
        blank=True,
        related_name='allowed_items',
        limit_choices_to={'tipe_site': 'STORE'},
        verbose_name="Toko yang Diizinkan Menjual"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Master Item'
        verbose_name_plural = 'Master Item'

    def __str__(self):
        return f'[{self.item_code or "-"}] {self.nama_produk or "-"}'

    def save(self, *args, **kwargs):
        # 1. Kalkulasi Diskon Bertingkat (Net Cost)
        cost = self.base_price
        if self.diskon_1 > 0:
            cost *= (Decimal('100.00') - self.diskon_1) / Decimal('100.00')
        if self.diskon_2 > 0:
            cost *= (Decimal('100.00') - self.diskon_2) / Decimal('100.00')
        if self.diskon_3 > 0:
            cost *= (Decimal('100.00') - self.diskon_3) / Decimal('100.00')
        self.net_cost = cost

        # 2. Break-down PPN Beli
        if self.ppn_beli_persen > 0:
            self.harga_beli_non_ppn = self.net_cost
            self.harga_beli_ppn = self.net_cost * (Decimal('1.00') + (self.ppn_beli_persen / Decimal('100.00')))
        else:
            self.harga_beli_non_ppn = self.net_cost
            self.harga_beli_ppn = self.net_cost

        # 3. Break-down PPN Jual
        if self.ppn_jual_persen > 0:
            self.harga_jual_non_ppn = self.harga_jual / (Decimal('1.00') + (self.ppn_jual_persen / Decimal('100.00')))
            self.harga_jual_ppn = self.harga_jual
        else:
            self.harga_jual_non_ppn = self.harga_jual
            self.harga_jual_ppn = self.harga_jual

        # 4. Kalkulasi Gross Margin (%)
        if self.harga_jual_non_ppn > 0:
            margin = ((self.harga_jual_non_ppn - self.harga_beli_non_ppn) / self.harga_jual_non_ppn) * Decimal('100.00')
            self.gross_margin_persen = round(margin, 2)
        else:
            self.gross_margin_persen = Decimal('0.00')

        super().save(*args, **kwargs)


# ==========================================
# 3. PURCHASE ORDER MANAGEMENT
# ==========================================

class PurchaseOrder(models.Model):
    PO_TYPES = [
        ('DIRECT', 'Direct Order'),
        ('REPLENISHMENT', 'Replenishment Order')
    ]
    no_po = models.CharField(max_length=50, unique=True)
    tipe_po = models.CharField(max_length=20, choices=PO_TYPES, default='DIRECT')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='merchandise_purchase_orders')
    lokasi_tujuan = models.ForeignKey(SiteLocation, on_delete=models.PROTECT, related_name='merchandise_purchase_orders')
    tanggal_po = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, default='DRAFT')
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Order'

    def __str__(self):
        return f'{self.no_po} - {self.supplier.nama_perusahaan} ({self.get_tipe_po_display()})'

    def generate_replenishment_items(self):
        """
        Metode helper untuk menghitung dan menghasilkan item PO secara otomatis
        berdasarkan rata-rata penjualan 14 hari ke belakang, dikurangi stok berjalan,
        dan memperhitungkan retur/barang rusak yang di-input ke sistem.
        """
        if self.tipe_po != 'REPLENISHMENT':
            return

        # Hapus item existing jika di-generate ulang
        self.items.all().delete()

        today = self.tanggal_po
        start_date = today - timedelta(days=14)

        from operations.models import DamageGoods, SalesItem, StockSnapshot

        # 1. Hitung total penjualan 14 hari ke belakang per item dari seluruh toko
        sales_data = SalesItem.objects.filter(
            sales_header__tanggal_transaksi__date__gte=start_date,
            sales_header__tanggal_transaksi__date__lte=today,
            item__supplier=self.supplier,
            item__status_item='ACTIVE'
        ).values('item').annotate(total_sold=Sum('qty'))

        target_days = 14
        calculated_total = Decimal('0.00')

        sales_dict = {data['item']: data['total_sold'] for data in sales_data}
        supplier_items = Item.objects.filter(supplier=self.supplier, status_item='ACTIVE')

        for item in supplier_items:
            total_sold = sales_dict.get(item.id, Decimal('0.00'))
            adps_14 = Decimal(total_sold) / Decimal(14)
            projected_need = adps_14 * Decimal(target_days)

            # 2. Ambil sisa stok total saat ini dari StockSnapshot pada lokasi tujuan
            stock_record = StockSnapshot.objects.filter(
                lokasi=self.lokasi_tujuan,
                item=item
            ).first()
            current_stock = Decimal(stock_record.qty_on_hand) if stock_record else Decimal('0.00')

            # 3. Tambahkan kembali retur / barang rusak / pending return yang tercatat di lokasi
            pending_return = DamageGoods.objects.filter(
                location=self.lokasi_tujuan,
                item=item,
                is_written_off=False
            ).aggregate(total_damage=Sum('quantity'))['total_damage'] or Decimal('0.00')

            # 4. Hitung Rekomendasi Qty Order Bersih
            qty_order_calc = projected_need - current_stock + pending_return
            suggested_qty = int(qty_order_calc)

            if suggested_qty > 0:
                harga_satuan = item.net_cost if item.net_cost > 0 else item.base_price

                po_item = PurchaseOrderItem.objects.create(
                    po=self,
                    item=item,
                    qty_order=suggested_qty,
                    harga_beli_satuan=harga_satuan
                )
                calculated_total += po_item.subtotal

        self.total_amount = calculated_total
        self.save(update_fields=['total_amount'])


class PurchaseOrderItem(models.Model):
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='merchandise_po_items')
    qty_order = models.PositiveIntegerField(default=1)
    harga_beli_satuan = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    def save(self, *args, **kwargs):
        self.subtotal = Decimal(self.qty_order) * self.harga_beli_satuan
        super().save(*args, **kwargs)