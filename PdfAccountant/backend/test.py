import unittest
from app import app


class TestRegister(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    def test_register(self):
        rv = self.app.post('/register',
                           data=dict(
                               username="testuser", email="test@test.com", password="1234", password2="1234"),
                           follow_redirects=True)
        self.assertEqual(rv.status, '200 OK')


class TestLogin(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    def test_login(self):
        rv = self.app.get('/login')
        self.assertEqual(rv.status, '200 OK')


class TestUnauthenticated(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    def test_unauthenticated(self):
        rv = self.app.get('/index')
        self.assertNotEqual(rv.status, '200 OK')


if __name__ == '__main__':
    unittest.main()
