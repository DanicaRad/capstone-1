"""SQLAlchemy models for Spoonacular."""

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()

class List(db.Model):
    """Connection of user <---> list"""

    __tablenmame__ = "lists"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="cascade")
    )

class Recipe(db.Model):
    """Recipes saved to user lists."""

    __tablename__ = "recipes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.Text,
        nullable=False
    )

    source = db.Column(
        db.Text
    )

    source_url = db.Column(
        db.Text
    )

    image_url = db.Column(
        db.Text
    )

    summary = db.Column(
        db.Text
    )
    instructions = db.Column(
        db.Text
    )

    total_min = db.Column(
        db.Integer
    )

    servings = db.Column(
        db.Integer
    )

    ingredients = db.Column(
        db.Text
    )

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
        db.FireignKey("recipes.id", ondelete="cascade"),
        primary_key=True
    )

class User(db.model):
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

    image_url = db.Column(
        db.text,
        defulat="/static/images/default_user.jpg"
    )

    password = db.Column(
        db.Text,
        nullable=False
    )

    lists = db.Relationship(
        "List",
        secondary="recipe_list",
        primary_join=(List.user_id == id),
        secondary_join=(RecipeList.list_id == List.id)
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