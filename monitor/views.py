import os
import signal
from io import BytesIO
from typing import Optional

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from openpyxl import Workbook

from .models import KillLog, Snapshot
from .services import filter_and_sort_processes, get_processes, get_snapshot_chart_data


def _render_process_table(
    request: HttpRequest,
    *,
    processes: Optional[list[dict]] = None,
    error_message: Optional[str] = None,
    success_message: Optional[str] = None,
) -> HttpResponse:
    if processes is None:
        processes = get_processes()

    context = {
        "processes": processes,
        "error_message": error_message,
        "success_message": success_message,
    }
    return render(request, "monitor/partials/process_table.html", context)


@login_required
def process_list(request: HttpRequest) -> HttpResponse:
    return render(request, "monitor/processes.html")


@login_required
def process_list_partial(request: HttpRequest) -> HttpResponse:
    processes = get_processes()
    filter_and_sort_processes(
        processes,
        pid=request.GET.get("pid") or None,
        name=request.GET.get("name") or None,
        status=request.GET.get("status") or None,
        sort=request.GET.get("sort") or None,
    )
    return _render_process_table(request, processes=processes)


@login_required
@require_http_methods(["POST"])
def kill_process(request: HttpRequest, pid: int) -> HttpResponse:
    error_message: Optional[str] = None
    processes = get_processes()

    process_name: Optional[str] = None
    for process in processes:
        if process.get("pid") == pid:
            process_name = process.get("name")
            break

    try:
        os.kill(pid, signal.SIGTERM)
        if process_name:
            KillLog.objects.create(
                author=request.user,  # type: ignore[misc]
                process_name=process_name,
                pid=pid,
            )
    except ProcessLookupError:
        error_message = "Process not found."
    except PermissionError:
        error_message = "Permission denied."
    except Exception as e:
        error_message = str(e)

    return _render_process_table(request, processes=processes, error_message=error_message)


@login_required
@require_http_methods(["POST"])
def take_snapshot(request: HttpRequest) -> HttpResponse:
    processes = get_processes()
    Snapshot.objects.create(author=request.user, data=processes)  # type: ignore[misc]
    return _render_process_table(
        request,
        processes=processes,
        success_message="Snapshot taken.",
    )


@login_required
def kill_log_list(request: HttpRequest) -> HttpResponse:
    logs = KillLog.objects.select_related("author").all()
    return render(request, "monitor/kill_log.html", {"logs": logs})


@login_required
def snapshot_list(request: HttpRequest) -> HttpResponse:
    snapshots = Snapshot.objects.select_related("author").all()
    chart_data = get_snapshot_chart_data(snapshots)
    return render(
        request,
        "monitor/snapshot_list.html",
        {"snapshots": snapshots, **chart_data},
    )


@login_required
def snapshot_detail(request: HttpRequest, pk: int) -> HttpResponse:
    snapshot = get_object_or_404(Snapshot.objects.select_related("author"), pk=pk)
    processes = snapshot.data or []
    return render(
        request,
        "monitor/snapshot_detail.html",
        {
            "snapshot": snapshot,
            "processes": processes,
        },
    )


@login_required
def snapshot_export_excel(request: HttpRequest, pk: int) -> HttpResponse:
    snapshot = get_object_or_404(Snapshot.objects.select_related("author"), pk=pk)
    processes = snapshot.data or []

    wb = Workbook()
    ws = wb.active
    ws.title = "Processes"

    headers = [
        "PID",
        "Name",
        "Status",
        "Start Time",
        "Duration",
        "CPU (%)",
        "Memory (MB)",
    ]
    ws.append(headers)

    for p in processes:
        ws.append(
            [
                p.get("pid"),
                p.get("name"),
                p.get("status"),
                p.get("start_time"),
                p.get("duration"),
                p.get("cpu"),
                p.get("memory"),
            ]
        )

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )
    filename = f"snapshot_{snapshot.id}_{snapshot.created_at:%Y%m%d_%H%M%S}.xlsx"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
