"""
URL configuration for retail_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.templatetags.static import static

urlpatterns = [
    # Redirect otomatis request /favicon.ico ke logo Nichomaret PNG
    path(
        'favicon.ico',
        RedirectView.as_view(
            url=static('img/logo_Nichomaret.png'),
            permanent=True
        )
    ),

    # Django Admin Panel
    path('admin/', admin.site.urls),

    # App Sub-URLs
    path('merchandise/', include('merchandise.urls')),

    # (Opsional) Tambahkan app lain di sini jika sudah ada
    # path('operations/', include('operations.urls')),
    # path('finance/', include('finance.urls')),
    # path('core/', include('core.urls')),
    # path('customers/', include('customers.urls')),
]