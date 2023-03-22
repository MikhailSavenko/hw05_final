from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache
from ..models import Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',

        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

        cls.user_two = User.objects.create_user(username='test-user_two')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)
        self.authorized_client_two = Client()
        self.authorized_client_two.force_login(PostPagesTests.user_two)
        cache.clear()

    def test_pages_correct_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        pages_template = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug':
                    f'{PostPagesTests.group.slug}'}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username':
                    f'{PostPagesTests.post.author}'}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id':
                    f'{PostPagesTests.post.id}'}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id':
                    f'{PostPagesTests.post.id}'}): 'posts/create_post.html',

        }
        for reverse_name, template in pages_template.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_detail_context(self):
        """post_detail контекст(пост отфильтрованный по id)"""
        response = reverse('posts:post_detail', kwargs={'post_id':
                                                        self.post.id})
        post = self.guest_client.get(response).context.get('post')
        self.assertEqual(post.pk, self.post.pk)

    def test_context(self):
        """context profile, group_post, index"""
        response = [
            reverse('posts:group_list', kwargs={'slug':
                                                self.group.slug}),
            reverse("posts:profile", args=(self.post.author,)),
            reverse('posts:index')
        ]
        for page in response:
            with self.subTest(page=page):
                post = self.guest_client.get(page).context.get("post")
                self.assert_post(post)

    def test_create_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:post_create"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:post_edit",
                                                      kwargs={'post_id':
                                                              self.post.id}))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_check_group_in_pages(self):
        """Проверяем создание group на страницах"""
        const = {'group': self.post.group}
        form_fields = {
            reverse('posts:index'): const,
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            const,
            reverse('posts:profile', kwargs={'username': self.user}):
            const,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                response.context['page_obj']
                self.assertTrue(Post.objects.filter(
                                group=self.post.group).exists())

    def test_post_in_expected_group(self):
        """Пост с группой попал в правильную группу"""
        const = {'group': self.post.group}
        response = self.authorized_client.get(reverse("posts:group_list",
                                              kwargs={'slug':
                                                      self.group.slug}))
        pages_context = {
            "group": const,
        }
        for value, expected in pages_context.items():
            with self.subTest(value=value):
                response.context["page_obj"]
                self.assertTrue(Post.objects.filter(
                                group=self.post.group).exists())

    def test_cach(self):
        """Проверка cach"""
        response = self.guest_client.get(reverse("posts:index"))
        first_resp = response.content
        Post.objects.get(id=1).delete()
        response_second = self.guest_client.get(reverse("posts:index"))
        second_resp = response_second.content
        cache.clear()
        after_clear = response_second.content
        self.assertEqual(first_resp, second_resp)
        self.assertNotEqual(response_second, after_clear)

    def assert_post(self, post):
        self.assertEqual(self.post.text, post.text)
        self.assertEqual(self.post.author, post.author)
        self.assertEqual(self.post.group, post.group)

    def test_follow_page(self):
        """Появляется запись в ленте тех кто подписан"""
        self.authorized_client_two.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username}))
        response = self.authorized_client_two.get(
            reverse('posts:follow_index'))
        self.assertContains(response, self.post.text)

    def test_not_follow_page(self):
        """Новая запись НЕ появляется у тех, кто не подписан"""
        response = self.authorized_client_two.get(
            reverse('posts:follow_index'))
        self.assertNotContains(response, self.post.text)
