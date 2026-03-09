from typing import cast

from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.test import Client, TestCase
from django.urls import reverse

from .models import KillLog, Snapshot
from .services import get_processes

User = get_user_model()


class GetProcessesTests(TestCase):
    def test_returns_list(self) -> None:
        result = get_processes()
        self.assertIsInstance(result, list)

    def test_items_have_expected_keys(self) -> None:
        result = get_processes()
        expected_keys = {"pid", "name", "status", "cpu", "memory", "start_time", "duration"}
        for item in result:
            self.assertIsInstance(item, dict)
            self.assertEqual(set(item.keys()), expected_keys, f"Item keys: {item.keys()}")

    def test_no_pid_zero(self) -> None:
        result = get_processes()
        pids = [p["pid"] for p in result]
        self.assertNotIn(0, pids)


class ViewAuthTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_process_list_redirects_when_anonymous(self) -> None:
        response = self.client.get(reverse("process_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", cast(HttpResponseRedirect, response).url)

    def test_process_list_partial_redirects_when_anonymous(self) -> None:
        response = self.client.get(reverse("process_list_partial"))
        self.assertEqual(response.status_code, 302)

    def test_snapshot_list_redirects_when_anonymous(self) -> None:
        response = self.client.get(reverse("snapshot_list"))
        self.assertEqual(response.status_code, 302)

    def test_kill_log_list_redirects_when_anonymous(self) -> None:
        response = self.client.get(reverse("kill_log_list"))
        self.assertEqual(response.status_code, 302)

    def test_take_snapshot_post_redirects_when_anonymous(self) -> None:
        response = self.client.post(reverse("take_snapshot"))
        self.assertEqual(response.status_code, 302)

    def test_kill_process_post_redirects_when_anonymous(self) -> None:
        response = self.client.post(reverse("kill_process", kwargs={"pid": 99999999}))
        self.assertEqual(response.status_code, 302)


class ViewProcessListTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client = Client()
        self.client.force_login(self.user)

    def test_process_list_returns_200(self) -> None:
        response = self.client.get(reverse("process_list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Process Manager", response.content)

    def test_process_list_partial_returns_200(self) -> None:
        response = self.client.get(reverse("process_list_partial"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Last refresh", response.content)

    def test_process_list_partial_filter_pid_empty_invalid(self) -> None:
        response = self.client.get(reverse("process_list_partial"), {"pid": "not-a-number"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No processes found", response.content)


class ViewSnapshotTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client = Client()
        self.client.force_login(self.user)

    def test_take_snapshot_creates_snapshot(self) -> None:
        count_before = Snapshot.objects.count()
        response = self.client.post(reverse("take_snapshot"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Snapshot.objects.count(), count_before + 1)
        self.assertIn(b"Snapshot taken", response.content)

    def test_snapshot_list_returns_200(self) -> None:
        response = self.client.get(reverse("snapshot_list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Snapshots", response.content)

    def test_snapshot_detail_returns_200(self) -> None:
        snapshot = Snapshot.objects.create(author=self.user, data=[{"pid": 1, "name": "test"}])
        response = self.client.get(reverse("snapshot_detail", kwargs={"pk": snapshot.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Snapshot details", response.content)
        self.assertIn(b"test", response.content)

    def test_snapshot_export_excel_returns_xlsx(self) -> None:
        snapshot = Snapshot.objects.create(author=self.user, data=[{"pid": 1, "name": "test"}])
        response = self.client.get(reverse("snapshot_export_excel", kwargs={"pk": snapshot.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "spreadsheetml.sheet",
            response.get("Content-Type", ""),
        )
        self.assertIn("attachment", response.get("Content-Disposition", ""))
        self.assertTrue(len(response.content) > 100)


class ViewKillLogTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client = Client()
        self.client.force_login(self.user)

    def test_kill_log_list_returns_200(self) -> None:
        response = self.client.get(reverse("kill_log_list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Kill Log", response.content)

    def test_kill_log_list_shows_entries(self) -> None:
        KillLog.objects.create(author=self.user, process_name="python", pid=1234)
        response = self.client.get(reverse("kill_log_list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"python", response.content)
        self.assertIn(b"1234", response.content)


class KillProcessViewTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client = Client()
        self.client.force_login(self.user)

    def test_kill_nonexistent_pid_returns_200_with_error_message(self) -> None:
        response = self.client.post(
            reverse("kill_process", kwargs={"pid": 99999999}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Process not found", response.content)

    def test_kill_process_get_returns_405(self) -> None:
        response = self.client.get(reverse("kill_process", kwargs={"pid": 99999999}))
        self.assertEqual(response.status_code, 405)
