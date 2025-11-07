from django.apps import AppConfig


class HarvestLmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'harvest_lms'

def ready(self):
    import harvest_lms.signals