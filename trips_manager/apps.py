from django.apps import AppConfig
from django.conf import settings

cache = settings.SYSTEM_CACHE

class TripsManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trips_manager'

    def ready(self) -> None:
        from .models import TripStageChoices
        for stage in TripStageChoices.choices:
            cache.hset(settings.TRIP_STAGES_KEY , stage[1] , stage[0])
        return super().ready()