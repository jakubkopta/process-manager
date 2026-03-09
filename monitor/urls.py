from django.urls import path

from . import views

urlpatterns = [
    path("", views.process_list, name="process_list"),
    path("partials/processes/", views.process_list_partial, name="process_list_partial"),
    path("kill/<int:pid>/", views.kill_process, name="kill_process"),
    path("snapshots/take/", views.take_snapshot, name="take_snapshot"),
    path("snapshots/", views.snapshot_list, name="snapshot_list"),
    path("snapshots/<int:pk>/", views.snapshot_detail, name="snapshot_detail"),
    path("snapshots/<int:pk>/export/", views.snapshot_export_excel, name="snapshot_export_excel"),
    path("kill-log/", views.kill_log_list, name="kill_log_list"),
]
