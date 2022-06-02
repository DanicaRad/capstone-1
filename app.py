
from http.client import HTTPException
import os

from flask import Flask, render_template, request, flash, redirect, jsonify, session, g, url_for
from flask_migrate import Migrate
import requests
import random
import ast
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from forms import ListForm, SearchForm, UserAddForm, LoginForm, UserAddForm, UserEditForm
from models import db, connect_db, User, List, Recipe, RecipeList, Favorites, Tag, RecipeTags, SimilarRecipes

CURR_USER_KEY = "curr_user"
BASE_URL = f"https://api.spoonacular.com/recipes"
API_KEY = '979dfa9f09634c8faf4ba8e387c1b0ab'
API_KEY2 = 'e9bf0ccc334c426094129c237e94055a'
API_KEY3 = '5de13e67157c448f9608ba2c8d0b825c'

app = Flask(__name__)

app.config['TESTING'] = True

app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///spoonacular').replace("postgres://", "postgresql://", 1))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = "Winnie"
toolbar = DebugToolbarExtension(app)
migrate = Migrate(app, db)

connect_db(app)

#########################################################################
# User signup / login / logout 

@app.before_first_request
def add_apiKey_to_g():
    """Adds API key to Flask global."""

    g.API_KEY = API_KEY
    session['API_KEY'] = API_KEY

@app.before_request
def add_user_and_API_to_g():
    """If we're logged in, add curr user to Flask global."""

    if 'API_KEY' in session:
        g.API_KEY = session['API_KEY']

    else:
        g.API_KEY = API_KEY

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

    if g.user:
        if g.user.id == id:
            fav_tags = g.user.top_tags(g.user.favorites) if g.user.favorites else None

            return render_template('users/user.html', user=g.user, fav_tags=fav_tags)


    user = User.query.get_or_404(id)

    fav_tags = user.top_tags(user.favorites) if user.favorites else None

    lists = [list for list in user.lists if user.lists and list.private == False]

    return render_template('/users/user.html', user=user, fav_tags=fav_tags, lists=lists)

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
        return redirect(request.referrer)

    favorites = g.user.favorites

    return render_template('users/favorites.html', recipes=favorites)


########################################################################
# List routes:

@app.route('/lists/new', methods=['GET', 'POST'])
def add_list():
    """Add a list for current user."""

    back = request.referrer

    if not g.user:
        flash("You must signup or login to make a new recipe list.", "warning")
        return redirect(back)

    form = ListForm()

    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data or None
        private = form.private.data or False
        list = List(name=name, description=description, private=private, user_id=g.user.id)
        back = form.request_referrer.data

        db.session.add(list)
        db.session.commit()

        flash(f"{list.name} created!", "success")
        return redirect(back)

    return render_template('lists/form.html', form=form, back=back)

@app.route('/lists/<id>/edit', methods=['GET', 'POST'])
def edit_list(id):
    """Edit users list."""

    back = request.referrer

    if not g.user:
        flash("Unauthorized action", "warning")
        return redirect(back)

    list = List.query.get_or_404(id)

    if list.user.id != g.user.id:
        flash("Unauthorized action", "warning")
        return redirect(back)

    form = ListForm(name=list.name, description=list.description, private=list.private)
    
    if form.validate_on_submit():
       list.name = form.name.data or list.name
       list.description = form.description.data or list.description
       list.private = form.private.data or list.private
       back = form.request_referrer.data

       db.session.add(list)
       db.session.commit()

       flash("List updated!", "success")
       return redirect(url_for('show_list', id=id))

    return render_template('lists/edit.html', form=form, list=list, back=back)

@app.route('/users/<username>/lists')
def users_lists(username):
    """Shows user's own lists."""

    if g.user.username == username:
        lists = g.user.lists
        return render_template('lists/users-lists.html', lists=lists, username=username)

    user = User.query.filter(User.username == username).first()

    if not user:
        return render_template('404.html', var=f"User {username}")

    lists = List.query.filter(List.private == False, List.user_id == user.id).all()
    return render_template('lists/users-lists.html', lists=lists, username=username)

@app.route('/lists')
def show_all_lists():
    """Shows all lists that aren't private."""

    lists = List.query.filter(List.private == False).all()

    return render_template('lists/all-lists.html', lists=lists, recipe=False)

@app.route('/lists/<int:id>')
def show_list(id):
    """Shows recipelist if list user is curr_user."""

    list = List.query.get_or_404(id)
    user = list.user
    top_tags = user.top_tags(list.recipes)

    if list.private == False:
        return render_template("lists/list.html", list=list, top_tags=top_tags)

    if g.user and list.user_id == g.user.id:
        return render_template("lists/list.html", list=list, top_tags=top_tags)

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


########################################################################### 
# AXIOS post request List routes

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

        if list.image_url == recipe.image_url:
            list.image_url = list.recipes[1].image_url
            db.session.add(list)

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

    if len(list.recipes) == 0:
        list.image_url = recipe.image_url
        db.session.add(list)

    recipe_list = RecipeList(list_id=l_id, recipe_id=recipe.id)
    db.session.add(recipe_list)
    db.session.commit()

    return(jsonify(message="Added to list!"), 200)

###########################################################################
## AXIOS post request Recipe routes

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

            recipe.likes = recipe.likes - 1

            db.session.add(recipe)
            db.session.delete(fav)
            db.session.commit()

            return (jsonify(message="Removed from favorites", likes=f"{recipe.likes}"), 200)

        newfav = Favorites(user_id=g.user.id, recipe_id=id)

        recipe.likes = recipe.likes + 1
        db.session.add(recipe)

        db.session.add(newfav)
        db.session.commit()


        return (jsonify(message="Added to favorites!", likes=f"{recipe.likes}"), 200)

    return (jsonify(message="We couldn't find that recipe"), 404)

############################################################################################
## Recipe routes:


@app.route('/recipes/<int:id>', methods=['GET', 'POST'])
def recipe_info(id):
    """Get and show recipe meta information from API."""

    recipe = Recipe.query.get_or_404(id)

    lists = List.query.filter(List.recipes.contains(recipe), List.private == False).all()
    recipes = get_similar_recipes(id) 

    if not recipes and g.API_KEY == API_KEY3:
        return render_template('recipes/recipe.html', recipe=recipe, lists=lists, recipes=recipes)

    if not recipes:
        return redirect(url_for('recipe_info', id=id))

    return render_template('recipes/recipe.html', recipe=recipe, lists=lists, recipes=recipes)

def search_request(params, sort):
    """Sends search request to API. Clears recipes saved in session and saves API response in session."""

    ## If recipes saved in session, clear ###
    session.pop('recipes', None)

    response = requests.get(
                        f"{BASE_URL}/complexSearch?apiKey={g.API_KEY}",
                        params) 

    if response.status_code != 200 and g.API_KEY == API_KEY3:
        return None

    if response.status_code != 200:
        switch_API_keys()
        return None

    resp = response.json()
    search_results = resp['results']

    ## Saves new search results to session ##
    ids = [recipe['id'] for recipe in search_results]
    recipes = get_recipes(ids)

    session['recipes'] = ids
    return Recipe.sort_by(sort, ids)

@app.route('/quick-search', methods=['GET', 'POST'])
def quick_search():
    """Handle quick search form from navbar."""

    session.pop('recipes', None)

    if request.method == 'POST':
        params = {
                "query": request.form['query'],
                "number": "20",
                "addRecipeInformation": "true"
            }
        return redirect(url_for('search', params=params, sort="likes"))


@app.route('/search', methods=['GET', 'POST'])
def search_form():
    """Handle form submission. If not submitted, present form."""

    session.pop('recipes', None)

    form = SearchForm()

    if form.validate_on_submit():

        params = {
            "query": form.query.data,
            "type": form.type.data,
            "cuisine": form.cuisine.data,
            "intolerances": form.intolerances.data,
            "diet": form.diet.data,
            "number": "20",
            "addRecipeInformation": "true"
        }

        sort = form.sort.data

        return redirect(url_for('search', params=params, sort=sort))

    return render_template('search.html', form=form)

@app.route(f'/search/<params>sort-by=<sort>', methods=['GET', 'POST'])
def search(params, sort):
    """Handle search request, check for saved search results in session, present if saved."""

    tags = Tag.query.order_by('tag_name').all()

    p = ast.literal_eval(params)
    query = p['query']

    if 'recipes' in session:
        ids = session['recipes']
        recipes = Recipe.sort_by(sort, ids)

        return render_template('recipes/search-results.html', recipes=recipes, query=query, tags=tags, params=params)

    recipes = search_request(p, sort)

    if not recipes and g.API_KEY == API_KEY3:
        return render_template("500.html")

    if not recipes:
        return redirect(url_for('search', params=params, sort=sort))

    return render_template('recipes/search-results.html', recipes=recipes, query=query, tags=tags)

@app.route(f'/search/<query>?sort-by=<sort>')
def sort_search(query, sort):
    """Sorts search results."""

    tags = Tag.query.order_by('tag_name').all()

    if 'recipes' in session:
        ids = session['recipes']
        sorted = Recipe.sort_by(sort, ids)

        return render_template('recipes/search-results.html', recipes=sorted, query=query, tags=tags)

    return render_template('404.html')

@app.route(f'/recipes/filter/<tag>')
def filter_by_tag(tag):
    """Filters recipes by tag."""

    tags = Tag.query.order_by('tag_name').all()

    if tag in session['filters']:
        i = session['filters'].index(tag)
        session['filters'].pop(i)

        if session['filters'] == []:
            all_recipes = Recipe.query.all()
            recipes = random.sample(all_recipes, 12)

            return render_template("recipes/filter-recipes.html", recipes=recipes, tags=tags, selected=None)

    selected = list(session['filters'])
    selected.append(tag)
    session['filters'] = selected

    saved_tags = Tag.query.filter(Tag.tag_name.in_(selected)).all()
    tag_ids = [tag.id for tag in saved_tags]

    recipe_tags = RecipeTags.query.filter(RecipeTags.tag_id.in_(tag_ids)).all()
    recipe_ids = [recipe.recipe_id for recipe in recipe_tags]

    recipes = [get_recipe(id) for id in recipe_ids]

    return render_template("recipes/filter-recipes.html", recipes=recipes, tags=tags, selected=selected)

#################################################################################
## not used in app, used to fill in recipe data gaps if any are found.

@app.route('/get-recipe-data', methods=['GET', 'POST'])
def get_recipe_data():

    db.session.rollback()

    db_recipes = Recipe.query.filter(Recipe.likes == None, Recipe.health_score == None).all()
    ids = str([recipe.id for recipe in db_recipes])
    str_ids = ids[1:-1].replace(" ", "")

    response = requests.get(f"{BASE_URL}/informationBulk?apiKey={g.API_KEY}", params={"ids": f"{str_ids}", "includeNutrition": "false"})
    
    if response.status_code != 200:
        switch_API_keys()
        return redirect(request.referrer)

    resp = response.json()

    for res in resp:
        recipe = Recipe.query.get(res['id'])
        recipe.likes = res['aggregateLikes']
        recipe.health_score = res['healthScore']
        db.session.add(recipe)

    db.session.commit()

    return redirect(request.referrer)


######################################################################### 
## Recipe helper functions:

def get_random_recipes(num):
    """Get num number of random recipes"""

    all_recipes = Recipe.query.all()
    if len(all_recipes) >= num:
        recipes = random.sample(all_recipes, num)

    response = requests.get(f"{BASE_URL}/random?apiKey={g.API_KEY}", 
                            params={"number": f"{num}"})

    if response.status_code != 200:
        switch_API_keys()
        return None

    resp = response.json()
    data = resp['recipes']
    recipes = [get_recipe(r['id']) for r in data]

    return recipes

def get_recipe(id):
    """Checks if recipe is in db, gets info from API if not and returns recipe."""

    recipe = Recipe.query.filter_by(id=id).first()

    if recipe:
        return recipe

    response = requests.get(f"{BASE_URL}/{id}/information?apiKey={g.API_KEY}", params={"includeNutrition": "false"})

    if response.status_code != 200:
        switch_API_keys()
        return None

    resp = response.json()
    recipe = Recipe.make_recipe(resp)

    db.session.add(recipe)
    db.session.commit()

    ## runs after recipe added to db since it uses recipe.id as foreign key
    RecipeTags.get_recipe_tags(resp)

    return recipe


def get_recipes(ids):
    "Queries DB first then API to get bulk recipes by id."

    db_recipes = Recipe.query.filter(Recipe.id.in_(ids)).all()

    db_ids = set(recipe.id for recipe in db_recipes)
    all_ids = set(ids)
    get_ids = str(all_ids - db_ids)
    str_ids = get_ids[1:-1].replace(" ", "")

    response = requests.get(f"{BASE_URL}/informationBulk?apiKey={g.API_KEY}", params={"ids": f"{str_ids}", "includeNutrition": "false"})
    
    if response.status_code != 200:
        switch_API_keys()
        return None

    resp = response.json()

    recipes = [Recipe.make_recipe(r) for r in resp]

    db.session.add_all(recipes)
    db.session.commit()

     ## gets tags from API response and adds to RecipeTags table, commits to db
    for r in resp:
        RecipeTags.get_recipe_tags(r)

    all_recipes = db_recipes + recipes

    return all_recipes

def get_similar_recipes(id):
    """Checks session for similar recipes, if none, get from API using recipe id and saves to session."""

    recipe = get_recipe(id)
    if len(recipe.similar) >= 4:
        similar = random.sample(recipe.similar, 4)
        return similar

    num = 4 - len(recipe.similar)

    response = requests.get(f"{BASE_URL}/{id}/similar?apiKey={g.API_KEY}", params={"number": f"{num}"})

    if response.status_code != 200:
        switch_API_keys()
        return None

    resp = response.json()
    ids = [r['id'] for r in resp]
    recipes = get_recipes(ids)

    for r in recipes:
        SimilarRecipes.add_similar(id, r.id)

    return recipe.similar


def switch_API_keys():
    """Checks if quota limit with API key has been reached. Switches API keys if it has"""

    if g.API_KEY == API_KEY:
        session['API_KEY'] = API_KEY2
        return None

    elif g.API_KEY == API_KEY2:
        session['API_KEY'] = API_KEY3
        return None

    elif g.API_KEY == API_KEY3:
        return None

######################################################################### 
## Homepage and errors:

@app.route('/')
def homepage():
    """Show homepage."""

    all_recipes = Recipe.query.all()

    if len(all_recipes) >= 20:
        recipes = random.sample(all_recipes, 20)
        return render_template('/recipes/recipes.html', recipes=recipes)

    recipes = get_random_recipes(8)

    if not g.user:
        flash(f"Welcome! Login or signup to start making your own cook books!")
        return render_template('/recipes/recipes.html', recipes=recipes)

    flash(f"Welcome back, {g.user.username}!")
    
    return render_template('/recipes/recipes.html', recipes=recipes)


@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 error"""

    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 error."""

    return render_template("500.html"), 500

@app.route('/error')
def show_error_page():
    """Route for Heroku Error URL."""

    return render_template('error.html')



############################################################################

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req  


