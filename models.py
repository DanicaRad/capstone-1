"""SQLAlchemy models for Spoonacular."""

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

from fractions import Fraction
from bs4 import BeautifulSoup
from sqlalchemy import ForeignKey
from data.search_params import res_tags, tags, diets

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

class RecipeTags(db.Model):

    __tablename__ = "recipe_tags"

    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id", ondelete="cascade"), primary_key=True)

    tag_id = db.Column(db.Integer, db.ForeignKey("tags.id", ondelete="cascade"), primary_key=True)

    def __repr__(self):
        return f"< recipe #{self.recipe_id} tag #{self.tag_id}>"

    @classmethod
    def get_recipe_tags(cls, resp):
        """Gets recipe tags from API response, saves to DB."""

        data_tags = {res_tags[tag].casefold() for tag in res_tags if resp[tag] == True}

        resp_diets = {tag[1].casefold() for tag in tags if tag[1].casefold() in resp['diets']}

        tag_names = [item for item in (data_tags | resp_diets)]

        tag_ids = Tag.query.filter(Tag.tag_name.in_(tag_names)).all()

        recipe_tags = [RecipeTags(recipe_id=resp['id'], tag_id=tag.id) for tag in tag_ids]
        
        db.session.add_all(recipe_tags)
        db.session.commit()
    
    @classmethod
    def get_tags(cls, recipe):
        """Makes RecipeTags for recipe already in DB with Recipe.tags. For filling in missing data from fouled API queries."""

        recipe_tags = [item for item in recipe.tags]
        tag_ids = Tag.query.filter(Tag.tag_name.in_(recipe_tags)).all()

        tags = [RecipeTags(recipe_id=recipe.id, tag_id=tag.id) for tag in tag_ids]
        db.session.add_all(tags)
        db.session.commit()

class SimilarRecipes(db.Model):
    """Model for similar recipe pairs."""

    __tablename__ = "similar"

    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id", ondelete="cascade"), primary_key=True)

    similar_id = db.Column(db.Integer, db.ForeignKey("recipes.id", ondelete="cascade"), primary_key=True)

    def __repr__(self):
        return f"<recipe #{self.recipe_id}, similar #{self.similar_id}>"

    @classmethod
    def add_similar(cls, id, s_id):
        """Checks if similar relationship already in db, adds if not. Calls reverse simmilar method."""

        similar = SimilarRecipes.query.filter(SimilarRecipes.recipe_id == id, SimilarRecipes.similar_id == s_id).first()

        if not similar:
            similar = SimilarRecipes(recipe_id=id, similar_id=s_id)
            
            db.session.add(similar)
            db.session.commit()

        cls.reverse_similar(id, s_id)
        return

    @classmethod
    def reverse_similar(cls, id, s_id):
        """Uses ids from SimilarRecipe instance to see if reverse relationship is in db. If not, adds."""

        rev_similar = SimilarRecipes.query.filter(SimilarRecipes.recipe_id == s_id, SimilarRecipes.similar_id == id).first()

        if not rev_similar:
            reversed_similar = SimilarRecipes(recipe_id=s_id, similar_id=id)
            
            db.session.add(reversed_similar)
            db.session.commit()

        return None


class Tag(db.Model):

    __tablename__ = "tags"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    tag_name = db.Column(db.Text, unique=True)

    def __repr__(self):
        return f"{self.tag_name}"

    @classmethod
    def make_tag(cls, name):

        tag = Tag(tag_name=name)

        return tag

    def get_name(self):
        """Returns tag name from camel case API tag_name"""

        for tag in tags:
            if self.tag_name == tag[0]:
                return tag[1]

def make_tags_table(tags):
    """Gets tags for Tag table."""

    tag_names = [tag[1].casefold() for tag in tags]

    all_tags = [Tag(tag_name=name) for name in tag_names]

    db.session.add_all(all_tags)
    db.session.commit()

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

    likes = db.Column(db.Integer, default=0)

    health_score = db.Column(db.Integer)

    lists = db.relationship(
        'List',
        secondary="recipes_lists",
        cascade="all, delete"
    )

    favorites = db.relationship("Favorites")

    recipe_tags = db.relationship(
        'Tag',
        secondary='recipe_tags',
        primaryjoin=(RecipeTags.recipe_id == id),
        secondaryjoin=(RecipeTags.tag_id == Tag.id),
        cascade='all, delete'
    )

    similar = db.relationship(
        "Recipe",
        secondary="similar",
        primaryjoin=(SimilarRecipes.similar_id == id),
        secondaryjoin=(SimilarRecipes.recipe_id == id)
    )

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

        score = res.get('spoonacularScore', None)

        likes = res['aggregateLikes']

        health_score = res['healthScore']
    
        return Recipe(id=id, title=title, source=source, source_url=source_url, image_url=image_url, summary=summary, instructions=instructions, total_min=total_min, servings=servings, ingredients=ingredients, us=us, metric=metric, dish=dish, diets=diets, tags=tags, score=score, likes=likes, health_score=health_score)

    @property
    def total_likes(self):
        """Aggregate recipe likes from API and user likes from app."""

        if self.favorites:
            return self.likes + len(self.favorites)

        return self.likes

    @classmethod
    def strip_HTML(cls, res):
        """Uses BeautifulSoup library to remove all HTML elements from text."""

        soup = BeautifulSoup(res, "html.parser")
        return soup.get_text()

    @classmethod
    def clean_summary(cls, res):
        """Cleans HTML from response text and formats sentences to split cleanly for HTML rendering."""

        if not res:
            return None

        split = res.split('. ')

        str = ". ".join([str for str in split if "<a" not in str or ".com" not in str]) + "."

        return cls.strip_HTML(str)

    @classmethod
    def clean_inst(cls, res):
        """Removes HTML list tags and replaces with `.` for clean HTML list rendering."""

        if res:

            no_l1 = res.replace("</li>", ".")
            no_l2 = no_l1.replace("</ul>", ".")
            no_ol = no_l2.replace('</ol>', ".")
            no_ul = no_ol.replace('<ul>', ".")
            no_els = no_ul.replace("...", ".")
            no_pa = no_els.replace(".)", ").")
            no_p = no_pa.replace("</p>", ".")
            stripped = no_p.replace("..", ".")
            split = stripped.split('. ')

            str = ".".join([str for str in split if "<a" not in str and len(str) > 1])

            return cls.strip_HTML(str[0:-1])

        return None

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
        """Get recipe tags from response data. Checks response['diets'] and response[f"{tag}"] for completeness."""

        tags = {res_tags[tag].casefold() for tag in res_tags if res[tag] == True}
        diets = {diet.casefold() for diet in res['diets']}

        return [item for item in (tags | diets)]

    def has_tag(self, tag):
        """Return recipe if tag in recipe.tags"""

        tags = self.tags

        if tag in tags:
            return True

        return False

    @classmethod
    def sort_by(cls, sort, ids):
        """Sorts recipes by sort arg."""

        sorted = [recipe for recipe in Recipe.query.filter(Recipe.id.in_(ids)).order_by(sort)]

        if sort == "total_min":
            return sorted

        sorted.reverse()

        return sorted


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

    def top_tags(self):
        """Get top dietary tags in list."""

        all_tags = [tag[1] for tag in tags]

        tags_lists = [tag for tag in (r.tags for r in self.recipes if r.tags)]
        user_tags = [tag for sublist in tags_lists for tag in sublist]
        sorted_tags = sorted([(tag, user_tags.count(tag.casefold())) for tag in all_tags], key=lambda tag: tag[1])
        sorted_tags.reverse()

        return [tag[0] for tag in sorted_tags[0:5]]



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

    def top_tags(self, recipes):
        """Get user's top dietary tags based on favorite recipes"""

        all_tags = [tag[1] for tag in tags]

        tags_lists = [tag for tag in (r.tags for r in recipes if r.tags)]
        user_tags = [tag for sublist in tags_lists for tag in sublist]
        sorted_tags = sorted([(tag, user_tags.count(tag.casefold())) for tag in all_tags], key=lambda tag: tag[1])
        sorted_tags.reverse()

        return [tag[0] for tag in sorted_tags[0:5]]

def connect_db(app):
    """Connect this database to provided Flask app."""

    db.app = app
    db.init_app(app)