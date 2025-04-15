import unittest
from app import app  # Make sure this imports your Flask app correctly

class BasicTests(unittest.TestCase):

    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    # Test: Home page status code
    def test_home_status_code(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    # Test: Check known content on home page
    def test_home_content(self):
        response = self.app.get('/')
        self.assertIn(b'Air Quality', response.data)  # change text as per your homepage

    # Test: 404 error for non-existent page
    def test_404_error(self):
        response = self.app.get('/nonexistentpage')
        self.assertEqual(response.status_code, 404)

    # Test: Session does not contain user before login
    def test_session_before_login(self):
        with self.app as client:
            client.get('/')
            with client.session_transaction() as session:
                self.assertNotIn('user_id', session)  # replace with your actual session key if different

if __name__ == "__main__":
    unittest.main()
