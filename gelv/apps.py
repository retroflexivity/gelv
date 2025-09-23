from django.apps import AppConfig


class GelvConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gelv'

    def ready(self):
        import gelv.admin.admin_models  # noqa
        import gelv.signals  # noqa
