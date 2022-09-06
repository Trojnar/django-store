from django.urls import path
from .views import (
    CartView,
    TransactionView,
    TransactionsUserListView,
)

urlpatterns = [
    path(
        "cart/<int:pk>",
        CartView.as_view(),
        name="cart_details",
    ),
    path(
        "cart/<int:pk>",
        CartView.as_view(),
        name="cart_details",
    ),
    path(
        "transaction/<int:pk>",
        TransactionView.as_view(),
        name="transaction",
    ),
    path(
        "transactions",
        TransactionsUserListView.as_view(),
        name="transaction_history",
    ),
]
