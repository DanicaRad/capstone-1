"""Test for checking out API responses"""
from flask import Flask, render_template, request, flash, redirect, jsonify
import requests
from flask_debugtoolbar import DebugToolbarExtension
from models import Recipe


app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = "Winnie"
toolbar = DebugToolbarExtension(app)

API_KEY = '979dfa9f09634c8faf4ba8e387c1b0ab'
BASE_URL = f"https://api.spoonacular.com/recipes"
SIMILAR_URL = f"https://api.spoonacular.com/recipes/similar?apiKey={API_KEY}"


@app.route('/')
def get_data():

    querystring = {"tags":"vegetarian,dessert","number":"1", "stepBreakdown": "true", "extendedIngredients": "false"}
    response = requests.get(f"{BASE_URL}/random?apiKey={API_KEY}", querystring)
    resp = response.json()
    [data] = resp['recipes']
    obj = dict([(key, value) for key, value in data.items()])
    t = (type(data), len(data))
    recipe = Recipe(obj)

    similar = requests.get(SIMILAR_URL, params={"number": "1"})

    return render_template('test.html', data=data, recipe=recipe)