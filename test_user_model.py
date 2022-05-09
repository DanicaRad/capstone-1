"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase, expectedFailure
import unittest

from models import db, User, Favorites, List, Recipe, RecipeList

os.environ['DATABASE_URL'] = "postgresql:///spoon-test"


# Now we can import app

from app import app

db.create_all()

class UserModelTestCase(TestCase):
    """Test model for users."""

    def setUp(self):
        """Create test client, add sample data."""

        db.session.rollback()

        Favorites.query.delete()
        RecipeList.query.delete()
        List.query.delete()
        Recipe.query.delete()
        User.query.delete()


        user = User.signup(
            email="test@test.com",
            username="testuser",
            password="testuser",
            image_url=User.image_url.default.arg
        )

        recipe = Recipe(
            id=1,
            title="Test Recipe"
        )

        db.session.add(user)
        db.session.add(recipe)
        db.session.commit()

        self.user_id = user.id
        self.user = user

        self.r_id = recipe.id
        self.recipe = recipe

        self.client = app.test_client()

    def tearDown(self):
        """Cleanup any fouled transactions."""

        db.session.rollback()

    def test_user_model(self):
        """Does basic user model work?"""

        self.assertEqual(self.user.username, "testuser")
        self.assertIsInstance(self.user, User)

    def test_user_login(self):
        """Does user.authenticate work?"""

        self.assertEqual(User.authenticate("testuser", "testuser"), self.user)
        self.assertFalse(User.authenticate("testuser", "password"))

    def test_signup(self):
        """Does User.signup work?"""

        user2 = User.signup(email="test2@test.com", username="testuser2", password="testuser2", image_url="/static/images/default_user.jpg")

        self.assertIsInstance(user2, User)
        self.assertEqual(f"{user2}", f"<User #{user2.id}: testuser2, test2@test.com>")
        self.assertEqual(User.authenticate("testuser2", "testuser2"), user2)

    def test_make_list(self):
        """Can user make list?"""

        list = List(name="testlist", user_id=self.user_id, image_url=List.image_url.default.arg, private=False)

        db.session.add(list)
        db.session.commit()

        self.assertEqual(f"{list}", f"<list# {list.id}, user: {self.user_id}>")
        self.assertIsInstance(list, List)
        self.assertEqual(len(self.user.lists), 1)

    def test_add_user_favorite(self):
        """Can user add recipe to favorites?"""

        fav = Favorites(user_id=self.user_id, recipe_id=self.r_id)

        db.session.add(fav)
        db.session.commit()

        self.assertEqual(len(self.user.favorites), 1)
        self.assertEqual([f"{self.recipe}"], [f"<# {self.r_id} title: Test Recipe>"])

    class ExpectedFailureTestCase(TestCase):
        @unittest.expectedFailure

        def test_unique_username(self):
            """Test failure if new user signs up with non-unique username"""

            user = User.signup(
                email="test@test.com",
                username="testuser",
                password="testuser",
                image_url=User.image_url.default.arg
            )

            db.session.add(user)
            db.session.commit()

            self.assertIsInstance(user, User)

