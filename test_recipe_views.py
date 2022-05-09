"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


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
        Recipe.query.delete()
        User.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(
            email="testuser@test.com",
            username="testuser",
            password="testuser",
            image_url=User.image_url.default.arg)

        db.session.add(self.testuser)
        db.session.commit()