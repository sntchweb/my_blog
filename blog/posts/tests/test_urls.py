from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User

from blog.urls import handler404

GROUP_SLUG = 'test_group'
TEST_USER = 'test_urls1'
TEST_AUTHOR = 'test_urls0'
TEST_POST_TEXT = 'Test post text'
TEST_GROUP_TITLE = 'Test group title'
TEST_GROUP_DESCRIPTION = 'Test group description'

INDEX_URL = reverse('posts:index')
GROUP_URL = reverse('posts:group_list', args=[GROUP_SLUG])
PROFILE_URL = reverse('posts:profile', args=[TEST_USER])
POST_CREATE_URL = reverse('posts:post_create')
POST_CREATE_REDIRECT_URL = '/auth/login/?next=/create/'
UNEXISTING_PAGE_URL = '/bad/address/'
CUSTOM_404_PAGE_URL = handler404

INDEX_TEMPLATE = 'posts/index.html'
GROUP_TEMPLATE = 'posts/group_list.html'
PROFILE_TEMPLATE = 'posts/profile.html'
POST_DETAIL_TEMPLATE = 'posts/post_detail.html'
CUSTOM_404_PAGE_TEMPLATE = 'core/404.html'
CUSTOM_403_PAGE_TEMPLATE = 'core/403csrf.html'


class PostURLSTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USER)
        cls.author = User.objects.create_user(username=TEST_AUTHOR)
        cls.post = Post.objects.create(
            text=TEST_POST_TEXT,
            author=cls.author,
        )
        cls.group = Group.objects.create(
            title=TEST_GROUP_TITLE,
            slug=GROUP_SLUG,
            description=TEST_GROUP_DESCRIPTION,
        )
        cls.guest_client = Client()
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client_post_author = Client()
        cls.authorized_client_post_author.force_login(cls.author)
        cls.POST_ID_URL = reverse('posts:post_detail', args=[cls.post.pk])
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=[cls.post.pk])
        cls.POST_EDIT_REDIRECT_URL = (
            f'/auth/login/?next=/posts/{cls.post.pk}/edit/'
        )
        cls.index_data = (
            INDEX_URL,
            INDEX_TEMPLATE,
            cls.guest_client,
            HTTPStatus.OK
        )
        cls.groups_data = (
            GROUP_URL,
            GROUP_TEMPLATE,
            cls.guest_client,
            HTTPStatus.OK
        )
        cls.profile_data = (
            PROFILE_URL,
            PROFILE_TEMPLATE,
            cls.guest_client,
            HTTPStatus.OK
        )
        cls.post_detail_data = (
            cls.POST_ID_URL,
            POST_DETAIL_TEMPLATE,
            cls.guest_client,
            HTTPStatus.OK
        )
        cls.unexisting_page_data = (
            UNEXISTING_PAGE_URL,
            CUSTOM_404_PAGE_TEMPLATE,
            cls.guest_client,
            HTTPStatus.NOT_FOUND
        )
        cls.pages = (
            cls.index_data,
            cls.groups_data,
            cls.profile_data,
            cls.post_detail_data,
            cls.unexisting_page_data,
        )

    def setUp(self):
        cache.clear()

    def test_urls_for_unauthorized_user(self):
        """
        Страницы index, group/<slug>/, profile/<username>/ и
        posts/<post_id>/ доступны любому пользователю.
        """

        for url, template, client, status_code in self.pages:
            with self.subTest(url=url):
                response = client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_post_edit_available_to_author(self):
        """Страница posts/<post_id>/edit/ доступна автору поста."""

        response = self.authorized_client_post_author.get(self.POST_EDIT_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post_authorized_user(self):
        """Страница create/ доступна авторизованному пользователю."""

        response = self.authorized_client.get(POST_CREATE_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_redirect_anonymous_on_login(self):
        """
        Страницы по адресу create/ и /<post_id>/edit/ перенаправит
        анонимного пользователя на страницу логина.
        """

        redirect_urls = {
            POST_CREATE_URL: POST_CREATE_REDIRECT_URL,
            self.POST_EDIT_URL: self.POST_EDIT_REDIRECT_URL,
        }
        for url, expected_redirect in redirect_urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, expected_redirect)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        for url, template, client, status_code in self.pages:
            response = self.authorized_client.get(url)
            with self.subTest(url=url):
                self.assertTemplateUsed(response, template)

    def test_404_page_uses_custom_template(self):
        """Страница 404 использует кастомный шаблон."""

        response = self.guest_client.get(CUSTOM_404_PAGE_URL)
        self.assertTemplateUsed(response, CUSTOM_404_PAGE_TEMPLATE)
