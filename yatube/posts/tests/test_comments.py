from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from ..models import Group, Post, Comment

User = get_user_model()


class CommentTest(TestCase):
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

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(CommentTest.user)

    def test_comment_authorized_client(self):
        """Редирект при post запросе комментария"""
        response = self.authorized_client.post('/posts/1/comment/',
                                               follow=True)
        self.assertRedirects(response, '/posts/1/')

    def test_comment_guest_client(self):
        """Редирект при get запросе неовтаризованного пользователя"""
        response = self.guest_client.get('/posts/1/comment/')
        self.assertRedirects(response, '/auth/login/?next=/posts/1/comment/')

    def test_comment_context(self):
        """При отправке комментария, он появляется на странице"""
        data_context = {
            'text': 'Тестовый комментарий'
        }
        response = self.authorized_client.post(reverse('posts:add_comment',
                                               kwargs={'post_id':
                                                       self.post.id}),
                                               data=data_context,
                                               follow=True)
        comment = Comment.objects.latest('id')
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(comment.text, data_context['text'])
        self.assertEqual(response.status_code, 200)
