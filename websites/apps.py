from django.apps import AppConfig

class WebsitesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "websites"          
    verbose_name = "Websites"

    def ready(self):
        import websites.signals  
