from models import Inovice
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo
# from wtforms.ext.sqlalchemy.fields import QuerySelectField
from models import ROLES,User
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit1 = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username1 = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password1 = PasswordField('Password', validators=[DataRequired()])
    #password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    role = SelectField('select role:', choices = [('ACCOUNTANT','ACCOUNTANT'),('CUSTOMER','CUSTOMER')])
    avatar = SelectField('select avatar:', choices = [('https://robohash.org/3EC.png?set=set4','cat1'),('https://robohash.org/293.png?set=set4','cat2'),('https://robohash.org/ZOB.png?set=set4','cat3')])
    submit2 = SubmitField('Sign Up')

class uploadInovice(FlaskForm):
    Inovice_pdf = StringField(default='')
    inovice_Customer = StringField(default='')
    inovice_Accountant = SelectField(u'Select Accountant', choices=[])
    submit = SubmitField('upload') 

class DownloadInovice(FlaskForm):
    submit = SubmitField('Download Merged PDf')