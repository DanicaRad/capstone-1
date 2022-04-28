"""Test for checking out API responses"""

import os

from flask import Flask, render_template, request, flash, redirect, jsonify, session, g
import requests
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from site_models import APIRecipe, ShortRecipe
from forms import SearchForm, AddUserForm, LoginForm
from models import db, connect_db, User, List, Recipe

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///spoonacular'
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///spoonacular'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = "Winnie"
toolbar = DebugToolbarExtension(app)

API_KEY = '979dfa9f09634c8faf4ba8e387c1b0ab'
BASE_URL = f"https://api.spoonacular.com/recipes"
SIMILAR_URL = f"https://api.spoonacular.com/recipes/similar?apiKey={API_KEY}"

connect_db(app)

#########################################################################
# User signup / login / logout 

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@app.route('/signup', methods=["GET","POST"])
def signup():
    """Handle signup user.
    
    Create new user and add to DB. Redirect to home page. 
    
    If form not valid, show form.
    If username not unique, flash message and re-present form."""

    form = AddUserForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)

@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)

@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    flash("You've been logged out.", "success")

    return redirect('/login')

########################################################################
# General user routes:

# @app.route('/lists/add')
# def add_list():




########################################################################
########################################################################
########################################################################
# Test draft routes:

@app.route('/recipes')
def get_recipe():
    querystring = {"tags":"vegetarian,dessert","number":"1"}
    response = request.get(BASE_URL, querystring)
    return jsonify(response)


@app.route('/random')
def get_data():

    querystring = {"tags":"vegetarian,dessert","number":"1", "stepBreakdown": "true", "extendedIngredients": "false"}
    response = requests.get(f"{BASE_URL}/random?apiKey={API_KEY}", querystring)
    resp = response.json()
    [data] = resp['recipes']
    recipe_data = dict([(key, value) for key, value in data.items()])
    recipe = APIRecipe(recipe_data)

    similar = requests.get(SIMILAR_URL, params={"number": "1"})

    return render_template('recipes/test.html', data=data, recipe=recipe)

@app.route('/info/<int:recipe_id>')
def get_recipe_details(recipe_id):
    """Get and show recipe meta information from API."""

    response = requests.get(f"{BASE_URL}/{recipe_id}/information?apiKey={API_KEY}", params={"includeNutrition": "false"})

    resp = response.json()
    recipe = APIRecipe(resp)

    return render_template('recipes/recipes.html', recipe=recipe)

@app.route('/search', methods=["GET", "POST"])
def show_search_form():
    """Show form for users to search."""

    form = SearchForm()

    if form.validate_on_submit():

        params = {field: form[f"{field}"].data for field in form.data if form[f"{field}"].data and field != "csrf_token"}

        response = requests.get(
                        f"{BASE_URL}/complexSearch?apiKey={API_KEY}",
                        params)
        resp = response.json()
        results = resp['results']
        recipes = [ShortRecipe(recipe) for recipe in results]

        return render_template('search-results.html', recipes=recipes)

    return render_template('search.html', form=form)