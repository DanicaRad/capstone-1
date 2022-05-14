"""Demo class for sifting through data for planning"""

from fractions import Fraction
from bs4 import BeautifulSoup, SoupStrainer

class ShortRecipe:
    """Short recipe for search results"""

    def __init__(self, res):
        self.id = res['id']
        self.title = res['title']
        self.image_url = res.get('image', None)
        self.readyInMinutes = res.get('readyInMinutes', None)
        self.servings = res.get('servings', None)

        