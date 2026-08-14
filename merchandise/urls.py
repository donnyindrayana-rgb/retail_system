from django.urls import path
from . import views

app_name = 'merchandise'

urlpatterns = [
    # --------------------------------------------------
    # REST API ENDPOINTS
    # --------------------------------------------------
    path('api/items/', views.ItemListCreateAPIView.as_view(), name='api-item-list'),

    # --------------------------------------------------
    # PROTOTYPE / SAMPLE ROUTES (Bisa dihapus nanti)
    # --------------------------------------------------
    path('sample-order-form/', views.order_form_sample_view, name='order_form_sample'),
]