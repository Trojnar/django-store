from django.urls import path
from .views import (
    CategoryListView,
    CategoryDeleteView,
    CategoryCreateView,
    CategoryUpdateView,
    CategoryDetailsView,
    CategoryManageProductsView,
)

urlpatterns = [
    path("", CategoryListView.as_view(), name="category_list"),
    path(
        "delete/<int:pk>",
        CategoryDeleteView.as_view(),
        name="category_delete",
    ),
    path(
        "update/<int:pk>",
        CategoryUpdateView.as_view(),
        name="category_update",
    ),
    path("create", CategoryCreateView.as_view(), name="category_create"),
    path("<int:pk>", CategoryDetailsView.as_view(), name="category_details"),
    path(
        "<int:pk>/checkbox",
        CategoryManageProductsView.as_view(),
        name="category_checkbox",
    ),
]
