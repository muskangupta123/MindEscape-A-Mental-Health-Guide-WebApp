from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo

from wtforms import Form, StringField, PasswordField, validators

class RegisterForm(Form):
    name = StringField('Name', [
        validators.Length(min=1, max=50),
        validators.DataRequired()])
    username = StringField('Username', [
        validators.Length(min=4, max=25),
        validators.DataRequired()])
    email = StringField('Email', [
        validators.Length(min=6, max=50),
        validators.Email(),
        validators.DataRequired()])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
