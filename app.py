
from http.client import HTTPException
import os

from flask import Flask, render_template, request, flash, redirect, jsonify, session, g, json
import requests
import random
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from helpers import ShortRecipe
from forms import ListForm, SearchForm, UserAddForm, LoginForm, UserAddForm, UserEditForm
from models import db, connect_db, User, List, Recipe, RecipeList, Favorites
from data.search_params import diets

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

app.config['TESTING'] = True

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

        flash(f"Welcome {user.username}!")
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

######################################################################
# General user routes:

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
        return redirect('/login')

    form = UserEditForm()
    if form.validate_on_submit():
        if User.authenticate(g.user.username, form.password.data):
            g.user.username = form.username.data
            g.user.email = form.email.data
            g.user.bio = form.bio.data
            g.user.image_url = form.image_url.data if form.image_url.data else g.user.image_url

            db.session.add(g.user)
            db.session.commit()

            flash("Profile updated!", "success")
            return redirect(f'/users/{g.user.id}')

        else:
            flash("Acces unauthroized; incorrect password.")
            return redirect('/login')

    return render_template('users/edit.html', form=form)

@app.route('/favorites')
def favorites():
    """Show user's favorite recipes."""

    if not g.user:
        flash("Access unauthorized", "danger")
        return redirect('/')

    favorites = g.user.favorites

    return render_template('users/favorites.html', recipes=favorites)

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
        private = form.private.data or False
        list = List(name=name, description=description, private=private, user_id=g.user.id)

        db.session.add(list)
        db.session.commit()

        flash(f"{list.name} created!", "success")
        return redirect('/')

    return render_template('lists/form.html', form=form)

@app.route('/users/<int:id>/lists')
def users_lists(id):
    """Shows user's own lists."""

    if not g.user or g.user.id != id:
        flash("Access unauthorized", "danger")
        return redirect(f'/login')

    return render_template('/lists/lists.html')

@app.route('/lists')
def show_all_lists():
    """Shows all lists that aren't private."""

    lists = List.query.filter(List.private == False).all()

    return render_template('lists/lists-base.html', lists=lists, recipe=False)

@app.route('/lists/<int:id>')
def show_list(id):
    """Shows recipelist if list user is curr_user."""

    list = List.query.get_or_404(id)

    if not g.user:

        if list.private == False:
            return render_template("lists/list.html", list=list)

        flash("This list is private", "danger")
        return redirect('/signup')

    if list.user_id == g.user.id:
        return render_template("lists/list.html", list=list)

    flash("This list is private", "danger")
    return redirect('/signup')

@app.route('/lists/<int:id>/delete', methods=['GET', 'POST'])
def delete_list(id):
    """Deletes user list in list.html"""

    list = List.query.get_or_404(id)

    if not g.user:
        flash("Action unauthorized", "danger")
        return redirect(f"/lists/{id}")

    if list.user_id == g.user.id:
    
        db.session.delete(list)
        db.session.commit()

        flash("List deleted", "warning")
        return redirect(f'/users/{g.user.id}/lists')

    flash("Action unauthorized", "danger")
    return redirect(f"/lists/{id}")


########################################################################### AXIOS post request List routes

@app.route('/lists/delete', methods=['GET', 'POST'])
def delete_list_from_lists():
    """Handles axios post request to delete list from lists in lists.html. Return json."""

    id = request.json['id']
    list = List.query.get_or_404(id)

    if not g.user:
        return (jsonify(message="Action unauthorized"), 401)

    if  list.user_id == g.user.id:

        db.session.delete(list)
        db.session.commit()

        return (jsonify(message="List deleted"), 200)

    return (jsonify(message="Action unauthorized"), 401)

@app.route('/lists/delete-from', methods=['GET', 'POST'])
def delete_from_list():
    """Deletes recipe from list from axios post request. Returns json."""

    if not g.user:
        return (jsonify(message="Action unauthorized"), 401)

    r_id = request.json['recipe']
    l_id = request.json['list']


    list = List.query.get_or_404(l_id)
    if list not in g.user.lists:
        return (jsonify(message="Action unauthorized"), 401)

    recipe = Recipe.query.get_or_404(r_id)
    if recipe in list.recipes:

        recipe_list = RecipeList.query.filter(
            RecipeList.list_id == l_id,
            RecipeList.recipe_id == r_id).one()

        db.session.delete(recipe_list)
        db.session.commit()

        return (jsonify(message="Recipe removed from list"), 200)
        
    return (jsonify(message="Recipe not found in list"), 202)

@app.route('/recipes/add-to-list', methods=['GET', 'POST'])
def add_to_list():
    """Add recipe to user list from axios request. Returns json."""

    r_id = request.json['recipe']
    l_id = request.json['list']

    list = List.query.get_or_404(l_id)
    recipe = get_recipe(r_id)

    if not g.user or list.user_id != g.user.id:
        return(jsonify(message="Action unauthorized"), 401)
    
    if recipe in list.recipes:
        return(jsonify(message="Duplicate recipe."), 202)

    recipe_list = RecipeList(list_id=l_id, recipe_id=recipe.id)
    db.session.add(recipe_list)
    db.session.commit()

    return(jsonify(message="Added to list!"), 200)

########################################################################### AXIOS post request Recipe routes

@app.route("/recipes/favorite", methods=["GET", "POST"])
def add_or_delete_favorite():
    """Adds recipe to user favorites if not in favorites from axios request. Returns json."""

    if not g.user:
        return (jsonify(message="You must be logged in or signup to add favorites"), 401)

    id = request.json['id']
    recipe = get_recipe(id)

    if recipe:

        if recipe in g.user.favorites:
            fav = Favorites.query.filter(Favorites.user_id == g.user.id,    Favorites.recipe_id == id).one()

            db.session.delete(fav)
            db.session.commit()

            return (jsonify(message="Removed from favorites"), 200)

        newfav = Favorites(user_id=g.user.id, recipe_id=id)
        db.session.add(newfav)
        db.session.commit()

        return (jsonify(message="Added to favorites!"), 200)

    return (jsonify(message="We couldn't find that recipe"), 404)

#####################################################################
######################################################################### Recipe routes:

@app.route('/recipes/<int:id>', methods=['GET', 'POST'])
def recipe_info(id):
    """Get and show recipe meta information from API."""

    recipe = get_recipe(id)
    similar = get_similar_recipes(id)
    # similar = get_similar_recipes(id)

    lists = List.query.filter(List.recipes.contains(recipe), List.private == False).all()

    return render_template('recipes/recipe.html', recipe=recipe, lists=lists, similar=similar)


@app.route('/search', methods=["GET", "POST"])
def search_form():
    """Show search form. Remove previous search results from session."""

    session.pop('recipes', None)

    form = SearchForm()

    return render_template('search.html', form=form)

def search_request(params):
    """Sends search request to API. Clears recipes saved in session and saves API response in session."""

    ## If recipes saved in session, clear ###
    session.pop('recipes', None)

    response = requests.get(
                        f"{BASE_URL}/complexSearch?apiKey={API_KEY}",
                        params)
    resp = response.json()
    recipes = resp['results']

    ## Saves new search results to session ##
    session['recipes'] = recipes

    return [get_recipe(recipe['id']) for recipe in recipes]


@app.route('/search/results', methods=['GET', 'POST'])
def detailed_search():
    """Shows search results, add results to session so user can return to results page."""

    form = SearchForm()

    if form.validate_on_submit():
        params = {
            "query": form.query.data,
            "type": form.type.data,
            "cuisine": form.cuisine.data,
            "intolerances": form.intolerances.data,
            "diet": form.diet.data,
            "number": "12",
            "sort": form.sort.data,
            "addRecipeInformation": "true"
        }

        recipes = search_request(params)

        return render_template('recipes/filter-recipes.html', recipes=recipes)
    
    ## if form not submitted, fetch saved recipes from session for recipes/recipes.hhtml rendering ##
    saved_recipes = session['recipes']

    recipes = [ShortRecipe(recipe) for recipe in saved_recipes]
    return render_template('recipes/filter-recipes.html', recipes=recipes)


@app.route('/quick-search', methods=['GET', 'POST'])
def quick_search():
    """Handle quick search form from navbar."""

    if request.method == 'POST':
        params = {
                "query": request.form['query'],
                "number": "12",
                "sort": "meta-score",
                "addRecipeInformation": "true"
            }
        recipes = search_request(params)

        return render_template('recipes/filter-recipes.html', recipes=recipes)
    
    ## if form not submitted, fetch saved recipes from session for recipes/recipes.hhtml rendering ##
    saved_recipes = session['recipes']

    recipes = [ShortRecipe(recipe) for recipe in saved_recipes]
    return render_template('recipes/filter-recipes.html', recipes=recipes)

# @app.route(f"/search/filter")
# def filter_recipes_by_tag():
#     """Filters recipes by tag or diet name... not sure yet this is my test route."""

######################################################################### Recipe helper functions:

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

def get_similar_recipes(id):
    """Checks session for similar recipes, if none, get from API using recipe id and saves to session."""

    if f"{id}" in session:
        return [ShortRecipe(r) for r in session[f"{id}"]]

    response = requests.get(f"{BASE_URL}/{id}/similar?apiKey={API_KEY}", params={"number": "4"})

    resp = response.json()
    id = f"{id}"
    session[id] = resp
    recipes = [ShortRecipe(r) for r in resp]

    print(f"******************************************** SESSION   {session[id]} ********************************************************************************")
    return recipes


######################################################################### Homepage and errors:

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

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 error"""

    return render_template("404.html"), 404


############################################################################

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req  

