from django.urls import path
from src.api import views as api_views

urlpatterns = [
    path(
        "offers",
        api_views.Offer.as_view(),
        name="p2p-bot.offer",
    ),
    path(
        "offers/<str:offer_id>",
        api_views.Offer.as_view(),
        name="p2p-bot.single_offer",
    ),
]
