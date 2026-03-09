from django.conf import settings
from django.db import models


class Snapshot(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="snapshots",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Snapshot {self.id} by {self.author} at {self.created_at:%Y-%m-%d %H:%M:%S}"


class KillLog(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="kill_logs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    process_name = models.CharField(max_length=255)
    pid = models.IntegerField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Kill {self.process_name} ({self.pid}) by {self.author} at {self.created_at:%Y-%m-%d %H:%M:%S}"
