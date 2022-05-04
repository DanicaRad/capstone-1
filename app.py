"""Test for checking out API responses"""

import os
from re import L
from webbrowser import get

from flask import Flask, render_template, request, flash, redirect, jsonify, session, g
import pdb
import requests
import random
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from site_models import APIRecipe, ShortRecipe
from forms import ListForm, SearchForm, UserAddForm, LoginForm, UserAddForm, UserEditForm
from models import db, connect_db, User, List, Recipe, RecipeList, Favorites

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

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

    form = UserAddForm()

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

@app.route('/users/<int:id>/lists')
def show_users_lists(id):
    """Shows user's own lists."""

    if g.user.id != id:
        flash("Access unauthorized", "danger")
        return redirect('/')

    return render_template('/lists/lists.html')

@app.route('/users/<int:id>')
def show_user(id):
    """Show user info/ profile page."""

    user = User.query.get_or_404(id)

    return render_template('/users/user.html', user=user)

@app.route('/users/profile', methods=['GET', 'POST'])
def profile():
    """Show and update profile for current user."""

    if not g.user:
        flash("Access unauthorized", "danger")
        return redirect('/')

    form = UserEditForm()
    if form.validate_on_submit():
        if User.authenticate(g.user.username, form.password.data):
            g.user.username = form.username.data
            g.user.email = form.email.data
            g.user.image_url = form.image_url.data if form.image_url.data else g.user.image_url

            db.session.add(g.user)
            db.session.commit()

            flash("Profile updated!", "success")
            return redirect('/users/home')

        else:
            flash("Acces unauthroized; incorrect password.")
            return redirect('/users/home')

    return render_template('users/profile.html', form=form)

@app.route('/favorites')
def favorites():
    """Show user's favorite recipes."""

    if not g.user:
        flash("Access unauthorized", "danger")
        return redirect('/')

    return render_template('users/favorites.html')

########################################################################
# List routes:

@app.route('/lists/new', methods=['GET', 'POST'])
def add_list():
    """Add a list for current user."""

    if not g.user:
        flash("You must signup or login to make a new recipe list.", "warning")
        return redirect('/signup')

    form = ListForm()
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data or None
        list = List(name=name, description=description, user_id=g.user.id)

        db.session.add(list)
        db.session.commit()

        flash(f"{list.name} created!", "success")
        return redirect('/')

    return render_template('lists/form.html', form=form)

@app.route('/lists/<int:id>')
def show_list(id):
    """Shows recipelist if list user is curr_user."""

    list = List.query.get_or_404(id)

    if list not in g.user.lists and list.private == True:

        flash("Only the list creator can view this list.", "danger")
        return redirect('/')

    return render_template('lists/list.html', user=g.user, list=list)

@app.route('/lists/<int:id>/delete', methods=['GET', 'POST'])
def delete_list(id):
    """Delete's user list"""

    list = List.query.get_or_404(id)

    if not g.user or list.user_id != g.user.id:
        flash("Unauthorized action", "danger")
        return redirect(f'/lists/{id}')
    
    db.session.delete(list)
    db.session.commit()

    flash("List deleted", "warning")
    return redirect(f'/users/{g.user.id}/lists')

# @app.route('/lists/<int:r_id>/<int:l_id>/delete', methods=['GET', 'POST'])
# def delete_from_list(r_id, l_id):
#     """Deletes recipe from list."""

#     if not g.user:
#         flash("Action unauthorized", "danger")
#         return redirect(f'/lists/{l_id}')

#     list = List.query.get_or_404(l_id)
#     if list not in g.user.lists:
#         flash("Unauthorized action", "danger")
#         return redirect(f'/lists/{l_id}')

#     recipe = Recipe.query.get_or_404(r_id)
#     if recipe in list.recipes:

#         recipe_list = RecipeList.query.filter(
#             RecipeList.list_id == l_id,
#             RecipeList.recipe_id == r_id).one()

#         db.session.delete(recipe_list)
#         db.session.commit()

#         flash(f"Recipe removed from {list.name}")
#         return redirect(f'/lists/{l_id}')
        
#     flash(f"Recipe not found in {list.name}", "warning")
#     return redirect(f'/lists/{l_id}')

########## TEST ##################

# *********  Receives JS post request to delete recipe from list

@app.route('/lists/delete-from', methods=['GET', 'POST'])
def delete_from_list():
    """Deletes recipe from list."""

    if not g.user:
        return (jsonify(message="Action unauthorized"), 202)

    r_id = request.json['recipe']
    l_id = request.json['list']


    list = List.query.get_or_404(l_id)
    if list not in g.user.lists:
        return (jsonify(message="Action unauthroized"), 202)

    recipe = Recipe.query.get_or_404(r_id)
    if recipe in list.recipes:

        recipe_list = RecipeList.query.filter(
            RecipeList.list_id == l_id,
            RecipeList.recipe_id == r_id).one()

        db.session.delete(recipe_list)
        db.session.commit()

        return (jsonify(message="Recipe removed from list"), 200)
        
    return (jsonify(message="Recipe not found in list"), 202)





########################################################################
########################################################################
########################################################################
# Test draft routes:

@app.route('/recipes/<int:id>', methods=['GET', 'POST'])
def recipe_info(id):
    """Get and show recipe meta information from API."""

    recipe = get_recipe(id)

    return render_template('recipes/recipe.html', recipe=recipe)

# ***** Old add to list route before JS request written ***

# @app.route('/recipes/<int:r_id>/<int:l_id>/add', methods=['GET', 'POST'])
# def add_to_list(r_id, l_id):
#     """Add recipe to user list."""

#     if not g.user:
#         flash("Action unauthorized", "danger")
#         return redirect(request.referrer)

#     list = List.query.get_or_404(l_id)

#     if list.user_id != g.user.id:
#         flash("Action unauthorized", "danger")
#         return redirect(request.referrer)

#     recipe = get_recipe(r_id)

#     recipe_list = RecipeList(list_id=l_id, recipe_id=recipe.id)
#     db.session.add(recipe_list)
#     db.session.commit()

#     flash(f"Recipe added to list!", "success")
#     return redirect(request.referrer)

############ Adds to list from JS ppost request #################################

@app.route('/recipes/add-to-list', methods=['GET', 'POST'])
def add_to_list():
    """Add recipe to user list."""

    if not g.user:
        return(jsonify(message="Action unauthorized"), 202)

    r_id = request.json['recipe']
    l_id = request.json['list']

    list = List.query.get_or_404(l_id)

    if list.user_id != g.user.id:
        return(jsonify(message="Action unauthorized"), 202)

    recipe = get_recipe(r_id)

    recipe_list = RecipeList(list_id=l_id, recipe_id=recipe.id)
    db.session.add(recipe_list)
    db.session.commit()

    return(jsonify(message="Added to list!"), 200)

#####################################################################

# @app.route("/recipes/<int:id>/favorite", methods=["GET", "POST"])
# def add_favorite(id):
#     """Adds recipe to user favorites if not in favorites."""

#     if not g.user:
#         flash("You must be logged in or signup to add favorites", "danger")
#         return redirect(request.referrer)

#     recipe = get_recipe(id)

#     if recipe in g.user.favorites:
#         flash("This recipe is already in your favorites.")
#         return redirect(f'/recipes/{id}')

#     fav = Favorites(user_id=g.user.id, recipe_id=recipe.id)
#     db.session.add(fav)
#     db.session.commit()

#     flash("Added to favorites!", "success")
#     return redirect(request.referrer)

@app.route("/recipes/favorite", methods=["GET", "POST"])
def add_or_delete_favorite():
    """Adds recipe to user favorites if not in favorites."""

    if not g.user:
        return (jsonify(message="You must be logged in or signup to add favorites"), 202)

    id = request.json['id']

    recipe = get_recipe(id)

    if recipe in g.user.favorites:
        fav = Favorites.query.filter(Favorites.user_id == g.user.id, Favorites.recipe_id == id).one()
        print(f"********************************************* FAVORITE {fav} *********************************")
        db.session.delete(fav)
        db.session.commit()

        return (jsonify(message="Removed from favorites."), 200)

    newfav = Favorites(user_id=g.user.id, recipe_id=id)
    db.session.add(newfav)
    db.session.commit()

    return jsonify(("Added to favorites!"), 200)

@app.route('/search', methods=["GET", "POST"])
def show_search_form():
    """Show search form. Remove previous search results from session."""

    session.pop('recipes', None)

    form = SearchForm()

    return render_template('search.html', form=form)

@app.route('/search/results', methods=['GET', 'POST'])
def show_results():
    """Shows search results, add results to session so user can return to results page."""

    form = SearchForm()

    if form.validate_on_submit():
        params = {
            "query": form.query.data,
            "type": form.type.data,
            "cuisine": form.cuisine.data,
            "intolerances": form.intolerances.data,
            "diet": form.diet.data,
            "number": "10",
            "sort": form.sort.data,
            "addRecipeInformation": "true"
        }

        response = requests.get(
                        f"{BASE_URL}/complexSearch?apiKey={API_KEY}",
                        params)
        resp = response.json()
        results = resp['results']

        recipes = [get_recipe(recipe['id']) for recipe in results]

        session['recipes'] = results

        return render_template('recipes/recipes.html', recipes=recipes)
    
    results = session['recipes']
    recipes = [ShortRecipe(recipe) for recipe in results]
    return render_template('recipes/recipes.html', recipes=recipes)


@app.route('/search/test')
def search_test():

    form = SearchForm()

    return render_template('search-test.html', form=form)

########################################################################
# Recipe routes and functions:

def get_random_recipes(num):
    """Get num number of random recipes"""

    all_recipes = Recipe.query.all()
    if len(all_recipes) >= num:
        recipes = random.sample(all_recipes, num)

    response = requests.get(f"{BASE_URL}/random?apiKey={API_KEY}", 
                            params={"number": f"{num}"})

    resp = response.json()
    data = resp['recipes']
    recipes = [get_recipe(r['id']) for r in data]

    return recipes

def get_recipe(id):
    """Checks if recipe is in db, gets info from API if not and returns recipe."""

    recipe = Recipe.find_recipe(id)

    if recipe:
        return recipe

    response = requests.get(f"{BASE_URL}/{id}/information?apiKey={API_KEY}", params={"includeNutrition": "false"})

    resp = response.json()
    recipe = Recipe.make_recipe(resp)

    db.session.add(recipe)
    db.session.commit()
    return recipe


########################################################################
# Homepage and errors:

@app.route('/')
def homepage():
    """Show homepage."""

    if not g.user:
        return redirect('/signup')

    all_recipes = Recipe.query.all()
    if len(all_recipes) >= 8:
        recipes = random.sample(all_recipes, 8)
        return render_template('/recipes/recipes.html', recipes=recipes)

    recipes = get_random_recipes(8)

    flash(f"Welcome back, {g.user.username}!")

    return render_template('/recipes/recipes.html', recipes=recipes)  

############################################################################

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req  
