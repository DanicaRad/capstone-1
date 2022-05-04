import requests
from models import db, connect_db, User, List, Recipe, RecipeList, Favorites
from app import API_KEY, BASE_URL

def get_recipe(id):
    """Checks if recipe is in db, gets info from API if not and returns recipe."""

    response = requests.get(f"{BASE_URL}/{id}/information?apiKey={API_KEY}", params={"includeNutrition": "false"})

    resp = response.json()

    # check if recipe is already in db, add if not
    dbrecipe = Recipe.find_recipe(resp['id'])

    if dbrecipe:

        return dbrecipe

    recipe = Recipe.make_recipe(resp)

    db.session.add(recipe)
    db.session.commit()
    return recipe



    
