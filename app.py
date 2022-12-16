from flask import Flask, render_template, request, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import parking_detector as pkd

db = SQLAlchemy()

'''
to create the project database, open terminal
- type python and press enter
- type 
    from app import app, db
    with app.app_context():
        db.create_all()
- enter twice to confirm
'''

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.now)

    def __str__(self):
        return f'{self.username}({self.id})'

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/app.sqlite'
    app.config['SQLALCHEMY_ECHO'] = True
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'supersecretkeythatnooneknows'
    db.init_app(app)
    return app

app = create_app()

def create_login_session(user: User):
    session['id'] = user.id
    session['username'] = user.username
    session['email'] = user.email
    session['is_logged_in'] = True

def destroy_login_session():
    if 'is_logged_in'in session:
        session.clear()    


@app.route('/')
def index():
    return render_template('index.html')

# froute
@app.route('/login',  methods=['GET','POST'])
def login():
    errors = {}
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        print("LOGGIN IN",email, password)
        if password and email:
            if len(email) < 11 or '@' not in email:
                errors['email'] = 'Email is Invalid'
            if len(errors) == 0:
                user = User.query.filter_by(email=email).first()
                if user is not None:
                    print("user account found", user)
                    if user.password == password:
                        create_login_session(user)
                        flash('Login Successfull', "success")
                        return redirect('/detect')
                    else:
                        errors['password'] = 'Password is invalid'
                else:
                    errors['email']= 'Account does not exists'
        else:
            errors['email'] = 'Please fill valid details'
            errors['password'] = 'Please fill valid details'
    return render_template('login.html', errors = errors)

@app.route('/register', methods=['GET','POST'])
def register():
    errors = []
    if request.method == 'POST': # if form was submitted
        username = request.form.get('username')
        email = request.form.get('email')
        pwd = request.form.get('password')
        cpwd = request.form.get('confirmpass')
        print(username, email, pwd, cpwd)
        if username and email and pwd and cpwd:
            if len(username)<2:
                errors.append("Username is too small")
            if len(email) < 11 or '@' not in email:
                errors.append("Email is invalid")
            if len(pwd) < 6:
                errors.append("Password should be 6 or more chars")
            if pwd != cpwd:
                errors.append("passwords do not match")
            if len(errors) == 0:
                user = User(username=username, email=email, password=pwd)
                db.session.add(user)
                db.session.commit()
                flash('user account created','success')
                return redirect('/login')
        else:
            errors.append('Fill all the fields')
            flash('user account could not be created','warning')
    return render_template('register.html', error_list=errors)

@app.route('/logout')
def logout():
    destroy_login_session()
    flash('You are logged out','success')
    return redirect('/')  

@app.route('/detect', methods=['GET','POST'])
def parking_detector():
    if request.method == 'POST':
        pkd.detector()
    return render_template('parking_system.html')  

@app.route('/generate', methods=['GET','POST'])
def create():
    if request.method == 'POST':
        pkd.generate()
    return render_template('create.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)