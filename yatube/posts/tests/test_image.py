from posts.models import Post, Group
import shutil
import tempfile
from django.contrib.auth import get_user_model
from posts.forms import PostForm
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormImageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='1')
        cls.posts_count = Post.objects.count()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',

        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=(
                 b'\x47\x49\x46\x38\x39\x61\x02\x00'
                 b'\x01\x00\x80\x00\x00\x00\x00\x00'
                 b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                 b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                 b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                 b'\x0A\x00\x3B'
            ),
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый текст',
            image=cls.image,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormImageTest.user)

    def test_image_in_context(self):
        """Проверяем image в context"""
        form_data = {
            'author': '1',
            'group': self.group,
            'text': 'Тестовый текст',
            'image': self.image,
        }
        responses = [reverse('posts:index'),
                     reverse('posts:post_detail', kwargs={'post_id':
                                                          self.post.id}),
                     reverse('posts:group_list', kwargs={'slug':
                                                         self.group.slug}),
                     reverse("posts:profile", args=(self.post.author,))]
        for response in responses:
            post = self.guest_client.post(response, data=form_data)
            with self.subTest(post=post):
                self.assertTrue(
                    Post.objects.filter(
                        author='1',
                        group=self.group,
                        text='Тестовый текст',
                        image='posts/small.gif'
                    ).exists()
                )
                self.assertEqual(Post.objects.count(), self.posts_count + 1)

    def test_create_image_post(self):
        """При создании поста с картинкой создаётся запись в базе данных"""
        form_data = {
            "text": "Тестовый текст",
            "group": self.group,
            "image": self.image,
        }
        self.authorized_client.post(reverse('posts:post_create'),
                                    data=form_data, follow=True)
        self.assertEqual(Post.objects.count(), self.posts_count + 1)
