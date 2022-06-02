[**Spoonacular API**](https://spoonacular.com/food-api)  
[https://spoonacular.com/food-api](https://spoonacular.com/food-api)


### Using the [**Spoonacular API**](https://spoonacular.com/food-api), this app allows users to make their own recipe books!  

Users can create accounts where they can create public or private recipe lists and save recipes to lists and/or favorites to keep their recipes organized. Recipe search function allows users to filter and sort according to nutritional value, popularity, dietary preferences, cuisine, dish type and total cook time. Lists, favorites and user profiles can be edited or deleted.  

Users can browse other user's public lists for inspirtion. Gives similar recipe suggestions and lists featuring recipes to help users discover new things to put on their dinner table. User profiles and lists fearture "top dietary tags", so other users can browse lists/other users lists based on common dietary preferences. 

Lists and favorites display recipes in a card format featuring recipe photo, title, any dietary tags, nutritional score and likes the recipe has, and dropdowns of description, ingredients (with togglable metric/us conversions), instructions and cook time. The dropdown format keeps the recipe display compact while allowing users to view multiple recipe ingredients on a single page to make planning and shopping less work.  

I hate cooking, so with that in mind, I tried to create an app that makes the prep process as easy and painless as possible. 

## Tech Stack  

Python 3.10.0

- This project uses the Python web application framework [Flask](https://palletsprojects.com/p/flask/) and all it's dependencies, including [Jinja2](https://palletsprojects.com/p/jinja/) for HTML templates.     

- A [PostgreSQL](https://www.postgresql.org/) database and [SQLAlchemy](https://www.sqlalchemy.org/) library with the help of [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/en/2.x/) to work with the app's data.  

- [Flask-WTF](https://wtforms.readthedocs.io/en/3.0.x/) extension with [WTForms](https://wtforms.readthedocs.io/en/3.0.x/) library integration for user input data.

- The latest Beta version of [Bootstrap v5.2](https://getbootstrap.com/) with [compiled JS](https://getbootstrap.com/docs/5.2/getting-started/javascript/) helped make this app nicer to look at and easier to use.  
- [Spoonacular API](https://spoonacular.com/food-api) for all the recipes and recipe data!


