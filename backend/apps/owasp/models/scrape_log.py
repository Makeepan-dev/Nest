from django.db import models

class ScrapeLog(models.Model):
    """Log for OWASP project scraping tasks."""

    target_url = models.URLField(max_length=500)
    status = models.CharField(
        max_length=20,
        choices=[
            ("SUCCESS", "Success"),
            ("FAILURE", "Failure"),
            ("PARTIAL", "Partial Success"),
        ],
        default="SUCCESS"
    )
    duration = models.FloatField(help_text="Duration in seconds", null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Scrape Log"
        verbose_name_plural = "Scrape Logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.target_url} - {self.status} ({self.created_at})"
