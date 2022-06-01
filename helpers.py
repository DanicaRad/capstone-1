"""Demo class for sifting through data for planning"""

from flask import session, g 
import requests
import random
from models import db, Recipe, RecipeTags, SimilarRecipes
from app import BASE_URL, API_KEY, API_KEY2, API_KEY3

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
        