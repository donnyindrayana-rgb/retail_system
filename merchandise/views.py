from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from rest_framework import generics

from .models import Item
from .serializers import ItemSerializer


# ==========================================
# MERCHANDISE API VIEWS
# ==========================================

class ItemListCreateAPIView(generics.ListCreateAPIView):
    """
    API View untuk mendapatkan list item dan membuat item baru.
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


# ==========================================
# PROTOTYPE / SAMPLE VIEWS
# ==========================================

@staff_member_required
def order_form_sample_view(request):
    """
    View prototipe sampel Order Form Excel untuk peninjauan UI/UX Unfold Admin.
    Dapat dihapus dengan aman setelah peninjauan selesai.
    """
    context = {
        'page_title': 'Sample Excel Order Form',
    }
    return render(request, 'admin/order_form_sample.html', context)


# Alias untuk kompatibilitas nama view jika dipanggil di urls.py
sample_order_form_view = order_form_sample_view