from http import HTTPStatus
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="test-user")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовая пост",
            group=cls.group,
        )
        cls.user_two = User.objects.create(username="test-user-two")

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(StaticURLTests.user)
        self.authorized_client_two = Client()
        self.authorized_client_two.force_login(StaticURLTests.user_two)
        self.author = Client()
        self.author.force_login(StaticURLTests.post.author)
        cache.clear()

    def test_urls_correct_status(self):
        """Проверяем работу страниц, доступных всем"""
        url_names = {
            "/": HTTPStatus.OK,
            "/group/test-slug/": HTTPStatus.OK,
            "/profile/test-user/": HTTPStatus.OK,
            f"/posts/{StaticURLTests.post.id}/": HTTPStatus.OK,
        }
        for adress, status in url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, status)

    def test_urls_redirect_guest_client(self):
        """Редирект неавторизованного пользователя к ограниченным страницам"""
        url1 = '/auth/login/?next=/create/'
        url2 = f'/auth/login/?next=/posts/{StaticURLTests.post.id}/edit/'
        pages = {'/create/': url1,
                 f'/posts/{StaticURLTests.post.id}/edit/': url2}
        for page, value in pages.items():
            response = self.guest_client.get(page)
            self.assertRedirects(response, value)

    def test_authorized_client(self):
        """Доступ авторизованного пользователя к ограниченным страницам"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_client(self):
        """Доступ к странице, только для автора поста"""
        response = self.author.get(f'/posts/{StaticURLTests.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_uses_template(self):
        """Шаблоны"""
        template_url = {
            '/': 'posts/index.html',
            f'/group/{StaticURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{StaticURLTests.post.author}/': 'posts/profile.html',
            f'/posts/{StaticURLTests.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{StaticURLTests.post.id}/edit/': 'posts/create_post.html'}
        for adress, template in template_url.items():
            with self.subTest(adress=adress):
                response = self.author.get(adress)
                self.assertTemplateUsed(response, template)

    def test_error_404_not_found(self):
        """Проверка запроса и шаблоны к несуществующей страницы"""
        response = self.guest_client.get('/akrobat/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_follow_authorized_client(self):
        """Авторизованный пользователь может подписываться и отписывапться"""
        response = self.authorized_client_two.get(
            reverse('posts:profile_follow',
                    kwargs={'username': f'{self.user.username}'}
                    ))
        response2 = self.authorized_client_two.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': f'{self.user.username}'}
                    ))
        self.assertRedirects(response, '/follow/')
        self.assertRedirects(response2, '/follow/')
