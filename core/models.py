from django.db import models
from django.contrib.auth.models import User

# --- 1. COMPANY PROFILE (PROFIL PERUSAHAAN & LEGALITAS) ---
class CompanyProfile(models.Model):
    nama_perusahaan = models.CharField(max_length=150, help_text="Contoh: PT Retail Nusantara Sejahtera")
    kode_perusahaan = models.CharField(max_length=20, unique=True, help_text="Contoh: RNS")
    
    # Legalitas & Perizinan Usaha
    nib = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="Nomor Induk Berusaha (NIB)")
    npwp = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="NPWP Badan Usaha / Perusahaan")
    
    alamat = models.TextField()
    telepon = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='company/logo/', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Profil Perusahaan'
        verbose_name_plural = 'Profil Perusahaan'

    def __str__(self):
        return f"{self.nama_perusahaan} (NIB: {self.nib or '-'})"


# --- 2. MASTER SITE (DC, STORE, & KANTOR PUSAT) ---
class SiteLocation(models.Model):
    SITE_TYPES = [
        ('DC', 'Distribution Center / Gudang Utama'),
        ('STORE', 'Toko Cabang / Store'),
        ('HO', 'Head Office / Kantor Pusat'),
    ]

    kode_site = models.CharField(max_length=20, unique=True, help_text='Contoh: HO-01, DC-01, TKO-01')
    nama_site = models.CharField(max_length=100)
    tipe_site = models.CharField(max_length=10, choices=SITE_TYPES, default='STORE')
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='sites', help_text='Perusahaan induk site ini')
    
    # Informasi operasional & perpajakan pendukung cabang
    npwp_cabang = models.CharField(max_length=50, blank=True, null=True, help_text='NPWP Cabang (jika ada pendaftaran khusus lokasi)')
    
    alamat = models.TextField(blank=True, null=True)
    telepon = models.CharField(max_length=30, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    # Khusus untuk pengaturan operasional Store / DC (jadwal replenishment)
    replenishment_schedule_days = models.CharField(
        max_length=50, 
        default='MON,THU', 
        blank=True, 
        null=True,
        help_text='Hari jadwal replenishment (khusus Store), contoh: MON,THU'
    )

    class Meta:
        verbose_name = 'Master Site (DC & Toko)'
        verbose_name_plural = 'Master Site (DC & Toko)'

    def save(self, *args, **kwargs):
        if self.kode_site:
            self.kode_site = self.kode_site.upper()
        if self.nama_site:
            self.nama_site = self.nama_site.upper()
        if self.replenishment_schedule_days:
            self.replenishment_schedule_days = self.replenishment_schedule_days.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'[{self.kode_site}] {self.nama_site} ({self.get_tipe_site_display()})'


# --- 3. EXTENDED USER PROFILE / EMPLOYEE ASSIGNMENT ---
class UserSiteAccess(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='site_access')
    assigned_site = models.ForeignKey(SiteLocation, on_delete=models.PROTECT, related_name='assigned_users', help_text='Site/Cabang tempat user ini bertugas')
    jabatan = models.CharField(max_length=100, blank=True, null=True, help_text='Contoh: Store Manager, Kasir, Inventory Control')
    no_hp = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        verbose_name = 'Akses Site User'
        verbose_name_plural = 'Akses Site User'

    def __str__(self):
        return f'{self.user.username} - {self.assigned_site.nama_site}'