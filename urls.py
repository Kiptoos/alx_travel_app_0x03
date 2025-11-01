# alx_travel_app/urls.py (project-level)
from django.contrib import admin
from django.urls import path, include

urlpatterns = [path("admin/", admin.site.urls),
    path("api/", include("alx_travel_app.listings.urls", namespace="listings")),
    path("api/", include("listings.urls", namespace="payments")),]
