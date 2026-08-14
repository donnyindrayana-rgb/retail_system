from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import CompanyProfile, SiteLocation, UserSiteAccess

@admin.register(CompanyProfile)
class CompanyProfileAdmin(ModelAdmin):
    list_display = ('kode_perusahaan', 'nama_perusahaan', 'nib', 'npwp', 'telepon', 'email')
    search_fields = ('kode_perusahaan', 'nama_perusahaan', 'nib', 'npwp')

@admin.register(SiteLocation)
class SiteLocationAdmin(ModelAdmin):
    list_display = ('kode_site', 'nama_site', 'tipe_site', 'company', 'npwp_cabang', 'is_active', 'replenishment_schedule_days')
    list_filter = ('tipe_site', 'is_active', 'company')
    search_fields = ('kode_site', 'nama_site', 'npwp_cabang')

@admin.register(UserSiteAccess)
class UserSiteAccessAdmin(ModelAdmin):
    list_display = ('user', 'assigned_site', 'jabatan', 'no_hp')
    list_filter = ('assigned_site', 'jabatan')
    search_fields = ('user__username', 'user__first_name', 'assigned_site__nama_site')