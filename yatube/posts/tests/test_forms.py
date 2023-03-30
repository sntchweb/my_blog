import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


TEST_USER = 'test_forms'
TEST_AUTHOR = 'test_forms_author'
TEST_POST_TEXT = 'Test post text'
TEST_1ST_GROUP_TITLE = 'Test first group title'
TEST_2ND_GROUP_TITLE = 'Test second group title'
GROUP_1_SLUG = 'test-first-group-slug'
GROUP_2_SLUG = 'test-second-group-slug'
TEST_1ST_GROUP_DESCRIPTION = 'Test first group description'
TEST_2ND_GROUP_DESCRIPTION = 'Test second group description'
NEW_TEXT = 'Test form text'
CHANGED_TEXT = 'Changed test form text'
COMMENT_TEXT = 'Test comment text'
POSTS_MEDIA_FOLDER = 'posts/'
TEST_IMAGE_NAME = 'small.gif'

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)

PROFILE_URL = reverse('posts:profile', args=[TEST_USER])
POST_CREATE_URL = reverse('posts:post_create')
INDEX_URL = reverse('posts:index')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USER)
        cls.author = User.objects.create_user(username=TEST_AUTHOR)
        cls.post = Post.objects.create(
            text=TEST_POST_TEXT,
            author=cls.author,
            group=Group.objects.create(
                title=TEST_1ST_GROUP_TITLE,
                slug=GROUP_1_SLUG,
                description=TEST_1ST_GROUP_DESCRIPTION
            )
        )
        cls.new_group = Group.objects.create(
            title=TEST_2ND_GROUP_TITLE,
            slug=GROUP_2_SLUG,
            description=TEST_2ND_GROUP_DESCRIPTION
        )
        cls.test_text = NEW_TEXT
        cls.test_changed_text = CHANGED_TEXT
        cls.comment_text = COMMENT_TEXT
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=[cls.post.pk])
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.pk])
        cls.ADD_COMMENT_URL = reverse('posts:add_comment', args=[cls.post.pk])
        cls.POST_COMMENT_REDIRECT_URL = (
            f'/auth/login/?next=/posts/{cls.post.pk}/comment/'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_post_author = Client()
        self.authorized_post_author.force_login(self.post.author)

    def test_create_post_from(self):
        """Валидная форма создает запись."""
        posts_count = Post.objects.count()
        uploaded_image = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': NEW_TEXT,
            'group': self.post.group.id,
            'image': uploaded_image,
        }
        response = self.authorized_client.post(
            POST_CREATE_URL,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, PROFILE_URL)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.get(
            text=NEW_TEXT,
            group=self.post.group.id,
            image=f'{POSTS_MEDIA_FOLDER}{TEST_IMAGE_NAME}'
        )
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.image, f'{POSTS_MEDIA_FOLDER}{TEST_IMAGE_NAME}')

    def test_author_can_edit_post(self):
        """Автор поста может редактировать текст и менять группу."""
        form_data = {
            'text': CHANGED_TEXT,
            'group': self.new_group.id
        }
        response_edit = self.authorized_post_author.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True,
        )
        post_change = Post.objects.get(pk=self.post.pk)
        self.assertEqual(post_change.text, form_data['text'])
        self.assertEqual(post_change.group.id, form_data['group'])
        self.assertRedirects(response_edit, self.POST_DETAIL_URL)

    def test_write_comment_can_only_authorized_user(self):
        """Писать комментарии может только авторизованный пользвоатель."""
        form_data = {'text': COMMENT_TEXT}
        post_comments = 0
        self.authorized_client.post(
            self.ADD_COMMENT_URL,
            data=form_data,
            follow=True
        )
        post = Post.objects.get(pk=self.post.pk)
        total_post_comments = post.comments.count()
        self.assertEqual(total_post_comments, post_comments + 1)

    def test_guest_cant_write_comments(self):
        """Неавторизованный пользователь не может писать комментарии."""
        form_data = {'text': COMMENT_TEXT}
        response = self.guest_client.post(
            self.ADD_COMMENT_URL,
            data=form_data,
            follow=True
        )
        post = Post.objects.get(pk=self.post.pk)
        total_post_comments = post.comments.count()
        self.assertEqual(total_post_comments, 0)
        self.assertRedirects(response, self.POST_COMMENT_REDIRECT_URL)
