"""User model tests."""

# run these tests like:
#
#    python -m unittest test/test_recipe_model.py


import os
from unittest import TestCase, expectedFailure
import unittest

from models import db, User, Favorites, List, Recipe, RecipeList

os.environ['DATABASE_URL'] = "postgresql:///spoon-test"

from app import app

db.create_all()

class RecipeModelTestCase(TestCase):
    """Test model for users."""

    def setUp(self):
        """Create test client, add sample data."""

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

        summary = "Test summary. Here is a link <a href=`https://test.com`>sample recipe</a>"

        recipe = Recipe(
            id=1,
            title="Test Recipe",
            summary=summary
        )

        db.session.add(user)
        db.session.add(recipe)
        db.session.commit()

        self.user_id = user.id
        self.user = user

        self.r_id = recipe.id
        self.recipe = recipe

        list = List(name="testlist",            
            user_id=self.user_id, 
            image_url=List.image_url.default.arg,
            private=False)

        db.session.add(list)
        db.session.commit()

        self.list = list
        self.l_id = list.id

        self.client = app.test_client()

    def tearDown(self):
        """Cleanup any fouled transactions."""

        db.session.rollback()

    def test_recipe_model(self):
        """Does basic recipe model work?"""

        self.assertIsInstance(self.recipe, Recipe)
        self.assertEqual(f"{self.recipe}", f"<# {self.r_id} title: Test Recipe>")

    def test_find_recipe(self):
        """Does find_recipe def work?"""

        self.assertEqual(self.recipe, Recipe.find_recipe(self.r_id))
        self.assertNotEqual(self.recipe, Recipe.find_recipe(98273408972))

    def test_clean_summary(self):
        """Does clean_summary @classmethod remove HTML and suggested recipe links?"""

        self.recipe.summary = Recipe.clean_summary(self.recipe.summary)

        db.session.add(self.recipe)
        db.session.commit()

        self.assertEqual(self.recipe.summary, "Test summary.")
        self.assertNotIn("sample recipe", self.recipe.summary)

    def test_clean_instructions(self):
        """Does clean_instructions @classmethod remove list HTML?"""

        self.recipe.instructions = Recipe.clean_inst("<li>1.</li><li>2.</li></ul><p>3.</p><b>4...</b><i>(6.)")

        db.session.add(self.recipe)
        db.session.commit()


        self.assertEqual(self.recipe.instructions, '1.2.3.4.(6)')
        self.assertNotIn("<li>", self.recipe.instructions)

    def test_get_ingredients(self):
        """Does grt_ingredients @classmethod parse API data properly?"""

        res = {"name": "sugar",
            "measures": {
                "us": {
                "unitShort": "cup",
                "amount": .5}
                }
            }

        self.recipe.ingredients = Recipe.get_ingredients(res, "us")

        db.session.add(self.recipe)
        db.session.commit()
        
        self.assertEqual(self.recipe.ingredients, "1/2 cup sugar")
        self.assertNotIn("0.5", self.recipe.ingredients)

    def test_get_tags(self):
        """Does get_tags @classmethod get all tags from API response?"""

        self.recipe.tags = Recipe.get_tags({
            'dairyFree': True, 
            'glutenFree': True,
            'vegetarian': True,
            'vegan': True})

        db.session.add(self.recipe)
        db.session.commit()

        self.assertEqual(self.recipe.tags, ['Dairy Free', 'Gluten Free', 'Vegetarian', 'Vegan'])
        self.assertIsInstance(self.recipe.tags, list)

    def test_add_recipe_to_list(self):
        """Can recipe be added to list?"""

        recipe_list = RecipeList(list_id=self.l_id, recipe_id=self.r_id)

        db.session.add(recipe_list)
        db.session.commit()

        self.assertIsInstance(recipe_list, RecipeList)
        self.assertIn(self.recipe, self.list.recipes)

    def test_add_duplicate_recipe_to_list(self):
        """Does """

class ExpectedFailureTestCase(TestCase):
    @unittest.expectedFailure

    def test_add_duplicate_recipe(self):
        """Test fail if adding duplicate recipe to db"""

        recipe = Recipe(
            id=1,
            title="Test Recipe"
        )

        db.session.add(recipe)
        db.session.commit()

        recipe2 = Recipe(
            id=1,
            title="Test Recipe"
        )

        db.session.add(recipe2)
        db.session.commit()

    class ExpectedFailureTestCase(TestCase):
        @unittest.expectedFailure

        def test_add_duplicate_recipe_list(self):
            """Test failure if adding duplicate recipe to list"""

            recipe_list = RecipeList(list_id=self.l_id, recipe_id=self.r_id)

            db.session.add(recipe_list)
            db.session.commit()

            recipe_list2 = RecipeList(list_id=self.l_id, recipe_id=self.r_id)

            db.session.add(recipe_list2)
            db.session.commit()


