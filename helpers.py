"""Demo class for sifting through data for planning"""

from fractions import Fraction
from bs4 import BeautifulSoup, SoupStrainer

class ShortRecipe:
    """Short recipe for search results"""

    def __init__(self, res):
        self.id = res['id']
        self.title = res['title']
        self.image_url = res['image']
        