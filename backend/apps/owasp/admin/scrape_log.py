from django.contrib import admin
from apps.owasp.models.scrape_log import ScrapeLog

@admin.register(ScrapeLog)
class ScrapeLogAdmin(admin.ModelAdmin):
    list_display = ("target_url", "status", "duration", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("target_url", "error_message")
    readonly_fields = ("created_at",)
