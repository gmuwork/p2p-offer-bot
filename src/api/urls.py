from django.urls import path

from src.api.views import config as config_api_views
from src.api.views import offer as offer_api_views

urlpatterns = [
    path(
        "offers",
        offer_api_views.Offer.as_view(),
        name="p2p-bot.offer",
    ),
    path(
        "offers/<str:offer_id>",
        offer_api_views.Offer.as_view(),
        name="p2p-bot.single_offer",
    ),
    path(
        "configs",
        config_api_views.Config.as_view(),
        name="p2p-bot.config",
    ),
]
