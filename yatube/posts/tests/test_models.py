from django.contrib.auth import get_user_model
from django.test import TestCase

from yatube.settings import LEN_OF_POSTS

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='alla')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Длинный тестовый пост, очень длинный',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )

    def test_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        post = PostModelTest.post
        vals = [
            (str(post), post.text[:LEN_OF_POSTS]),
            (str(group), group.title)
        ]
        for value, exp in vals:
            with self.subTest(value=value):
                self.assertEqual(value, exp)
