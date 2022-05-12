"""Recipe View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest tests/test_recipe_views.py


import os
from unittest import TestCase
from flask import session
from models import db, connect_db, User, List, Recipe, RecipeList, Favorites

os.environ['DATABASE_URL'] = "postgresql:///spoon-test"

from app import app, CURR_USER_KEY


db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class RecipeViewsTestCase(TestCase):
    """Test views for recipes."""

    def setUp(self):
        """Create test client. Set up sample data."""

        Favorites.query.delete()
        RecipeList.query.delete()
        List.query.delete()
        Recipe.query.filter(Recipe.id == 1).delete()
        User.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(
            email="testuser@test.com",
            username="testuser",
            password="testuser",
            image_url=User.image_url.default.arg)

        self.recipe = Recipe(
            id=1,
            title="Test Recipe",
            summary="Summary"
        )

        db.session.add(self.testuser)
        db.session.add(self.recipe)
        db.session.commit()

    def tearDown(self):
        """Clean up any fouled transactions."""

        db.session.rollback()

    def test_view_recipe_info(self):
        """Test single recipe info view."""

        resp = self.client.get("/recipes/1")
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Test Recipe", html)

    def test_view_invalid_recipe_info(self):
        """Test 404 error page shown when invalid recipe id requested."""

        resp = self.client.get("/recipes/lknioh4oi2")
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 404)
        self.assertIn("Page Not Found.", html)

    def test_recipe_search_form_view(self):
        """Test recipe search form"""

        resp = self.client.get("/search")
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("It's ok to be picky.", html)
        self.assertIn("Search", html)

    def test_recipe_search_view(self):
        """Test submitting recipe search works."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/search/results", data={
                "query": "cookies",
                "diet": "vegan"
            }, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Search results:", html)
            self.assertTrue(len(Recipe.query.all()) > 1)

    def test_recipe_quicksearch_view(self):
        """Test if quick search form submission from navbar returns search results."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/quick-search", data={
                "query": "cookies"
            }, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Search results:", html)
            self.assertTrue(len(Recipe.query.all()) > 1)