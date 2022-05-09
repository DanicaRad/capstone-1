"""SQLAlchemy models for Spoonacular."""

from cgitb import text
from typing import Text
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY

from fractions import Fraction
import math
from bs4 import BeautifulSoup

bcrypt = Bcrypt()
db = SQLAlchemy()


class RecipeList(db.Model):
    """Maps recipes to lists."""

    __tablename__ = "recipes_lists"

    list_id = db.Column(
        db.Integer,
        db.ForeignKey("lists.id", ondelete="cascade"),
        primary_key=True
    )

    recipe_id = db.Column(
        db.Integer,
        db.ForeignKey("recipes.id", ondelete="cascade"),
        primary_key=True
    )

class Favorites(db.Model):
    """Model for user favorite recipes."""

    __tablename__ = "favorites"

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="cascade"),
        primary_key=True
    )

    recipe_id = db.Column(
        db.Integer,
        db.ForeignKey("recipes.id", ondelete="cascade"),
        primary_key=True
    )


class Recipe(db.Model):
    """Recipes saved to user lists."""

    __tablename__ = "recipes"

    id = db.Column(
        db.Integer,
        primary_key=True,
        unique=True
    )

    title = db.Column(
        db.Text,
        nullable=False
    )

    source = db.Column(db.Text, default="View Source")

    source_url = db.Column(db.Text)

    image_url = db.Column(db.Text, default="/static/images/default-recipe.jpg")

    summary = db.Column(db.Text)
    
    instructions = db.Column(db.Text)

    total_min = db.Column(db.Integer)

    servings = db.Column(db.Integer)

    ingredients = db.Column(db.PickleType)

    us = db.Column(db.PickleType)

    metric = db.Column(db.PickleType)

    dish = db.Column(db.PickleType)

    diets = db.Column(db.PickleType)

    tags = db.Column(db.PickleType)

    score = db.Column(db.Integer)


    lists = db.relationship(
        'List',
        secondary="recipes_lists",
        cascade="all, delete"
    )

    favorites = db.relationship("Favorites")

    def __repr__(self):
        return f"<# {self.id} title: {self.title}>"

    @classmethod
    def make_recipe(cls, res):
        """Make recipe model from API response."""

        id = res['id']

        title = res['title']

        source = res['sourceName'] if res['sourceName'] else "Source"

        source_url = res['sourceUrl']

        image_url = res.get('image', '/static/images/default-recipe.jpg')

        summary = cls.clean_summary(res['summary'])

        instructions = cls.clean_inst(res['instructions'])

        total_min = res['readyInMinutes']

        servings = res['servings']

        ingredients = [r['original'] for r in res['extendedIngredients']]

        us = [cls.get_ingredients(r, "us") for r in res["extendedIngredients"]]

        metric = [cls.get_ingredients(r, "metric") for r in res["extendedIngredients"]]

        dish = res['dishTypes']

        diets = res['diets']

        tags = cls.get_tags(res)

        score = res['spoonacularScore']
    

        return Recipe(id=id, title=title, source=source, source_url=source_url, image_url=image_url, summary=summary, instructions=instructions, total_min=total_min, servings=servings, ingredients=ingredients, us=us, metric=metric, dish=dish, diets=diets, tags=tags, score=score)

    @classmethod
    def find_recipe(cls, id):
        """Find recipe by id. If recipe not in db, return false, otherwise return recipe."""

        recipe = cls.query.filter_by(id=id).first()

        if recipe:
            return recipe

        return False

    @classmethod
    def strip_HTML(cls, res):
        """Uses BeautifulSoup library to remove all HTML elements from text."""

        soup = BeautifulSoup(res)
        return soup.get_text()

    @classmethod
    def clean_summary(cls, res):
        """Cleans HTML from response text and formats sentences to split cleanly for HTML rendering."""

        split = res.split('. ')

        str = ". ".join([str for str in split if "<a" not in str or ".com" not in str]) + "."

        return cls.strip_HTML(str)

    @classmethod
    def clean_inst(cls, res):
        """Removes HTML list tags and replaces with `.` for clean HTML list rendering."""

        no_l1 = res.replace(".</li>", ".")
        no_l2 = no_l1.replace(".</ul>", ".")
        no_ol = no_l2.replace('.</ol', ".")
        no_ul = no_ol.replace('.<ul>', ".")
        no_els = no_ul.replace("...", ".")
        no_pa = no_els.replace(".)", ").")
        no_p = no_pa.replace("</p>", "")
        split = no_p.split('. ')

        str = ".".join([str for str in split if "<a" not in str and len(str) > 1])

        return cls.strip_HTML(str[0:-1])

    @classmethod
    def get_ingredients(cls, res, ms):
        """Make dictionary of ingredients"""

        name =  res["name"]
        mu = res["measures"][ms]
        unit = mu["unitShort"]
        num = mu["amount"]

        return f"{cls.get_amount(num)} {unit} {name}"

    @classmethod
    def get_amount(cls, num):
        """Format floats in ingredient amounts as fraction ratios"""

        if num.is_integer() or num >= 1:
            return int(num)

        fract = Fraction(num).limit_denominator(9)
        return f"{fract.numerator}/{fract.denominator}"

    @classmethod
    def get_tags(cls, res):
        """Get recipe tags."""

        tags = {'dairyFree': 'Dairy Free',
        'glutenFree': 'Gluten Free',
        'vegetarian': 'Vegetarian',
        'vegan': 'Vegan'}

        return [tags[tag] for tag in tags if res[tag] == True]

    def favs(self):
        """Return number of `likes` or favorites recipe has."""

        return len(self.favorites)


class List(db.Model):
    """Connection of user <---> list"""

    __tablename__ = "lists"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    name = db.Column(db.Text, nullable=False)

    description = db.Column(db.Text)

    private = db.Column(db.Boolean, nullable=False, default=False)

    image_url = db.Column(db.Text, nullable=False, default="/static/images/default-list.jpg")

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="cascade")
    )

    user = db.relationship('User')

    recipes = db.relationship(
        'Recipe',
        secondary="recipes_lists",
        primaryjoin=(RecipeList.list_id == id),
        secondaryjoin=(RecipeList.recipe_id == Recipe.id)
    )

    def __repr__(self):
        return f"<list# {self.id}, user: {self.user_id}>"

    def has_recipe(self, id):
        """Uses recipe id to see if recipe is already in list."""

        ids = [recipe.id for recipe in self.recipes]
        if id in ids:
            return True
        return False



class User(db.Model):
    """User model for app."""

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True
    )

    bio = db.Column(db.Text)

    image_url = db.Column(
        db.Text,
        default="/static/images/default_user.jpg"
    )

    password = db.Column(
        db.Text,
        nullable=False
    )

    lists = db.relationship("List")

    favorites = db.relationship(
        "Recipe",
        secondary="favorites",
        primaryjoin=(Favorites.user_id == id),
        secondaryjoin=(Favorites.recipe_id == Recipe.id)
    )

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    @classmethod
    def signup(cls, username, email, password, image_url):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            image_url=image_url,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`. If can't find  matching user and/or password, return False."""

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

def connect_db(app):
    """Connect this database to provided Flask app."""

    db.app = app
    db.init_app(app)