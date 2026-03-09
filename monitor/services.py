from datetime import datetime, timezone
from typing import Optional

import psutil


def get_processes() -> list[dict]:
    processes = []
    now = datetime.now(timezone.utc)

    for proc in psutil.process_iter(
        [
            "pid",
            "name",
            "status",
            "create_time",
            "memory_info",
            "cpu_percent",
        ]
    ):
        try:
            pid = proc.info["pid"]

            if pid == 0:
                continue

            start_time = datetime.fromtimestamp(
                proc.info["create_time"],
                tz=timezone.utc,
            )

            duration = now - start_time

            memory_info = proc.info.get("memory_info")

            memory_mb = 0
            if memory_info:
                memory_mb = memory_info.rss / 1024 / 1024

            processes.append(
                {
                    "pid": pid,
                    "name": proc.info.get("name", ""),
                    "status": proc.info.get("status", ""),
                    "cpu": proc.info.get("cpu_percent", 0),
                    "memory": round(memory_mb, 2),
                    "start_time": start_time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "duration": str(duration).split(".")[0],
                }
            )

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
            KeyError,
            AttributeError,
        ):
            continue

    return processes


def filter_and_sort_processes(
    processes: list[dict],
    *,
    pid: Optional[str] = None,
    name: Optional[str] = None,
    status: Optional[str] = None,
    sort: Optional[str] = None,
) -> list[dict]:
    if pid:
        try:
            pid_int = int(pid)
            processes[:] = [p for p in processes if p.get("pid") == pid_int]
        except ValueError:
            processes.clear()

    if name:
        name_lower = name.lower()
        processes[:] = [
            p for p in processes
            if name_lower in str(p.get("name", "")).lower()
        ]

    if status:
        status_lower = status.lower()
        processes[:] = [
            p for p in processes
            if str(p.get("status", "")).lower() == status_lower
        ]

    if sort:
        reverse = sort.startswith("-")
        field = sort.lstrip("-")
        if field in {"pid", "cpu", "memory"}:
            processes.sort(
                key=lambda p: float(p.get(field) or 0),
                reverse=reverse,
            )
        elif field == "name":
            processes.sort(
                key=lambda p: str(p.get("name", "")).lower(),
                reverse=reverse,
            )

    return processes


def get_snapshot_chart_data(snapshots) -> dict:
    labels: list[str] = []
    cpu: list[float] = []
    memory: list[float] = []
    process_count: list[int] = []

    for snapshot in snapshots.order_by("created_at"):
        processes = snapshot.data or []
        total_cpu = 0.0
        total_memory = 0.0

        for p in processes:
            try:
                total_cpu += float(p.get("cpu") or 0)
            except (TypeError, ValueError):
                pass
            try:
                total_memory += float(p.get("memory") or 0)
            except (TypeError, ValueError):
                pass

        labels.append(snapshot.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        cpu.append(round(total_cpu, 2))
        memory.append(round(total_memory, 2))
        process_count.append(len(processes))

    return {
        "chart_labels": labels,
        "chart_cpu": cpu,
        "chart_memory": memory,
        "chart_process_count": process_count,
    }
