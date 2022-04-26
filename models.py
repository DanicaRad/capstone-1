"""Demo class for sifting through data for planning"""

class Recipe:

    def __init__(self, obj):
        self.id = obj['id']
        self.title = obj['title']
        self.source = obj['sourceName']
        self.source_url = obj['sourceUrl']
        self.image_url = obj['image']
        self.summary = self.strip(obj['summary'])
        self.instructions = self.split(obj['instructions'])
        self.total_min = obj['readyInMinutes']
        self.servings = obj['servings']
        self.ingredients = obj['extendedIngredients']

    def __repr__(self):
        return f"<title={self.title}, source_url={self.source_url}, image_url={self.image_url}, instructions={self.instructions}>"

    @classmethod
    def strip(self, str):
        """Removes HTML formating from body of text"""
        stripped = str.replace('<b>', '')
        strip = stripped.replace('</b>', '')
        idx = strip.find('spoonacular') + 10
        i = strip.find('.', idx) + 1
        return strip[0:i]

    def split(self, str):
        """Removes suggested recipe HTML links within summary text body."""
        split = str.split('.')
        split.pop(-1)
        return [s.strip() for s in split]