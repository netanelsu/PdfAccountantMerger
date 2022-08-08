from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask_mongoengine import MongoEngine
ROLES = ('ACCOUNTANT', 'CUSTOMER')
AVATARS = ('https://robohash.org/3EC.png?set=set4','https://robohash.org/293.png?set=set4','https://robohash.org/ZOB.png?set=set4')
db = MongoEngine()
class User(UserMixin, db.Document):
    # User authentication information
    username = db.StringField(default='')
    password_hash = db.StringField()
    email = db.EmailField()
    # User information
    first_name = db.StringField(default='')
    last_name = db.StringField(default='')
    # Relationships
    role = db.StringField(default='', choices = ROLES)
    Blocked = db.StringField(default='false')
    avatar =  db.StringField(default='', choices = AVATARS)
    def get_role (self):
        return self.role
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Inovice(UserMixin,db.Document):
    Inovice_year = db.StringField(default='')
    Inovice_month = db.StringField(default='')
    Inovice_pdf = db.StringField(default='')
    inovice_Customer = db.StringField(default='')
    inovice_Accountant = db.StringField(default='')

class Merged_pdf(UserMixin,db.Document):
    inovice_Accountant_mail = db.StringField(default='')
    PdfPath = db.StringField(default='')
   
