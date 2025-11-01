# alx_travel_app/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # your listings app routes for API
    # (your current listings/urls.py is payments-related, but we can still include it)
    path("api/", include("alx_travel_app.listings.urls", namespace="payments")),
]
