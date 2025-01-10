from flask_wtf import Form
from wtforms import StringField, PasswordField, ValidationError, SelectField
from wtforms.validators import DataRequired, Email, Length, AnyOf, URL, EqualTo
# import bcrypt
from model import User
from flask import flash
from helper import user_login_validation
from model import *


class SignUp(Form):
    name = StringField('name', validators=[DataRequired(), Length(min=4, max=24)])
    email = StringField('email', validators=[DataRequired(), Length(min=8, max=64), Email()])
    password = PasswordField('password', validators=[DataRequired(), Length(min=6)])


class Login(Form):
    email = StringField(
        'email',
        validators=[DataRequired(), Length(min=8, max=64), Email()])
    password = PasswordField(
        'password',
        validators=[DataRequired(), Length(min=6)])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.user = None

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False
        self.user = user_login_validation(self.email.data, self.password.data)
        if self.user is None:
            flash('Wrong email or password')
            return False
        else:
            return True


class CreatePlaylist(Form):
    name = StringField(
        'name',
        validators=[DataRequired(), Length(min=4, max=255)])
    privacy = SelectField(
        'privacy',
        coerce=int,
        choices=list(PlaylistPrivacy.select().tuples()),
        validators=[DataRequired()])
    style = SelectField(
        'style',
        coerce=int,
        choices=list(PlaylistStyle.select().tuples()),
        validators=[DataRequired()])

class Profile(Form):
    name = StringField('name', validators=[DataRequired(), Length(min=4, max=24)])
    phrase = StringField('name', validators=[Length(min=0, max=255)])
    picture = StringField('Picture URL', validators=[URL()], message="Must be a valid url")
    old_password = PasswordField('Current password', validators=[DataRequired(), Length(min=6)])
    password = PasswordField('New Password', [DataRequired(), EqualTo('confirm', message='Passwords must match')])
    confirm  = PasswordField('Repeat Password')

