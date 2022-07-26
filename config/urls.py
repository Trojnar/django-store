from django.conf import settings
from django.conf.urls.static import static
from django import urls
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("imnotanadminpage/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("accounts/", include("accounts.urls")),
    path("products/", include("products.urls")),
    path("products/reviews/", include("reviews.urls")),
    path("transactions/", include("transactions.urls")),
    path("categories/", include("categories.urls")),
    path("images/", include("images.urls")),
    path("", include("pages.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
