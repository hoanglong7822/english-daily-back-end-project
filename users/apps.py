from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        import playground  # noqa: F401 - chạy playground.py mỗi khi server start/restart
