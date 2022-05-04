"""Demo class for sifting through data for planning"""

from fractions import Fraction
from bs4 import BeautifulSoup, SoupStrainer

class APIRecipe:
    """Detailed recipe"""

    def __init__(self, res):
        self.id = res['id']
        self.title = res['title']
        self.source = res['sourceName'] if res['sourceName'] else "View Source"
        self.source_url = res['sourceUrl']
        self.image_url = res.get('image', '/static/images/default-recipe.jpg')
        self.summary = self.clean_text(res['summary'])
        self.instructions = self.strip_HTML(res['instructions'])
        self.total_min = res['readyInMinutes']
        self.dish_types = res['dishTypes']
        self.servings = res['servings']
        self.ingredients = [r['original'] for r in res['extendedIngredients']]

        self.us = list(self.get_ingredient(r, "us") for r in res["extendedIngredients"])

        self.metric = [self.get_ingredient(r, "metric") for r in res["extendedIngredients"]]

    def __repr__(self):
        return f"<title={self.title}, source_url={self.source_url}, image_url={self.image_url}, instructions={self.instructions}>"

    def strip_HTML(self, res):
        """Uses BeautifulSoup library to remove all HTML elements from text."""

        soup = BeautifulSoup(res)
        return soup.get_text()

    def clean_text(self, res):
        """Removes sentences with suggested recipe links and strips all other HTML."""

        split = res.split('. ')
        str = ". ".join([str for str in split if "<a" not in str or "http:" not in str]) + "."

        return self.strip_HTML(str)

    def get_ingredient(self, res, ms):
        """Make dictionary of ingredients"""

        name =  res["name"]
        mu = res["measures"][ms]
        unit = mu["unitShort"]
        num = mu["amount"]

        if num.is_integer() or num >= 1:
            return f"{int(num)} {unit} {name}"

        fract = Fraction(num).limit_denominator(9)
        return f"{fract.numerator}/{fract.denominator} {unit} {name}"

    def get_amount(self, num):
        """Format floats in ingredient amounts as fraction ratios"""

        if num.is_integer() or num >= 1:
            return int(num)

        fract = Fraction(num).limit_denominator(9)
        return f"{fract.numerator}/{fract.denominator}"

    def get_conversions(self, res):
        """Make dict from measurement conversions"""

        amount =  self.get_amount(res["amount"])
        unit =  res["unitShort"]

        return f"{amount}  {unit}"


    def parse_ingredients(self, res, ms):
        """Format floats in ingredient amounts as fraction ratios"""

        name = res["name"]


        num = res["amount"]

        if num.is_integer() or num >= 1:
            return int(num)

        fract = Fraction(num).limit_denominator(9)
        return f"{fract.numerator}/{fract.denominator}"


class Ingredient:
    
    def __init__(self, dict):
        self.name = dict["name"]
        self.original = dict["original"]
        self.amount = self.get_amount(dict["amount"])
        self.float_amount = dict["amount"]
        self.unit = dict["unit"]
        self.us = self.get_conversions(dict["measures"]["us"])
        self.metric = self.get_conversions(dict["measures"]["metric"])

    def get_amount(self, num):
        """Format floats in ingredient amounts as fraction ratios"""

        if num.is_integer() or num >= 1:
            return int(num)

        fract = Fraction(num).limit_denominator(9)
        return f"{fract.numerator}/{fract.denominator}"

    def get_conversions(self, dict):
        """Make dict from measurement conversions"""
        return {
            "amount": self.get_amount(dict["amount"]),
            "unit": dict["unitShort"]
        }

class ShortRecipe:
    """Short recipe for search results"""

    def __init__(self, res):
        self.id = res['id']
        self.title = res['title']
        self.image_url = res['image']
        