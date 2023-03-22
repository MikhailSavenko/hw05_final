from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from yatube.settings import POSTS_ON_PAGES_FIRST, POSTS_ON_PAGES_SECOND

from ..models import Group, Post

User = get_user_model()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='AAAA')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',

        )
        bulk_posts = [
            Post(
                text=f'Пост номер {i}',
                author=cls.user,
                group=cls.group,
            )
            for i in range(13)
        ]
        cls.post = Post.objects.bulk_create(bulk_posts)
        cls.pages = [reverse('posts:index'),
                     reverse('posts:group_list',
                     kwargs={'slug': cls.group.slug}),
                     reverse("posts:profile", args=(cls.user.username,))]

    def setUp(self):
        self.guest_client = Client()

    def test_paginaror_pages_first(self):
        """Пагинатор отрбражает 10/13 постов на странице"""
        for page in self.pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(len(response.context['page_obj']),
                                 POSTS_ON_PAGES_FIRST)

    def test_paginaror_pages_second(self):
        """Пагинатор отрбражает 3/13 постов на странице"""
        for page in self.pages:
            page = f'{page}?page=2'
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(len(response.context['page_obj']),
                                 POSTS_ON_PAGES_SECOND)
