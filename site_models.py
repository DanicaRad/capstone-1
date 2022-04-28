"""Demo class for sifting through data for planning"""

from fractions import Fraction

class APIRecipe:
    """Detailed recipe"""

    def __init__(self, res):
        self.id = res['id']
        self.title = res['title']
        self.source = res['sourceName']
        self.source_url = res['sourceUrl']
        self.image_url = res['image']
        self.summary = self.strip_all(res['summary'])
        self.summary_long = res['summary']
        self.instructions = self.split(res['instructions'])
        self.total_min = res['readyInMinutes']
        self.servings = res['servings']
        self.ext_ingredients = res['extendedIngredients']
        self.ingredients = [Ingredient(dict) for dict in res['extendedIngredients']]

    def __repr__(self):
        return f"<title={self.title}, source_url={self.source_url}, image_url={self.image_url}, instructions={self.instructions}>"

    def parse_data(self, data):
        """Parse API response into Recipe model."""

        recipe = dict([(key, value) for key, value in data.items()])
        return APIRecipe(recipe)

    def strip_b(self, str):
        """Removes HTML formating from body of text"""
        strip = str.replace('<br>', '')
        strip1 = strip.replace('<b>', '')
        stripped = strip1.replace('</b>', '')
        return stripped

    def strip_li(self, str):
        """Removes any list item html."""

        strip1 = str.replace('<li>', '')
        strip2 = strip1.replace('</li>', '')
        strip3 = strip2.replace('<ol>', '')
        stripped = strip3.replace('<ul>', '')
        return stripped

    def strip_links(self, str):
        """Strips suggested recipe links from body of text."""

        split = str.split('.')
        for str in split:
            if "<" in str:
                slice = split[0:split.index(str)]
                return ".".join(slice) + "."


    def strip_all(self, str):
        """Strips all unwanted HTML elements from text body."""
        
        strip1 = self.strip_b(str)
        strip2 = self.strip_li(strip1)
        stripped = self.strip_links(strip2)
        return stripped

    def split(self, str):
        """Removes suggested recipe HTML links within summary text body."""
        strip1 = self.strip_b(str)
        strip2 = self.strip_li(strip1)
        split = strip2.split('.')
        split.pop(-1)
        return [s.strip() for s in split]

    def parse_ingredients(self, lst):
        """Extracts ingredients and quantity from response ingredient dict."""
        for dict in lst:
            self.ing.name = dict["name"]
            self.ing.original = dict["original"]
            self.ing.amount = dict["amount"]
            self.ing.unit = dict["unit"]


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
        