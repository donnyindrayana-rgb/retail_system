# retail_system/settings.py
import os
from pathlib import Path
from django.templatetags.static import static

# 1. BUILD PATHS
BASE_DIR = Path(__file__).resolve().parent.parent

# Mengambil secret key dari environment variable cloud, fallback ke insecure key untuk lokal
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-g$q23%^&z*s8v_x+z-j-k!9l0p#m-a1b2c3d4e5f6g7h8i9j0'
)

# DEBUG otomatis False jika dijalankan di cloud (Render/Railway), True jika di komputer lokal
DEBUG = 'RENDER' not in os.environ and 'RAILWAY_ENVIRONMENT' not in os.environ

# Mengatur host yang diizinkan agar bisa diakses secara publik di cloud
ALLOWED_HOSTS = ['*']

ROOT_URLCONF = 'retail_system.urls'

LANGUAGE_CODE = 'id-id'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,  # Menunggu hingga 20 detik jika DB sedang terkunci
        },
    }
}

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'unfold.contrib.import_export',
    'unfold.contrib.guardian',
    'unfold.contrib.simple_history',
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework.authtoken',

    # Aplikasi Crispy Forms & Tailwind
    'crispy_forms',
    'crispy_tailwind',

    'core',
    'merchandise',
    'operations',
    'finance',
    'customers',
]

# Konfigurasi Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # <-- Ditambahkan untuk melayani file statis di cloud
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Konfigurasi kompresi WhiteNoise untuk produksi
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

UNFOLD = {
    "SITE_TITLE": "Nichomaret Admin System",
    "SITE_HEADER": "Nichomaret Retail",
    "SITE_LOGO": {
        "light": "/static/img/logo_Nichomaret.png",
        "dark": "/static/img/logo_Nichomaret.png",
    },
    "SITE_FAVICON": "/static/img/logo_Nichomaret.png",
    "SITE_SYMBOL": "/static/img/logo_Nichomaret.png",

    "STYLES": [
        lambda request: static("css/custom_admin.css"),
    ],

    # Konfigurasi Jam Real-Time yang telah diperbarui
    "EXTRA_HEAD": [
        lambda request: """
        <script>
            document.addEventListener("DOMContentLoaded", function() {
                function updateGlobalClock() {
                    const now = new Date();
                    const options = { 
                        weekday: 'long', 
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric', 
                        hour: '2-digit', 
                        minute: '2-digit', 
                        second: '2-digit',
                        hour12: false 
                    };
                    
                    let clockContainer = document.getElementById('global-realtime-clock');
                    if (!clockContainer) {
                        const topNavBar = document.querySelector('nav') || document.querySelector('header') || document.querySelector('.bg-white');
                        if (topNavBar) {
                            clockContainer = document.createElement('div');
                            clockContainer.id = 'global-realtime-clock';
                            clockContainer.style.cssText = 'margin-left: auto; margin-right: 16px; display: flex; align-items: center; gap: 8px; padding: 6px 12px; font-size: 12px; font-weight: 500; background-color: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 6px; color: #374151; z-index: 50;';
                            
                            const targetFlex = document.querySelector('.navbar') || document.querySelector('div.flex.items-center.justify-between') || topNavBar;
                            if (targetFlex) {
                                targetFlex.style.display = 'flex';
                                targetFlex.style.alignItems = 'center';
                                targetFlex.appendChild(clockContainer);
                            }
                        }
                    }
                    if (clockContainer) {
                        clockContainer.innerHTML = '🕒 ' + now.toLocaleDateString('id-ID', options) + ' WIB';
                    }
                }
                setInterval(updateGlobalClock, 1000);
                updateGlobalClock();
            });
        </script>
        """,
    ],

    "TABS": [
        {
            "models": ["merchandise.item", "merchandise.supplier", "merchandise.purchaseorder"],
            "items": [
                {"title": "Master Item", "link": "/admin/merchandise/item/"},
                {"title": "Master Supplier", "link": "/admin/merchandise/supplier/"},
                {"title": "Purchase Order", "link": "/admin/merchandise/purchaseorder/"},
            ],
        },
        {
            "models": ["operations.stocksnapshot", "operations.goodsreceiving", "operations.storerequisition"],
            "items": [
                {"title": "Stock Inquiry", "link": "/admin/operations/stocksnapshot/unified-stock-inquiry/"},
                {"title": "Goods Receiving", "link": "/admin/operations/goodsreceiving/"},
                {"title": "Store Requisition", "link": "/admin/operations/storerequisition/"},
            ],
        },
    ],

    "SIDEBAR": {
        "navigation": [
            {
                "title": "Core Settings & Master",
                "separator": True,
                "items": [
                    {"title": "Profil Perusahaan (NIB & NPWP)", "icon": "business", "link": "/admin/core/companyprofile/"},
                    {"title": "Master Site (DC & Toko)", "icon": "store", "link": "/admin/core/sitelocation/"},
                    {"title": "Akses Site User", "icon": "badge", "link": "/admin/core/usersiteaccess/"},
                ],
            },
            {
                "title": "Merchandise Management",
                "separator": True,
                "items": [
                    {"title": "Divisi", "icon": "category", "link": "/admin/merchandise/divisi/"},
                    {"title": "Department", "icon": "account_tree", "link": "/admin/merchandise/dept/"},
                    {"title": "Category", "icon": "grid_view", "link": "/admin/merchandise/category/"},
                    {"title": "Sub-Category", "icon": "subdirectory_arrow_right", "link": "/admin/merchandise/subcategory/"},
                    {"title": "Master Supplier", "icon": "local_shipping", "link": "/admin/merchandise/supplier/"},
                    {"title": "Master Item", "icon": "inventory_2", "link": "/admin/merchandise/item/"},
                    {"title": "Purchase Order (Pusat)", "icon": "shopping_cart", "link": "/admin/merchandise/purchaseorder/"},
                    {"title": "Dashboard Replenishment", "icon": "fact_check", "link": "/admin/merchandise/purchaseorder/replenishment-list/"},
                ],
            },
            {
                "title": "Operations & Inventory",
                "separator": True,
                "items": [
                    {"title": "Unified Stock Inquiry", "icon": "analytics", "link": "/admin/operations/stocksnapshot/unified-stock-inquiry/"},
                    {"title": "Pengaturan Stok Toko", "icon": "inventory", "link": "/admin/operations/storeinventorysetting/"},
                    {"title": "Master Rak Gudang", "icon": "shelves", "link": "/admin/operations/warehouserack/"},
                    {"title": "Goods Receiving (Penerimaan PO)", "icon": "move_to_inbox", "link": "/admin/operations/goodsreceiving/"},
                    {"title": "Store Requisition", "icon": "assignment", "link": "/admin/operations/storerequisition/"},
                    {"title": "Stock Transfer", "icon": "swap_horiz", "link": "/admin/operations/stocktransfer/"},
                    {"title": "Konsolidasi Penjualan", "icon": "receipt_long", "link": "/admin/operations/salesheader/"},
                    {"title": "Inventory Stock (Stok Rak/Site)", "icon": "warehouse", "link": "/admin/operations/inventorystock/"},
                    {"title": "Konsolidasi Stok", "icon": "assessment", "link": "/admin/operations/stocksnapshot/"},
                    {"title": "Damage Goods", "icon": "warning", "link": "/admin/operations/damagegoods/"},
                ],
            },
            {
                "title": "Finance",
                "separator": True,
                "items": [
                    {"title": "Transactions", "icon": "payments", "link": "/admin/finance/transaction/"},
                ],
            },
            {
                "title": "Customers",
                "separator": True,
                "items": [
                    {"title": "Customer List", "icon": "group", "link": "/admin/customers/customer/"},
                ],
            },
            {
                "title": "Sampel & Prototipe",
                "separator": True,
                "items": [
                    {"title": "Sample Order Form", "icon": "description", "link": "/merchandise/sample-order-form/"},
                ],
            },
        ],
    },
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'