from django.test import TestCase

from posts.models import (Group, Post, User, Comment,
                          FIRST_FIFTEEN_CHARS_OF_TEXT)


GROUP_SLUG = 'test_group'
TEST_USER = 'test_views1'
TEST_AUTHOR = 'test_post_author'
TEST_POST_TEXT = 'Test post text'
TEST_GROUP_TITLE = 'Test group title'
TEST_GROUP_DESCRIPTION = 'Test group description'
TEXT_FOR_STR_TEST = 'Test first fifteen chars of text'
TEST_COMMENT_TEXT = 'Test comment text'


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USER)
        cls.post = Post.objects.create(
            author=cls.user,
            text=TEXT_FOR_STR_TEST,
            group=Group.objects.create(
                title=TEST_GROUP_TITLE,
                slug=GROUP_SLUG,
                description=TEST_GROUP_DESCRIPTION)
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.post.author,
            text=TEST_COMMENT_TEXT
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""

        test_str = {
            self.post.group.title: self.post.group,
            self.post.text[:FIRST_FIFTEEN_CHARS_OF_TEXT]: self.post,
            self.comment.text: self.comment,
        }
        for correct_str, expected_value in test_str.items():
            with self.subTest(correct_str=correct_str):
                self.assertEqual(correct_str, str(expected_value))

    def test_post_model_verbose_name(self):
        """Проверяем, что verbose_name модели Post совпадает с ожидаемым."""

        field_labels = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
            'image': 'Картинка',
        }
        for field, expected_value in field_labels.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_post_model_help_text(self):
        """help_text полей text и group модели Post совпадает с ожидаемым."""

        field_help_texts = {
            'text': 'Текст записи',
            'group': ('Выберите подходящую для записи группу '
                      'или оставьте поле пустым'),
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    expected_value
                )

    def test_comment_model_verbose_name(self):
        """
        Проверяем, что verbose_name модели Comment
        совпадает с ожидаемым.
        """

        field_labels = {
            'post': 'Запись',
            'author': 'Автор',
            'text': 'Текст комментария',
            'created': 'Дата добавления комментария',
        }
        for field, expected_value in field_labels.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.comment._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_post_model_help_text(self):
        """help_text поля text модели Comment совпадает с ожидаемым."""

        help_text = {'text': 'Введите текст комментария'}
        for field, expected_value in help_text.items():
            self.assertEqual(
                self.comment._meta.get_field(field).help_text,
                expected_value
            )
