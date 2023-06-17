import os
from datetime import datetime
import parking_editor as pked
import parking_detector as pkd
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, flash, session, url_for

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

class ParkingLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True, nullable=False)
    address = db.Column(db.String())
    image_path = db.Column(db.String())
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    posfile = db.Column(db.String, default="")
    source = db.Column(db.String, default="")
    created_on = db.Column(db.DateTime, default=datetime.now)

    def __str__(self):
        return f'{self.id}_{self.name}'

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/app.sqlite'
    app.config['SQLALCHEMY_ECHO'] = False
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'static/uploads/images'
    app.config['VIDEO_FOLDER'] = 'static/uploads/videos'
    app.secret_key = 'supersecretkeythatnooneknows'
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
    db.init_app(app)
    return app

app = create_app()

def create_login_session(user: User):
    session['id'] = user.id
    session['username'] = user.username
    session['email'] = user.email
    session['is_logged_in'] = True

def destroy_login_session():
    if 'is_logged_in' in session:
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
    if request.method == 'POST': #if form was submitted 
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
def parking_detection():
    data = db.session.query(ParkingLocation).all()
    return render_template('parking_system.html', locs=data)

@app.route('/detect/camera/<int:pid>')
def open_parking_window(pid):
    try:
        row = db.session.query(ParkingLocation).get(pid)
        print(f'{row.id}, {row.name}')
        if os.path.exists(row.posfile):
            pkd.detector(posfile=row.posfile, video=row.source)
            flash('No location setting found for this parking', 'warning')
    except Exception as e:
        print('error',e)
        flash(f"{e}", 'danger')

    return redirect('/detect')

@app.route('/edit/parking/<int:id>')
def parking_space_picker(id):
    try:
        row = db.session.query(ParkingLocation).get(id)
        parking_img = row.image_path
        parking=row.name
        w = row.width
        h = row.height
        pked.open_parking_image_window(parking_img, params=dict(parking=parking,w=w, h=h ))
        # save name in posfile columns
    except Exception as e:
        print(e)
        flash(f'{e}', 'danger')
    return redirect('/detect')


@app.route('/form', methods=['GET','POST'])
def form():
    if request.method=='POST':
        if 'camera_still' not in request.files:
            flash('No file part','danger')
            return redirect(request.url)
        name = request.form.get('name')
        addr = request.form.get('address')
        w = "0"
        h = "0"
        file = request.files['camera_still']
        source = request.files.get('camera_source')
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and name and addr and w and h:
            # try:
                filename = secure_filename(file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(path)
                if source: 
                    source_name = secure_filename(source.filename)
                    print( "source name", source_name) 
                    source_path = os.path.join(app.config['VIDEO_FOLDER'], source_name)
                    print("source path", source_path)
                    file.save(source_path)
                else:
                    source_path =  '0'
                    print("source path", source)
                parking = ParkingLocation(name=name, address=addr,image_path=path, width=int(w), height=int(h), posfile=name, source=source_path)
                db.session.add(parking)
                db.session.commit()
                flash("Parking information saved successfully")
                return redirect('/dashboard')
            # except Exception as e:
            #     flash(f"some error occurred {e}")
        else:
            flash("Some data missing")
    return render_template('form.html')
    
@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    data = db.session.query(ParkingLocation).all()
    return render_template('dashboard.html', locs=data)  

@app.route('/parking/delete/<int:pid>')
def delete_parking(pid):
    try:
        row = db.session.query(ParkingLocation).get(pid)
        if row:
            db.session.delete(row)
            db.session.commit()
            flash("record deleted")
    except:
        flash("Could not delete entry")
    return redirect('/dashboard')
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True) 