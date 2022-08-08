import time

from flask.globals import session
from models import User,Inovice,Merged_pdf
import os
from boto.s3.connection import S3Connection, Bucket, Key
import smtplib
from email.message import EmailMessage
import PyPDF2
from datetime import datetime
from pdf_mail import sendpdf 
# import schedule
from datetime import date
import boto3
import boto
import boto.s3.connection
from flask import Flask, config, current_app, flash, Response, request, render_template_string, render_template, jsonify, redirect, url_for
from flask_mongoengine import MongoEngine
from bson.objectid import ObjectId
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from flask_principal import Principal, Permission, RoleNeed, identity_changed, identity_loaded, Identity, AnonymousIdentity, UserNeed

from forms import LoginForm, RegistrationForm,uploadInovice,DownloadInovice
from models import ROLES
import atexit

from apscheduler.schedulers.background import BackgroundScheduler

from flask_dropzone import Dropzone
basedir = os.path.abspath(os.path.dirname(__file__))
access_key = '**********************'
secret_key = '######################'


# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-MongoEngine settings
    MONGODB_SETTINGS = {
        'db': 'PdfMerger',
        'host': 'mongodb://localhost:27017/PdfMerger',
    }

app = Flask(__name__)
app.config.from_object(__name__+'.ConfigClass')



app.config.update(
    UPLOADED_PATH = os.path.join(basedir, 'uploads'),
    DROPZONE_MAX_FILE_SIZE = 1024,
    DROPZONE_TIMEOUT = 5*60*1000),

app.config['DROPZONE_UPLOAD_MULTIPLE'] = True
app.config['DROPZONE_PARALLEL_UPLOADS'] = 5    


dropzone = Dropzone(app)


def mergePdf():
    s3 = boto3.resource('s3',
                        aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key,
                        )
    # s3 = boto3.resource('s3',)
    samefiles = False
    year = datetime.now().year
    month = datetime.now().month
    if month == 1:
        month = 12
        year = year - 1
    for bucket in s3.buckets.all():
        for obj in bucket.objects.all():
            print('{0}:{1}'.format(bucket.name, obj.key))
            tmpl = obj.key.split('/')
            if len(tmpl) > 4 and int(tmpl[2]) == year and int(tmpl[3]) == month:
                bucket.download_file('/'.join(tmpl), './Downloads/{}'.format(tmpl[-1]))
                accountant = tmpl[0]
                costumer = tmpl[1]
                samefiles = True
            elif samefiles:
                samefiles = False
                Merge_pdf(['./Downloads/'+f for f in os.listdir('./Downloads/')])
                send_merged(accountant,costumer)
                os.remove('./Downloads/MergedFiles.pdf')
                continue
scheduler = BackgroundScheduler()
scheduler.add_job(func=mergePdf, trigger="interval", month='1-12', day='last',hour= '23' )
scheduler.start()
db = MongoEngine()
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# create role based auth
principals = Principal(app)
admin_permission = Permission(RoleNeed('Admin'))
student_permission = Permission(RoleNeed('Student'))
lecturer_permission = Permission(RoleNeed('Lecturer'))

gmail_user = '*******************'
gmail_password = '******************'

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except:
        redirect('index')


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    # Assuming the User model has a list of roles, update the
    # identity with the roles that the user provides
    if hasattr(current_user, 'role'):
        identity.provides.add(RoleNeed(current_user.role))


@app.route('/new', methods=['GET', 'POST'])
def login():
    
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form1 = LoginForm()
    form2 = RegistrationForm()
   
    if form1.validate_on_submit():
        user = User.objects(username=form1.username.data).first()
        if user is None or not user.check_password(form1.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form1.remember_me.data)
        identity_changed.send(current_app._get_current_object(),
                              identity=Identity(user.username))
        return redirect(url_for('index'))
    if form2.validate_on_submit():
            register(form2)
    return render_template('new.html', title='Sign In', form1=form1, form2=form2)

@app.route('/logout')
def logout():
    logout_user()
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register(form):
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = form
    if form.validate_on_submit():  
        create_user(form)
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('index'))
    return render_template('new.html', title='Register', form=form)
    # else:
    #     flash('username Already exists')
    #     return redirect('/register')

def create_Inovice(form,u):
    inovice = Inovice(Inovice_pdf=form.Inovice_pdf.data,inovice_Customer = u.username)
    inovice.save()


def create_user(form):
    user = User(username=form.username1.data, email=form.email.data)
    user.role = form.role.data
    user.first_name = form.first_name.data
    user.last_name = form.last_name.data
    user.set_password(form.password1.data)
    user.avatar = form.avatar.data
    user.save()

def Merge_pdf(list):
    try:
        pdfWriter = PyPDF2.PdfFileWriter()
        for i in list:
            pdfFile = open(i,'rb')
            pdfReader = PyPDF2.PdfFileReader(pdfFile)
            for pageNum in range(pdfReader.numPages):
                pdfWriter.addPage(pdfReader.getPage(pageNum))
            os.remove(i)
        today = datetime.today()
        YandM = datetime(today.year, today.month, 1)
        timeString = str(YandM).split(" ")[0]

        loc = os.path.join(basedir, 'Downloads')
        pdfOutputFile = open(os.path.join(loc, 'MergedFiles.pdf', 'wb'))
        pdfWriter.write(pdfOutputFile)
        pdfOutputFile.close()
        pdfFile.close()
        # return os.path.join(loc, '{0}-{1}-MergedFiles.pdf'.format(current_user.username,timeString))
        return
    except:
        flash("Opps!! Error opening file!")

def send_merged(acountant,costumer):
    acountant_mail = User.objects.filter(role = "ACCOUNTANT" ,username=acountant ).first().email
    path = ""
    loc = os.path.join(basedir, 'Downloads')
    paths = loc.split('\\')
    seprator = '/'
    k = sendpdf("{}".format(gmail_user),
                    "{}".format(acountant_mail),
                    "{}".format(gmail_password),
                    "Inovice from {}".format(costumer),
                    "Hello, here is my inovices. Have a good day!",
                    "{}".format('MergedFiles.pdf'),
                    "{}".format('./Downloads/MergedFiles.pdf'))
    k.email_send()


@app.route('/')
@app.route('/index')
@login_required
def index():
    session['file'] = []
    user = User.objects(username=current_user.username).first()
    send_merged()
    if user.role == 'ACCOUNTANT':
        return render_template('Accountant.html', user=user)
    elif user.role == 'CUSTOMER':
        return render_template('Customer.html', user=user)
    else:
        return redirect(url_for('index'))


@app.route('/Customer/DownloadInoviceInovices', methods=['GET','POST'])
@login_required
def Download_merged_pdf():

    u = User.objects(username=current_user.username).first()
    form = DownloadInovice()
    # try:
    if form.validate_on_submit():
        Acountant_username = Inovice.objects(inovice_Customer = current_user.username).first().inovice_Accountant
        mail = User.objects(username = Acountant_username ).first().email
        pathtofile = Merge_pdf(u)
        merged = Merged_pdf(inovice_Accountant_mail = mail,PdfPath = pathtofile)
        merged.save()
        path = ""
        loc = os.path.join(basedir, 'Downloads')
        paths = loc.split('\\')
        seprator = '/'
        
        k = sendpdf("{}".format(gmail_user), 
                    "{}".format(mail), 
                    "{}".format(gmail_password), 
                    "Inovice from {}".format(current_user.username), 
                    "Hello, here is my inovices. Have a good day!",
                    "{}".format(pathtofile.split('\\')[-1].split('.')[0]), 
                    "{}".format(seprator.join(paths))) 

        
        k.email_send()
        flash('Download seccessfull!')
        return redirect(url_for('index'))
    return render_template('DownloadPdf.html', title='DownloadInovice', form=form,user=u)
    # except:
    #     flash('cant Download document')
    #     return redirect('/index')




@app.route('/Customer/DeletePdf', methods=['GET','POST'])
@login_required
def Delete_Pdf():
    u = User.objects(username=current_user.username).first()
    inovices = Inovice.objects(inovice_Customer = current_user.username)
    
    if request.method == 'POST':
        deletePDfList = request.form.getlist('checked')
        for d in deletePDfList:
            Deletepdf = Inovice.objects(Inovice_pdf = d ,inovice_Customer= current_user.username)
            Deletepdf.delete()
            s3 = boto3.resource('s3',
                                aws_access_key_id=access_key,
                                aws_secret_access_key=secret_key)
            s3.Object('pdfmergersce', d).delete()
            print('s')
        return redirect(url_for('Delete_Pdf'))
    return render_template('DeletePdf.html', title='DownloadInovice',user=u,inovices = inovices)


def checkinovice(Path,accountant,Customer):
    I = Inovice.objects(Inovice_pdf = Path, inovice_Accountant = accountant,inovice_Customer = Customer )
    if I:
        return False
    return True 
@app.route('/Customer/upload', methods=['POST', 'GET'])
@login_required
def upload():
    
    user = User.objects(username=current_user.username).first()
    form = uploadInovice()
    form.inovice_Accountant.choices = [(u.username, u.username) for u in User.objects.filter(role = 'ACCOUNTANT')]
    if request.method == 'POST' and not form.validate_on_submit():
        for key, f in request.files.items():
            if key.startswith('file'):
                f.save(os.path.join(app.config['UPLOADED_PATH'], f.filename))
                session['file'].append(os.path.join(app.config['UPLOADED_PATH'], f.filename))
        redirect ('/')
    if form.validate_on_submit():
        for file in session['file']:
            pdf = Inovice(inovice_Customer = current_user.username,inovice_Accountant = form.inovice_Accountant.data)
            pdf.Inovice_year = str(datetime.now().year)
            pdf.Inovice_month = str(datetime.now().month)
            s3 = boto3.resource('s3',
                                aws_access_key_id=access_key,
                                aws_secret_access_key=secret_key)
            for bucket in s3.buckets.all():
                if bucket.name == 'pdfmergersce':
                    res = bucket
            path = '{}/{}/{}/{}/{}'.format(pdf.inovice_Accountant,pdf.inovice_Customer,pdf.Inovice_year,pdf.Inovice_month,file.split('\\')[-1])
            res.upload_file(file,path)
            pdf.Inovice_pdf = path
            os.remove(file)
            pdf.save()
            session['file'] = []
    return render_template('test.html', user=user, form=form)


@app.route('/Customer/myProfile', methods=['POST', 'GET'])
@login_required
def myprofile():
    user = User.objects(username=current_user.username).first()
    return render_template('myProfile.html', title='myProfile', user=user)


if __name__ == '__main__':
    app.run()



