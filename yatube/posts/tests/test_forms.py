from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post
from http import HTTPStatus

User = get_user_model()


class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create(username='test-user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',

        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',

        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTest.user)

    def test_form_create_post_plus(self):
        """Пост создается в базе при создании поста с create_post"""
        post_count = Post.objects.count()
        form_data = {"text": "Тестовый пост"}
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data, follow=True)
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertRedirects(response, reverse("posts:profile",
                                               kwargs={"username":
                                                       self.user.username}))

    def test_post_edit_form(self):
        """Форма изменяет запись"""
        post_count = Post.objects.count()
        form_data = {"text": "Измененный текст", "group": 1}
        response = self.authorized_client.post(
            reverse("posts:post_edit", args=({self.post.id})),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(Post.objects.filter(text="Измененный текст").exists())
        self.assertEqual(response.status_code, HTTPStatus.OK)
