from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'

    def ready(self):
        # عند إقلاع التطبيق نقوم بتحميل ملف signals حتى تُسجَّل الإشارات
        from . import signals  # noqa: F401
