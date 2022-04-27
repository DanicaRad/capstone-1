"""Forms for recipe search."""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SelectMultipleField, HiddenField, PasswordField
from wtforms.validators import Optional, DataRequired, Email, Length
from search_params import cuisines, intolerances, diets, type

class AddUserForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    image_url = StringField('(Optional) Image URL')

class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

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
                    validators=[Optional()],
                    default=False)

    intolerances = SelectMultipleField(
                    'Food Intolerances',
                    choices=intolerances,
                    validators=[Optional()],
                    default=False)

    diet = SelectField(
                    'Diet',
                    choices=diets,
                    validators=[Optional()],
                    default=False)

    number = HiddenField('number', default="10")