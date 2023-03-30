from django.test import TestCase, Client
from http import HTTPStatus


class StaticPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_and_tech_urls(self):
        """Проверка доступности адресов about/ и tech/ любому пользователю."""
        pages = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }
        for field, expected_value in pages.items():
            response = self.guest_client.get(field)
            with self.subTest(field=field):
                self.assertEqual(response.status_code, expected_value)
