"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest tests/test_user_views.py


import json
import os
from unittest import TestCase
from flask import session, g, jsonify
from sqlalchemy import JSON
from models import db, connect_db, User, List, Recipe, RecipeList, Favorites

os.environ['DATABASE_URL'] = "postgresql:///spoon-test"

from app import app, CURR_USER_KEY


db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class UserViewsTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

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

        db.session.commit()

        self.recipe = Recipe(
            id=1,
            title="Test Recipe",
            summary="Summary"
        )

        db.session.add(self.recipe)
        db.session.commit()

        testlist = List(
            name="Test List",
            private=False,
            image_url=List.image_url.default.arg,
            user_id=self.testuser.id
        )

        privatelist = List(
            name="Private List",
            private=True,
            image_url=List.image_url.default.arg,
            user_id=self.testuser.id
        )

        db.session.add(testlist)
        db.session.add(privatelist)
        db.session.commit()

        self.list_id = testlist.id
        self.private_list_id = privatelist.id

        recipe_list = RecipeList(list_id=self.list_id, recipe_id=1)

        db.session.add(recipe_list)
        db.session.commit()

    def tearDown(self):
        """Cleanup any fouled transactions."""

        db.session.rollback()

    def test_anon_home_view(self):
        """Test if new user is directs to signup on homepage."""

        resp = self.client.get("/", follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Signup", html)

    # def test_loggedin_home_view(self):
    #     """Test random recipes shown in logged in user home view."""

    #     with self.client as c:
    #         with c.session_transaction() as sess:
    #             sess[CURR_USER_KEY] = self.testuser.id

    #         resp = c.get("/", follow_redirects=True)
    #         html = resp.get_data(as_text=True)

    #         self.assertEqual(resp.status_code, 200)
    #         self.assertIn("<i class=\"bi bi-bookmark-plus-fill\"></i>", html)

    def test_view_signup_form(self):
        """Does user signup form show if no logged in user?"""

        resp = self.client.get("/signup")
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Signup", html)

    def test_signup_user(self):
        """Can new user signup?"""

        resp = self.client.post("/signup", data={
            "email": "newtestuser@test.com",
            "username": "newtestuser",
            "password": "newtestuser", 
            "image_url": f"{User.image_url.default.arg}"
        }, follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Welcome newtestuser!", html)

    def test_unique_user_signup_constraint(self):
        """Can new user signup?"""

        resp = self.client.post("/signup", data={
            "email": "testuser@test.com",
            "username": "testuser",
            "password": "testuser"
        }, follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Username already taken", html)

    def test_show_login_view(self):
        """Does login form show when no logged in user?"""

        resp = self.client.get("/login")
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Login", html)

    def test_login(self):
        """Can user login and is added to session?"""

        resp = self.client.post("/login", data={
            "username": "testuser",
            "password": "testuser"
        }, follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Hello, testuser!", html)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            self.assertEqual(self.testuser.id, sess[CURR_USER_KEY])

    def test_wrong_pw_login(self):
        """Test wrong password login attemp is denied."""

        resp = self.client.post("/login", data={
            "username": "testuser",
            "password": "wrongpassword"
        }, follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Invalid credentials.", html)

    def test_logout_view(self):
        """Test logout redirects to login."""

        resp = self.client.get("/logout", follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Login", html)

    def test_user_profile_view(self):
        """Test user profile views."""

        user = User.query.one()

        resp = self.client.get(f"/users/{user.id}")
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("testuser", html)

    def test_edit_profile_view(self):
        """Test if logged in user can edit profile"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.testuser.id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Edit Profile", html)

    def test_edit_profile(self):
        """Test user can edit profile."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/users/profile", data={
                "username": "testuser",
                "password": "testuser", 
                "email": "testuser@test.com",
                "bio": "testuser bio",
            }, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Profile updated!", html)

    def test_invalid_edit_profile(self):
        """Test user cannot update profile with inavlid credentials"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/users/profile", data={
                "username": "testuser",
                "password": "invalidpassword", 
                "email": "testuser@test.com",
                "bio": "testuser bio",
            }, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Acces unauthroized; incorrect password.", html)
            self.assertNotEqual("testuser bio", self.testuser.bio)

    def test_add_user_favorite(self):
        """Test user can add recipe to favorites."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/recipes/favorite", json={"id": "1"})

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {"message": "Added to favorites!"})
        self.assertEqual(Favorites.query.count(), 1)

    def test_delete_favorite(self):
        """Test if request removes recipe from user favorites if already in favorites."""

        fav = Favorites(user_id=self.testuser.id, recipe_id=1)
        db.session.add(fav)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/recipes/favorite", json={"id": "1"})

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(
                resp.json,
                {"message": "Removed from favorites"})
            self.assertEqual(Favorites.query.count(), 0)

    def test_anon_add_fav_request(self):
        """Test anonymous user cannot add recipe to favorites."""

        resp = self.client.post("recipes/favorite", json={"id": "1"})
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 401)
        self.assertEqual(
            resp.json, 
            {"message": "You must be logged in or signup to add favorites"})
        self.assertEqual(Favorites.query.count(), 0)
            

    def test_create_list_form_view(self):
        """Test view for user to create a new list form."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/lists/new')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Add List", html)

    def test_create_list(self):
        """Test user can create new list."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/lists/new", data={
                "name": "Test List 2",
                "description": "",
                "private": False
            }, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Test List 2 created!", html)

    def test_no_user_list_form(self):
        """Test user can create new list."""

        resp = self.client.get('/lists/new', follow_redirects=True)
        html = resp.get_data(as_text=True)


        self.assertEqual(resp.status_code, 200)
        self.assertIn("You must signup or login to make a new recipe list.", html)

    def test_view_users_lists(self):
        """Test user can view own lists."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.testuser.id}/lists")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Test List", html)

    def test_anon_user_view_lists(self):
        """Test if anon user is denied access to viewing another user's lists."""

        resp = self.client.get(f"/users/{self.testuser.id}/lists", follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Access unauthorized", html)

    def test_view_own_list(self):
        """Test user can view own private list."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/lists/{self.private_list_id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Test List", html)

    # def test_view_other_users_list(self):
    #     """Test if anon user can view a non-private list."""

    #     list = List.query.filter(List.private == False).one()

    #     resp = self.client.get(f"/lists/{list.id}")
    #     html = resp.get_data(as_text=True)

    #     self.assertEqual(resp.status_code, 200)
    #     self.assertIn("Test List", html)

    # def test_view_other_users_private_list(self):
    #     """Test anon user cannot view a private list."""

    #     resp = self.client.get(f"/lists/{self.private_list_id}", follow_redirects=True)
    #     html = resp.get_data(as_text=True)

    #     self.assertEqual(resp.status_code, 200)
    #     self.assertIn("This list is private.", html)

    def test_delete_own_list(self):
        """Test user can delete own list from list.html page."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.post(f'/lists/{self.private_list_id}/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("List deleted", html)

    def test_delete_own_list_from_axios_req(self):
        """Test user can delete own list from lists.html axios request."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/lists/delete", json={"id": f"{self.list_id}"})
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json, {"message": "List deleted"})
            self.assertEqual(List.query.count(), 1)

    def test_delete_other_users_list_from_axios_req(self):
        """Test user cannot delete another user's list from lists.html axios request."""

        resp = self.client.post("/lists/delete", json={"id": f"{self.list_id}"})
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json, {"message": "Action unauthorized"})
        self.assertEqual(List.query.count(), 2)
    
    def test_delete_other_users_list(self):
        """Test anon user cannot delete another users list."""

        resp = self.client.post(f"/lists/{self.private_list_id}/delete", follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(List.query.count(), 2)
        self.assertIn("Action unauthorized", html)

    def test_add_recipe_to_list(self):
        """Test logged in user can add recipe to list."""

        recipe = Recipe.query.filter(Recipe.id != 1).first()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/recipes/add-to-list", json={"recipe": f"{recipe.id}", "list": f"{self.list_id}"})
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json, {"message": "Added to list!"})
            self.assertEqual(RecipeList.query.count(), 2)

    def test_add_duplicate_recipe(self):
        """Test user cannot add duplicate recipe to list."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/recipes/add-to-list", json={"recipe": "1", "list": f"{self.list_id}"})

            self.assertEqual(resp.status_code, 202)
            self.assertEqual(resp.json, {"message": "Duplicate recipe."})
            self.assertEqual(RecipeList.query.count(), 1)

    def test_anon_user_add_to_list(self):
        """Test anon user cannot add recipe to another user's list."""

        recipe = Recipe.query.filter(Recipe.id != 1).first()

        resp = self.client.post("/recipes/add-to-list", json={"recipe": f"{recipe.id}", "list": f"{self.list_id}"}, follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json, {"message": "Action unauthorized"})
        self.assertEqual(RecipeList.query.count(), 1)

    def test_delete_recipe_from_list(self):
        """Test user can delete recipe from own list."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/lists/delete-from", json={"recipe": "1", "list": f"{self.list_id}"})
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json, {"message": "Recipe removed from list"})
            self.assertEqual(RecipeList.query.count(), 0)

    def test_delete_recipe_from_other_users_list(self):
        """Test user cannot delete a recipe from another user's list."""

        resp = self.client.post("/lists/delete-from", json={"recipe": "1", "list": f"{self.list_id}"})

        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json, {"message": "Action unauthorized"})
        self.assertEqual(RecipeList.query.count(), 1)