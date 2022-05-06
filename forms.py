"""Forms for recipe search."""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SelectMultipleField, HiddenField, PasswordField, TextAreaField, BooleanField
from wtforms.validators import Optional, DataRequired, Email, Length
from search_params import cuisines, intolerances, diets, type, sort

class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    image_url = StringField('(Optional) Image URL')

class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

class UserEditForm(UserAddForm):
    """Form for editing user."""

    image_url = StringField('(Optional) Image URL')
    bio = TextAreaField('(Optional) Bio')

class ListForm(FlaskForm):
    """Form for users to make new list."""

    name = StringField('List Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    private = BooleanField('Private', validators=[Optional()])

class AddRecipeForm(FlaskForm):
    """Form to add recipe to user list."""



class SearchForm(FlaskForm):
    """Form for detailed recipe search"""

    query = StringField(
                    'Search',
                    validators=[Optional()])

    type = SelectField(
                    'Dish Type',
                    choices=type,
                    validators=[Optional()])

    cuisine = SelectMultipleField(
                    'Cuisine',
                    choices=cuisines,
                    validators=[Optional()])

    intolerances = SelectMultipleField(
                    'Food Intolerances',
                    choices=intolerances,
                    validators=[Optional()])

    diet = SelectField(
                    'Diet',
                    choices=diets,
                    validators=[Optional()])

    sort = SelectField(
                    'Sort By',
                    choices=sort,
                    validators=[Optional()],
                    default="meta-score")