from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MagiaViewSet, PersonagemViewSet

router = DefaultRouter()
router.register(r"personagens", PersonagemViewSet, basename="personagem")
router.register(r"magias", MagiaViewSet, basename="magia")

urlpatterns = [
    path("", include(router.urls)),
]
