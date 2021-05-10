from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class YaTbStaticPagesURLTests(TestCase):
    """Проверка статичных страниц 'об авторе' 'о технолоиях'."""
    def setUp(self):
        # Неавторизованый клиент
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адреса /about/author/."""
        response = self.guest_client.get('/about/author/')
        self.assertEqual(
            response.status_code, 200,
            ('Нужно проверить доступность страницы /about/author'
             'для неавторизованного пользователя')
        )

    def test_tech_url_exists_at_desired_location(self):
        """Проверка доступности адреса /about/tech/."""
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(
            response.status_code, 200,
            ('Нужно проверить доступность страницы /about/tech'
             ' для неавторизованного пользователя')
        )

    def test_about_url_uses_correct_template(self):
        """Проверка шаблона для адреса /about/author/.

        Для страницы 'about/author' должен применяться
        шаблон 'about/author.html'"""
        response = self.guest_client.get('/about/author/')
        self.assertTemplateUsed(
            response, 'about/author.html',
            ('Нужно проверить, что для страницы "/about/author"'
             ' используется шаблон "about/author.html"')
        )

    def test_tech_url_uses_correct_template(self):
        """Проверка шаблона для адреса /about/tech/.

        Для страницы '/about/tech' должен применяться
        шаблон 'about/tech.html'"""
        response = self.guest_client.get('/about/tech/')
        self.assertTemplateUsed(
            response, 'about/tech.html',
            ('Нужно проверить, что для страницы "/about/tech"'
             ' используется шаблон "about/tech.html"')
        )


class YatubeURL_AbsPath_Tests(TestCase):
    """Проверка доступности абсолютных url-адресов

    В проекте есть адреса с разной доступностью для guest и user
    URL                      тип пользователя             редирект
    "/"                                     g
    "/group/"                               g
    "/group/<slug:slug>/"                   g
    "/<str:username>/"                      g
    "/<str:username>/<int:post_id>/"        g
    "/<str:username>/<int:post_id>/edit/"   u-a     g->/login
                                                    u->/username/post_id/
    "/new/"                                 u       g->/login
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # два тестовых юзера, один - автор поста
        cls.user_with_post = User.objects.create(
            username='poster_user'
        )
        cls.user_no_post = User.objects.create(
            username='silent_user'
        )
        # тестовая группа
        cls.group_test = Group.objects.create(
            title='test_group_title',
            slug='test-slug'
        )

        # тестовый пост
        cls.test_post = Post.objects.create(
            author=cls.user_with_post,
            text='test_post_text'
        )
        cls.test_post.save()
        cls.group_test.save()

        # неавторизованный клиент
        cls.guest_client = Client()
        # авторизованный клиент с постом
        cls.authorized_client_a = Client()
        cls.authorized_client_a.force_login(cls.user_with_post)
        # авторизованный клиент без поста
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user_no_post)

        # набор пар "url": "status code" для guest
        cls.templts_pgs_names = {
            '/': 200,
            '/group/': 200,
            '/group/test-slug/': 200,
            '/poster_user/': 200,
            '/poster_user/1/': 200
        }

    def setUp(self):
        self.test_class = YatubeURL_AbsPath_Tests

    def test_guest_get_nonautorized_pages(self):
        """Проверка, что guest видит доступные страницы"""
        for page_url, resp_code in self.test_class.templts_pgs_names.items():

            with self.subTest(page_url=page_url):
                resp = self.test_class.guest_client.get(page_url)
                self.assertEqual(resp.status_code, resp_code, page_url)

    # проверка редиректов по абсолютным путям
    # guest "new/" -> "login/"
    # method == GET
    def test_guest_abs_new_redirect_login_get(self):
        """Проверка, что guest GET /new -> /auth/login/?next=/new/"""
        resp = self.test_class.guest_client.get('/new/')
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '/auth/login/?next=/new/')

    # method == POST
    def test_guest_abs_new_redirect_login_post(self):
        """Проверка, что guest POST /new -> /auth/login/?next=/new/"""
        resp = self.test_class.guest_client.post('/new/')
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '/auth/login/?next=/new/')

    # guest GET "<username>/post_id/edit" -> "login/"
    def test_guest_abs_edit_redirect_login_get(self):
        """Проверка, что guest GET /user/post/edit -> /auth/login/?next=..."""
        resp = self.test_class.guest_client.get('/poster/1/edit/')
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '/auth/login/?next=/poster/1/edit/')

    # guest POST "<username>/post_id/edit" -> "login/"
    def test_guest_abs_edit_redirect_login_post(self):
        """Проверка, что guest POST /user/post/edit -> /auth/login/?next=..."""
        resp = self.test_class.guest_client.post('/poster/1/edit/')
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '/auth/login/?next=/poster/1/edit/')

    # user-not-author "<username>/post_id/edit" -> "<username>/post_id/"
    # method == GET
    def test_user_abs_edit_redirect_postcard_get(self):
        """Проверка, что не автор GET /user/post/edit -> /user/post/"""
        resp = self.test_class.authorized_client.get('/poster/1/edit/')
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '/poster/1/')

    # method == POST
    def test_user_abs_edit_redirect_postcard_post(self):
        """Проверка, что не автор POST /user/post/edit -> /user/post/"""
        resp = self.test_class.authorized_client.post('/poster/1/edit/')
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '/poster/1/')

    # user-author "<username>/post_id/edit" 200
    # method == GET
    def test_user_author_abs_edit_redirect_postcard_get(self):
        """Проверка, что автор GET /user/post/edit == status 200"""
        resp = self.test_class.authorized_client_a.get('/poster/1/edit/')
        self.assertEqual(resp.status_code, 200)

    # method == POST
    def test_user_author_abs_edit_redirect_postcard_post(self):
        """Проверка, что автор POST /user/post/edit == status 200"""
        resp = self.test_class.authorized_client_a.post('/poster/1/edit/')
        self.assertEqual(resp.status_code, 200)
