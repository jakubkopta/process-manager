from django.contrib import admin

from .models import KillLog, Snapshot


@admin.register(Snapshot)
class SnapshotAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "created_at")
    list_filter = ("author", "created_at")
    ordering = ("-created_at",)


@admin.register(KillLog)
class KillLogAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "process_name", "pid", "created_at")
    list_filter = ("author", "created_at")
    ordering = ("-created_at",)

