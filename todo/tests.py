from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from todo.forms import TaskForm
from todo.models import Tag, Task


class TaskModelTests(TestCase):
    def test_str_returns_content(self):
        task = Task.objects.create(content="Buy milk")
        self.assertEqual(str(task), "Buy milk")

    def test_defaults(self):
        task = Task.objects.create(content="Buy milk")
        self.assertFalse(task.is_done)
        self.assertIsNone(task.deadline)
        self.assertIsNotNone(task.created_at)

    def test_ordering_not_done_first_then_newest(self):
        now = timezone.now()
        old_done = Task.objects.create(content="old done", is_done=True)
        new_done = Task.objects.create(content="new done", is_done=True)
        old_open = Task.objects.create(content="old open")
        new_open = Task.objects.create(content="new open")
        for i, task in enumerate([old_done, new_done, old_open, new_open]):
            Task.objects.filter(pk=task.pk).update(
                created_at=now + timedelta(minutes=i)
            )

        self.assertEqual(
            list(Task.objects.all()),
            [new_open, old_open, new_done, old_done],
        )

    def test_task_can_have_many_tags_and_tag_many_tasks(self):
        home = Tag.objects.create(name="home")
        shop = Tag.objects.create(name="shop")
        first = Task.objects.create(content="first")
        second = Task.objects.create(content="second")
        first.tags.add(home, shop)
        second.tags.add(shop)

        self.assertEqual(first.tags.count(), 2)
        self.assertEqual(set(shop.tasks.all()), {first, second})


class TagModelTests(TestCase):
    def test_str_returns_name(self):
        self.assertEqual(str(Tag.objects.create(name="work")), "work")


class TaskFormTests(TestCase):
    def test_tags_are_optional(self):
        form = TaskForm(data={"content": "No tags"})
        self.assertTrue(form.is_valid(), form.errors)

    def test_content_is_required(self):
        form = TaskForm(data={"content": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("content", form.errors)


class TaskViewTests(TestCase):
    def setUp(self):
        self.tag = Tag.objects.create(name="shop")
        self.task = Task.objects.create(content="Buy carrots")
        self.task.tags.add(self.tag)

    def test_home_page_lists_tasks_with_tags(self):
        response = self.client.get(reverse("todo:task-list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "todo/task_list.html")
        self.assertContains(response, "Buy carrots")
        self.assertContains(response, "shop")
        self.assertContains(response, "Not done")
        self.assertContains(response, "Complete")

    def test_home_page_is_root_url(self):
        self.assertEqual(reverse("todo:task-list"), "/")

    def test_home_page_query_count_does_not_grow_with_tasks(self):
        for i in range(5):
            Task.objects.create(content=f"Task {i}").tags.add(self.tag)

        with self.assertNumQueries(2):
            self.client.get(reverse("todo:task-list"))

    def test_create_task(self):
        response = self.client.post(
            reverse("todo:task-create"),
            {"content": "Clean windows", "tags": [self.tag.pk]},
        )

        self.assertRedirects(response, reverse("todo:task-list"))
        task = Task.objects.get(content="Clean windows")
        self.assertEqual(list(task.tags.all()), [self.tag])

    def test_update_task(self):
        response = self.client.post(
            reverse("todo:task-update", args=[self.task.pk]),
            {"content": "Buy 3 carrots", "is_done": "on"},
        )

        self.assertRedirects(response, reverse("todo:task-list"))
        self.task.refresh_from_db()
        self.assertEqual(self.task.content, "Buy 3 carrots")
        self.assertTrue(self.task.is_done)
        self.assertEqual(self.task.tags.count(), 0)

    def test_delete_task_needs_confirmation(self):
        url = reverse("todo:task-delete", args=[self.task.pk])

        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())

        response = self.client.post(url)
        self.assertRedirects(response, reverse("todo:task-list"))
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())

    def test_toggle_switches_status_both_ways(self):
        url = reverse("todo:task-toggle", args=[self.task.pk])

        response = self.client.post(url)
        self.assertRedirects(response, reverse("todo:task-list"))
        self.task.refresh_from_db()
        self.assertTrue(self.task.is_done)

        self.client.post(url)
        self.task.refresh_from_db()
        self.assertFalse(self.task.is_done)

    def test_toggle_rejects_get(self):
        response = self.client.get(
            reverse("todo:task-toggle", args=[self.task.pk])
        )

        self.assertEqual(response.status_code, 405)
        self.task.refresh_from_db()
        self.assertFalse(self.task.is_done)

    def test_toggle_missing_task_returns_404(self):
        response = self.client.post(reverse("todo:task-toggle", args=[999]))
        self.assertEqual(response.status_code, 404)


class TagViewTests(TestCase):
    def setUp(self):
        self.tag = Tag.objects.create(name="home")

    def test_tag_list_page(self):
        response = self.client.get(reverse("todo:tag-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(reverse("todo:tag-list"), "/tags/")
        self.assertContains(response, "home")

    def test_create_tag(self):
        response = self.client.post(reverse("todo:tag-create"), {"name": "work"})

        self.assertRedirects(response, reverse("todo:tag-list"))
        self.assertTrue(Tag.objects.filter(name="work").exists())

    def test_tag_names_are_unique(self):
        response = self.client.post(reverse("todo:tag-create"), {"name": "home"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Tag.objects.filter(name="home").count(), 1)

    def test_update_tag(self):
        response = self.client.post(
            reverse("todo:tag-update", args=[self.tag.pk]), {"name": "house"}
        )

        self.assertRedirects(response, reverse("todo:tag-list"))
        self.tag.refresh_from_db()
        self.assertEqual(self.tag.name, "house")

    def test_delete_tag_keeps_its_tasks(self):
        task = Task.objects.create(content="Clean room")
        task.tags.add(self.tag)

        response = self.client.post(
            reverse("todo:tag-delete", args=[self.tag.pk])
        )

        self.assertRedirects(response, reverse("todo:tag-list"))
        self.assertFalse(Tag.objects.filter(pk=self.tag.pk).exists())
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())
        self.assertEqual(task.tags.count(), 0)


class SidebarTests(TestCase):
    def test_sidebar_links_on_every_page(self):
        task = Task.objects.create(content="Task")
        tag = Tag.objects.create(name="tag")
        urls = [
            reverse("todo:task-list"),
            reverse("todo:task-create"),
            reverse("todo:task-update", args=[task.pk]),
            reverse("todo:task-delete", args=[task.pk]),
            reverse("todo:tag-list"),
            reverse("todo:tag-create"),
            reverse("todo:tag-update", args=[tag.pk]),
            reverse("todo:tag-delete", args=[tag.pk]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, 'href="/"')
                self.assertContains(response, 'href="/tags/"')
