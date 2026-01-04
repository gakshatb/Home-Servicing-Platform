import pandas as pd

import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')

import os
from flask import Flask 
from flask import render_template, request, url_for, redirect, session, flash, abort
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy


from config import app_config as ap


curr_dir=os.path.abspath(os.path.dirname(__file__))


#Creating a Flask instance
app=Flask(__name__, template_folder="templates")
app.secret_key= ap.APP_SECRET_KEY


#adding the database
# Use DATABASE_URL from environment (for Vercel Postgres) or fallback to SQLite
database_url = getattr(ap, 'DATABASE_URL', None) or os.getenv('DATABASE_URL', None)
if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(curr_dir, ap.database)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False


db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(30), nullable = False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    profile = db.Column(db.Boolean, default=False, nullable=False)
    street = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_professional = db.Column(db.Boolean, default=False, nullable=False)
    is_customer = db.Column(db.Boolean, default=False, nullable=False)
    description = db.Column(db.Text, nullable=False, default='No description provided')
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    experience = db.Column(db.String(3), nullable=False, default='0')
    # Relationships
    service_requests = db.relationship('ServiceRequest', back_populates='customer', foreign_keys='ServiceRequest.customer_id')
    professional_requests = db.relationship('ServiceRequest', back_populates='professional', foreign_keys='ServiceRequest.professional_id')

    def __repr__(self):
        return f"User(id={self.id}, username='{self.username}', name ='{self.name}', email='{self.email}', Phone='{self.phone}')"


class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ServiceType = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    status_service = db.Column(db.String(10), nullable=False, default='under_review') #under_review, approved, rejected
    time_required = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    professional_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Relationships
    service_requests = db.relationship('ServiceRequest', back_populates='service')

    def __repr__(self):
        return f"Service(id={self.id}, name='{self.name}', type ='{self.ServiceType}', price={self.price})"


class ServiceRequest(db.Model):
    __tablename__ = 'service_requests'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    service_status = db.Column(db.String(10), nullable=False, default='requested')  #requested, open, closed
    messages = db.Column(db.Text, nullable=True, default='No messages')
    date_of_request = db.Column(db.TIMESTAMP)
    date_of_completion = db.Column(db.TIMESTAMP)
    # Relationships
    feedback = db.relationship('Feedback', uselist=False, back_populates='service_request')
    service = db.relationship('Service', back_populates='service_requests')
    customer = db.relationship('User', back_populates='service_requests', foreign_keys=[customer_id])
    professional = db.relationship('User', back_populates='professional_requests', foreign_keys=[professional_id])

    def __repr__(self):
        return f"ServiceRequest(id={self.id}, service_id={self.service_id}, customer_id={self.customer_id}, professional_id={self.professional_id}, status='{self.service_status}')"

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_requests.id'), nullable=False, unique=True)
    rating = db.Column(db.Integer, nullable=False)  # Rating out of 5
    remarks = db.Column(db.Text)
    # Relationships
    service_request = db.relationship('ServiceRequest', back_populates='feedback')

    def __repr__(self):
        return f"Feedback(id={self.id}, service_request_id={self.service_request_id}, rating={self.rating})>"


#initialising database
db.init_app(app)

#creating database if not already exists
# Note: SQLite won't work on Vercel (read-only filesystem)
# You'll need to use Vercel Postgres or another database service
def init_db():
    """Initialize database tables. Safe for serverless environments."""
    try:
        with app.app_context():
            # Only check for SQLite file if not using DATABASE_URL
            database_url = getattr(ap, 'DATABASE_URL', None) or os.getenv('DATABASE_URL', None)
            if database_url:
                # Using Postgres or other external database
                # Just create tables - connection will be established on first query
                db.create_all()
            else:
                # Using SQLite (local development only)
                db_file_path = os.path.join(curr_dir, ap.database)
                if os.path.exists(db_file_path):
                    # Database exists, just ensure tables are created
                    db.create_all()
                else:
                    # Try to create database file (will fail on Vercel)
                    try:
                        db.create_all()
                    except (OSError, PermissionError) as e:
                        error_msg = f"SQLite not supported on Vercel. Error: {e}"
                        print(f"Warning: {error_msg}")
                        print("Note: Please set DATABASE_URL environment variable to use Vercel Postgres.")
                        # Don't raise - let the app start, DB operations will fail gracefully
    except Exception as e:
        # Log error but don't crash the app
        error_msg = f"Database initialization error: {e}"
        print(f"Warning: {error_msg}")
        # Check if it's a connection error
        if "DATABASE_URL" in str(e) or "connection" in str(e).lower():
            print("Note: Please check your DATABASE_URL environment variable in Vercel settings.")
        # Continue - app can start, DB operations will fail with clear errors


@app.route("/health")
def health():
    """Health check endpoint for Vercel"""
    try:
        # Test database connection
        db_status = "unknown"
        database_url = getattr(ap, 'DATABASE_URL', None) or os.getenv('DATABASE_URL', None)
        if database_url:
            try:
                with app.app_context():
                    db.engine.connect()
                    db_status = "connected"
            except Exception as e:
                db_status = f"error: {str(e)}"
        else:
            db_status = "sqlite (not configured for Vercel)"
        
        return {
            "status": "ok",
            "database": db_status,
            "database_url_set": bool(database_url)
        }, 200
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }, 500

@app.route("/")
def home():
    if request.method == 'GET':
        if 'user_id' in session:
            if session["is_admin"]:
                return redirect('/admin/dashboard')
            if session["is_customer"]:
                return redirect('/customer/dashboard')
            if session["is_professional"]:
                return redirect('/professional/dashboard')
            flash('Invalid user type')
            abort(404)
        return render_template('index.html')
    abort(404)


@app.route("/<user_type>/register", methods=['GET', 'POST'])
def register(user_type):
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        street = request.form.get('street')
        city = request.form.get('city')
        state = request.form.get('state')
        postal_code = request.form.get('postal_code')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        description = request.form.get('description')
        experience = request.form.get('experience')
        hashed_password = generate_password_hash(password, salt_length = 16)
        admincode = request.form.get('admincode')
        if user_type == 'admin':
            if admincode != ap.admin_code:
                flash('Admin Registration Code is incorrect.', 'danger')
                return render_template('register.html', user_type=user_type)

        user_name_exist = User.query.filter_by(username=username).first()
        if user_name_exist:
            flash('This username already exists. Please use other username.', 'danger')
            return render_template('register.html', user_type=user_type)

        email_exist = User.query.filter_by(email=email).first()
        if email_exist:
            flash('This email is already associated with another account.', 'danger')
            return render_template('register.html', user_type=user_type)
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html', user_type=user_type)
        
        phone_exist = User.query.filter_by(phone=phone).first()
        if phone_exist:
            flash('This phone number is already associated with another account.', 'danger')
            return render_template('register.html', user_type=user_type)
        
        user = User(name=name, username=username, email=email, phone=phone, street=street, city=city, state=state, postal_code=postal_code, password=hashed_password, description=description, experience=experience)

        if user_type == "professional":
            user.is_professional = True
        elif user_type == "customer":
            user.is_customer = True
        elif user_type == "admin":
            user.is_admin = True
        else:
            abort(404)
        
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    if request.method == 'GET':
        if 'user_id' in session:
            if session["is_admin"]:
                return redirect('/admin/dashboard')
            if session["is_customer"]:
                return redirect('/customer/dashboard')
            if session["is_professional"]:
                return redirect('/professional/dashboard')
            flash('Invalid user type')
            return redirect('customer/register')
        return render_template('register.html', user_type=user_type)
    abort(404)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'user_id' in session:
            if session["is_admin"]:
                return redirect('/admin/dashboard')
            if session["is_customer"]:
                return redirect('/customer/dashboard')
            if session["is_professional"]:
                return redirect('/professional/dashboard')
        return render_template('login.html')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['is_admin'] = user.is_admin
                session['is_customer'] = user.is_customer
                session['is_professional'] = user.is_professional
                flash('Login successful!', 'success')
                if user.is_admin:
                    return redirect('/admin/dashboard')
                if user.is_customer:
                    return redirect('/customer/dashboard')
                if user.is_professional:
                    return redirect('/professional/dashboard')
            flash('Login Unsuccessful. Incorrect password', 'danger')
            return redirect('/login')
        flash('Login Unsuccessful. Username Does Not Exist', 'danger')
        return redirect('/login')
    abort(404)



@app.route("/logout")
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)
    session.pop('is_customer', None)
    session.pop('is_professional', None)
    flash('You have been logged out.', 'success')
    return redirect('/')


@app.errorhandler(404)
def page_not_found(e):
    session.clear()
    return render_template('404.html'), 404


@app.route('/<user_type>/dashboard', methods=['GET', 'POST'])
def dashboard(user_type):
    if request.method == "GET":
        if 'user_id' in session:
            if user_type=="admin" and session["is_admin"]:
                admin = User.query.filter(User.id == session["user_id"]).first()
                service_to_approve = Service.query.filter(Service.status_service=='under_review').all()
                service_rejected = Service.query.filter(Service.status_service=='rejected').all()
                service_approved = Service.query.filter(Service.status_service=='approved').all()
                all_users = User.query.filter(User.id != session["user_id"] ).all()
                all_service = Service.query.all()
                all_ServiceRequest = ServiceRequest.query.join(Service).all()
                all_feedback = Feedback.query.all()
                return render_template(user_type + '_dashboard.html', admin = admin, service_to_approve=service_to_approve, service_rejected=service_rejected, service_approved=service_approved, all_users=all_users, all_service=all_service, all_ServiceRequest=all_ServiceRequest, all_feedback=all_feedback)
 
            if user_type=="customer" and session["is_customer"]:
                customer = User.query.filter(User.id == session["user_id"]).first()
                service_history = ServiceRequest.query.filter(ServiceRequest.customer_id == session["user_id"], ServiceRequest.service_status.in_(["rejected", "closed"])).all()
                service_accepted = ServiceRequest.query.filter(ServiceRequest.customer_id == session["user_id"], ServiceRequest.service_status=="accepted").all()
                service_requested = ServiceRequest.query.filter(ServiceRequest.customer_id == session["user_id"], ServiceRequest.service_status=="requested").all()
                active_services = Service.query.filter(Service.status_service == 'approved').all()
                user = User.query.all()
                return render_template(user_type + '_dashboard.html',customer = customer, service_history=service_history, service_accepted=service_accepted, active_services=active_services, service_requested=service_requested, user=user)

            if user_type=="professional" and session["is_professional"]:
                professional = User.query.filter(User.id == session["user_id"]).first()
                service_attending = ServiceRequest.query.filter(ServiceRequest.service_status == 'requested', ServiceRequest.professional_id == session["user_id"]).all()
                service_closed = ServiceRequest.query.filter(ServiceRequest.service_status == 'closed', ServiceRequest.professional_id == session["user_id"]).all()
                service_ongoing = ServiceRequest.query.filter(ServiceRequest.service_status == 'accepted', ServiceRequest.professional_id == session["user_id"]).all()
                service_rejected = ServiceRequest.query.filter(ServiceRequest.service_status == 'rejected', ServiceRequest.professional_id == session["user_id"]).all()
                return render_template(user_type + '_dashboard.html', professional = professional, service_attending=service_attending, service_closed=service_closed, service_ongoing=service_ongoing, service_rejected=service_rejected)
            flash('Invalid user', 'danger')
            return redirect('/login')
        flash('Please login first', 'danger')
        return redirect('/login')
    abort(404)

@app.route('/<user_type>/dashboard/<int:id>', methods=['GET', 'POST'])
def dashboard_action(user_type, id):
    if request.method == "POST":
        if user_type=="professional" and session["is_professional"]:
            action = request.form['action']
            if action == 'accept':
                service = ServiceRequest.query.filter(ServiceRequest.id == id).first()
                service.service_status = 'accepted'
                db.session.commit()
                flash('Service Accepted successfully!', 'success')
                return redirect('/professional/dashboard')
            if action == 'reject':
                service = ServiceRequest.query.filter(ServiceRequest.id == id).first()
                service.service_status = 'rejected'
                db.session.commit()
                flash('Service Rejected successfully!', 'success')
                return redirect('/professional/dashboard')
        if user_type=="customer" and session["is_customer"]:
            action = request.form['action']
            if action == 'delete':
                delete_service = ServiceRequest.query.filter(ServiceRequest.id == id).first()
                db.session.delete(delete_service)
                db.session.commit()
                flash('Request Deleted successfully!', 'success')
                return redirect('/customer/dashboard')
            if action == 'close':
                remark = request.form['remark']
                rating = request.form['rating']
                feedback = Feedback(service_request_id= id, remarks=remark, rating=rating)
                service = ServiceRequest.query.filter(ServiceRequest.id == id).first()
                service.service_status = 'closed'
                service.date_of_completion = datetime.now().replace(microsecond=0)
                db.session.add(feedback)
                db.session.commit()
                flash('Your Feedback submitted successfully!', 'success')
                return redirect('/customer/dashboard')
        if user_type=="admin" and session["is_admin"]:
            action = request.form.get('action')
            if action == 'delete':
                service = Service.query.filter(Service.id == id).first()
                service_requests = ServiceRequest.query.filter(ServiceRequest.service_id == id).all()
                for service_request in service_requests:
                    feedback = Feedback.query.filter(Feedback.service_request_id == service_request.id).first()
                    if feedback:
                        db.session.delete(feedback)
                    db.session.delete(service_request)
                db.session.delete(service)
                db.session.commit()
                flash('Service Deleted successfully!', 'success')
            if action == 'reject':
                service = Service.query.filter(Service.id == id).first()
                service.status_service = 'rejected'
                db.session.commit()
                flash('Service Rejected successfully!', 'success')
            if action == 'approve':
                service = Service.query.filter(Service.id == id).first()
                service.status_service = 'approved'
                db.session.commit()
                flash('Service Approved successfully!', 'success')
            if action == 'delete_user':
                user = User.query.filter(User.id == id).first()
                if user.is_customer:
                    service_requests = ServiceRequest.query.filter(ServiceRequest.customer_id == id).all()
                    for service_request in service_requests:
                        feedback = Feedback.query.filter(Feedback.service_request_id == service_request.id).all()
                        for feed in feedback:
                            db.session.delete(feed)
                        db.session.delete(service_request)
                if user.is_professional:
                    service_requests = ServiceRequest.query.filter(ServiceRequest.professional_id == id).all()
                    for service_request in service_requests:
                        feedback = Feedback.query.filter(Feedback.service_request_id == service_request.id).first()
                        for feed in feedback:
                            db.session.delete(feed)
                        db.session.delete(service_request)
                    services = Service.query.filter(Service.id == id).all()
                    for serv in services:
                        db.session.delete(serv)
                db.session.delete(user)
                db.session.commit()
                flash('User Deleted successfully!', 'success')
            return redirect(f"/{user_type}/dashboard")
    abort(404)


@app.route('/<user_type>/feedback/<int:service_id>', methods=['GET', 'POST'])
def feedback(user_type, service_id):
    if request.method == "GET":
        if 'user_id' in session:
            if user_type=="customer" and session["is_customer"]:
                customer = User.query.filter(User.id == session["user_id"]).first()
                requested_service = ServiceRequest.query.filter(ServiceRequest.id == service_id).first()
                service = Service.query.filter(Service.id == requested_service.service_id).first()
                return render_template('feedback.html', customer=customer, service=service, requested_service=requested_service)
            flash('Invalid user', 'danger')
            abort(404)
        flash('Please login first!', 'danger')
        return redirect('/login')
    abort(404)


@app.route('/<user_type>/create_request/<int:service_id>', methods=['GET', 'POST'])
def create_request(user_type, service_id):
    if request.method == "GET":
        if 'user_id' in session:
            if user_type=="customer" and session["is_customer"]:
                customer = User.query.filter(User.id == session["user_id"]).first()
                service = Service.query.filter(Service.id == service_id).first()
                return render_template('create_request.html', customer=customer, service=service, service_id=service_id)
            flash('Invalid user', 'danger')
            abort(404)
        flash('Please login first', 'danger')
        return redirect('/login')
    if request.method == "POST":
        message = request.form.get('message')
        service = Service.query.filter(Service.id == service_id).first()
        service_request = ServiceRequest(
            date_of_request=datetime.now().replace(microsecond=0),
            date_of_completion=(datetime.now() + timedelta(hours=service.time_required)).replace(microsecond=0),
            service_id=service_id,
            customer_id=session["user_id"],
            professional_id=service.professional_id,
            messages=message,
            service_status='requested')
        db.session.add(service_request)
        db.session.commit()
        return redirect('/customer/dashboard')        
    abort(404)


@app.route('/<user_type>/profile', methods=['GET', 'POST'])
def profile(user_type):
    if request.method == "GET":
        if 'user_id' in session:
            user = User.query.filter(User.id == session["user_id"]).first()
            if user_type=="customer" and session["is_customer"]:
                return render_template('user_profile.html', user=user, user_type=user_type)
            if user_type=="professional" and session["is_professional"]:
                return render_template('user_profile.html', user=user, user_type=user_type)
            if user_type=="admin" and session["is_admin"]:
                return render_template('user_profile.html', user=user, user_type=user_type)
            flash('Invalid user', 'danger')
            abort(404)
        flash('Please login first', 'danger')
        return redirect('/login')
    abort(404)


@app.route('/<user_type>/password_change', methods=['GET', 'POST'])
def password_change(user_type):
    if request.method == "GET":
        if 'user_id' in session:
            user = User.query.filter(User.id == session["user_id"]).first()
            if user_type=="customer" and session["is_customer"]:
                return render_template("change_password.html", user=user, user_type=user_type)
            if user_type=="professional" and session["is_professional"]:
                return render_template("change_password.html", user=user, user_type=user_type)
            if user_type=="admin" and session["is_admin"]:
                return render_template("change_password.html", user=user, user_type=user_type)
            flash('Invalid user', 'danger')
            abort(404)
        flash('Please login first', 'danger')
        return redirect('/login')
    abort(404)


@app.route('/<user_type>/editprofile', methods=['GET', 'POST'])
def editprofile(user_type):
    if request.method == "GET":
        if 'user_id' in session:
            user = User.query.filter(User.id == session["user_id"]).first()
            if user_type=="customer" and session["is_customer"]:
                return render_template("edit_profile.html", user=user, user_type=user_type)
            if user_type=="professional" and session["is_professional"]:
                return render_template("edit_profile.html", user=user, user_type=user_type)
            if user_type=="admin" and session["is_admin"]:
                return render_template("edit_profile.html", user=user, user_type=user_type)
            flash('Invalid user', 'danger')
            abort(404)
        flash('Please login first', 'danger')
        return redirect('/login')
    abort(404)


@app.route('/<user_type>/profile_action', methods=['GET', 'POST'])
def profile_action(user_type):
    if request.method == "POST":
        action = request.form['action']
        if action == 'delete':
            user = User.query.filter(User.id == session["user_id"]).first()
            if session["is_customer"]:
                service_requests = ServiceRequest.query.filter(ServiceRequest.customer_id == session["user_id"]).all()
                for service_request in service_requests:
                    feedbacks = Feedback.query.filter(Feedback.service_request_id == service_request.id).all()
                    for feedback in feedbacks:
                        db.session.delete(feedback)
                    db.session.delete(service_request)
            if session["is_professional"]:
                services = Service.query.filter(Service.professional_id == session["user_id"]).all()
                for service in services:
                    service_requests = ServiceRequest.query.filter(ServiceRequest.service_id == service.id).all()
                    for service_request in service_requests:
                        feedbacks = Feedback.query.filter(Feedback.service_request_id == service_request.id).all()
                        for feedback in feedbacks:
                            db.session.delete(feedback)
                        db.session.delete(service_request)
                    db.session.delete(service)
            db.session.delete(user)
            db.session.commit()
            session.pop('user_id', None)
            session.pop('is_admin', None)
            session.pop('is_customer', None)
            session.pop('is_professional', None)
            flash('Account Deleted successfully!', 'success')
            return redirect('/')
        if action == 'password':
            user = User.query.filter(User.id == session["user_id"]).first()
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            confirm_new_password = request.form.get('confirm_new_password')
            if new_password != confirm_new_password:
                flash('Passwords do not match.', 'danger')
                return render_template("change_password.html", user=user, user_type=user_type)
            if check_password_hash(user.password, old_password):
                user.password = generate_password_hash(new_password, salt_length = 16)
                db.session.commit()
                flash('Password Updated successfully!', 'success')
                return redirect('/logout')
            flash('Old password is incorrect.', 'danger')
            return render_template("change_password.html", user=user, user_type=user_type)
        if action == 'editprofile':
            user = User.query.filter(User.id == session["user_id"]).first()
            email = request.form.get('email')
            phone = request.form.get('phone')
            street = request.form.get('street')
            city = request.form.get('city')
            state = request.form.get('state')
            postal_code = request.form.get('postal_code')
            description = request.form.get('description')
            if email:
                temp = User.query.filter(User.email == email).first()
                if temp and temp.id != user.id:
                    flash('Email already exists.', 'danger')
                    return render_template("edit_profile.html", user=user, user_type=user_type)
                user.email = email
            if phone:
                temp = User.query.filter(User.phone == phone).first()
                if temp and temp.id != user.id:
                    flash('Phone number already exists.', 'danger')
                    return render_template("edit_profile.html", user=user, user_type=user_type)
                user.phone = phone
            if 'profile' in request.files:
                def allowed_file(filename):
                    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}
                profile = request.files['profile']
                if profile and profile.filename and allowed_file(profile.filename):
                    os.makedirs(f"{curr_dir}/static/profile", exist_ok=True)
                    profile.save(f"{curr_dir}/static/profile/{user.username}.jpg")
                    user.profile = True
            if street:
                user.street = street
            if city:
                user.city = city
            if state:
                user.state = state
            if postal_code:
                user.postal_code = postal_code
            if description:
                user.description = description
            db.session.commit()
            flash('Profile Updated successfully!', 'success')
            return redirect(f'/{user_type}/profile')
    abort(404)


@app.route('/<user_type>/myservices', methods=['GET', 'POST'])
def veiw_services(user_type):
    if request.method == "GET":
        if 'user_id' in session:
            if user_type == 'professional' and session["is_professional"]:
                user = User.query.filter(User.id == session["user_id"]).first()
                service = Service.query.filter(Service.professional_id == session["user_id"]).all()
                return render_template("view_service.html", user=user, user_type=user_type, service=service)
            flash('Invalid user', 'danger')
            abort(404)
        flash('Please login first', 'danger')
        return redirect('/login')
    if request.method == "POST":
        name = request.form.get('name')
        type = request.form.get('servicetype')
        description = request.form.get('description')
        price = request.form.get('price')
        time_required = request.form.get('time')
        service = Service(name=name, ServiceType=type, description=description, price=price, time_required=time_required, professional_id=session["user_id"])
        if user_type == 'professional':
            db.session.add(service)
            db.session.commit()
            flash('Service Added successfully!', 'success')
            return redirect(f"/{user_type}/myservices")
        if user_type == "admin":
            service.status_service = 'approved'
            db.session.add(service)
            db.session.commit()
            flash('Service Added successfully!', 'success')
            return redirect(f'/{user_type}/dashboard')
    abort(404)


@app.route('/<user_type>/addservice', methods=['GET', 'POST'])
def addservice(user_type):
    if request.method == "GET":
        if 'user_id' in session:
            user = User.query.filter(User.id == session["user_id"]).first()
            if user_type == 'professional' and session["is_professional"]:
                return render_template("add_service.html", user=user, user_type=user_type)
            if user_type == 'admin' and session["is_admin"]:
                return render_template("add_service.html", user=user, user_type=user_type)
            flash('Invalid user', 'danger')
            abort(404)
        flash('Please login first', 'danger')
        return redirect('/login')
    abort(404)


@app.route('/<user_type>/service_action/<int:service_id>', methods=['GET', 'POST'])
def service_action(user_type, service_id):
    if request.method == "POST":
        action = request.form.get('action')
        if action == 'delete':
            service = Service.query.filter(Service.id == service_id).first()
            db.session.delete(service)
            db.session.commit()
            flash('Service Deleted successfully!', 'success')
        if action == 'resubmit':
            service = Service.query.filter(Service.id == service_id).first()
            service.status_service = 'under_review'
            db.session.commit()
            flash('Service Resubmitted Successfully!', 'success')
        return redirect(f"/{user_type}/myservices")
    abort(404)


@app.route("/<user_type>/search", methods=["GET",'POST'])
def search(user_type):
    if request.method == 'POST':
        user = User.query.filter(User.id == session["user_id"]).first()
        query = request.form.get('query', default='')
        if user_type == 'customer' and session["is_customer"]:
            result1 = Service.query.filter(Service.status_service=='approved', Service.name.like(f'%{query}%')).all()
            result2 = Service.query.filter(Service.status_service=='approved', Service.ServiceType.like(f'%{query}%')).all()
            results = list({service.id: service for service in result1 + result2}.values())
            professionals = []
            for service in results:
                professional = User.query.filter(User.id == service.professional_id).first()
                if professional not in professionals:
                    professionals.append(professional)
            return render_template('search.html', user=user, user_type=user_type, query=query, results=results, professionals=professionals, zip=zip) 
        if user_type == 'professional' and session["is_professional"]:
            results = {'services': [],'customers': []}
            services = Service.query.filter( Service.professional_id == session["user_id"], (Service.name.ilike(f"%{query}%") | Service.description.ilike(f"%{query}%")) | Service.ServiceType.ilike(f"%{query}%") | Service.id.ilike(f"%{query}%") ).all()
            service_requests = ServiceRequest.query.filter(ServiceRequest.professional_id==session["user_id"]).join(User, ServiceRequest.customer_id == User.id).filter(User.name.ilike(f"%{query}%") | User.email.ilike(f"%{query}%")).all()
            results['services'] = services
            results['customers'] = service_requests
            return render_template('search.html', user=user, user_type=user_type, query=query, results=results)
        if user_type == 'admin' and session["is_admin"]:
            users = User.query.filter(
                (User.username.ilike(f"%{query}%")) |
                (User.id.ilike(f"%{query}%")) |
                (User.name.ilike(f"%{query}%")) |
                (User.phone.ilike(f"%{query}%")) |
                (User.email.ilike(f"%{query}%"))
            ).all()
            services = Service.query.filter(
                (Service.id.ilike(f"%{query}%")) |
                (Service.name.ilike(f"%{query}%")) |
                (Service.description.ilike(f"%{query}%")) |
                (Service.ServiceType.ilike(f"%{query}%"))
            ).all()
            requests = ServiceRequest.query.filter(
                (ServiceRequest.id.ilike(f"%{query}%")) |
                (ServiceRequest.messages.ilike(f"%{query}%")) |
                (ServiceRequest.service_status.ilike(f"%{query}%"))
            ).all()
            results = {'users': users, 'services': services, 'requests': requests}
            return render_template('search.html', user=user, user_type=user_type, results=results, query=query) 
        return redirect(f"/{user_type}/search")
    if request.method == 'GET':
        if 'user_id' in session:
            user = User.query.filter(User.id == session['user_id']).first()
            if user:
                if user_type == 'customer' and session["is_customer"]:
                    return render_template('search.html', user=user, user_type=user_type, query='')
                if user_type == 'professional' and session["is_professional"]:
                    return render_template('search.html', user=user, user_type=user_type, query='')
                if user_type == 'admin' and session["is_admin"]:
                    return render_template('search.html', user=user, user_type=user_type, query='')
                flash('Invalid user', 'danger')
            abort(404)
        flash('Please login first!', 'danger')
        return redirect('/login')
    abort(404)


def customer_summary(chart_dir):
    services_data = ServiceRequest.query.filter(ServiceRequest.customer_id == session["user_id"]).all()
    dataframe = pd.DataFrame([{
        'Service Name': req.service.name,
        'Category': req.service.ServiceType,
        'Price': req.service.price,
        'Status': req.service_status
    } for req in services_data])
    total_services = len(dataframe)
    total_spent = dataframe[dataframe['Status'] == 'closed']['Price'].sum() if 'Price' in dataframe else 0

    if dataframe.empty:
        # Chart 1: Total Services by Category - Empty Chart
        plt.figure(figsize=(14, 10))
        plt.text(0.5, 0.5, 'No Data Available', ha='center', va='center', fontsize=30, color='white', transform=plt.gca().transAxes)
        plt.xlabel('Service Category', color='white', fontsize=30)
        plt.ylabel('Number of Services', color='white', fontsize=30)
        plt.xticks([])
        plt.yticks(color='white')
        plt.savefig(os.path.join(chart_dir, 'customer_chart_1.png'), transparent=True)
        plt.close()
        # Chart 2: Service Status Distribution - Empty Chart
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, 'No Data Available', ha='center', va='center', fontsize=30, color='white', transform=plt.gca().transAxes)
        plt.savefig(os.path.join(chart_dir, 'customer_chart_2.png'), transparent=True)
        plt.close()
        # Chart 3: Spending on Closed Services - Empty Chart
        plt.figure(figsize=(14, 10))
        plt.text(0.5, 0.5, 'No Data Available', ha='center', va='center', fontsize=30, color='white', transform=plt.gca().transAxes)
        plt.xlabel('Service', color='white', fontsize=30)
        plt.ylabel('Amount Spent', color='white', fontsize=30)
        plt.xticks([])
        plt.yticks(color='white')
        plt.savefig(os.path.join(chart_dir, 'customer_chart_3.png'), transparent=True)
        plt.close()
    else:
        # Chart 1: Total Services by Category
        plt.figure(figsize=(14, 10))
        category_counts = dataframe['Category'].value_counts()
        bars = plt.bar(category_counts.index, category_counts.values, color='#66b3ff')
        plt.xlabel('Service Category', color='white', fontsize=30)
        plt.ylabel('Number of Services', color='white', fontsize=30)
        plt.yticks(color='white', fontsize=20)
        plt.xticks([])
        for bar, label in zip(bars, category_counts.index):
            plt.text(bar.get_x() + bar.get_width() / 2, 0.1, str(label), ha='center', va='bottom', rotation=90, fontsize=30, color='white')
        plt.savefig(os.path.join(chart_dir, 'customer_chart_1.png'), transparent=True)
        plt.close()
        # Chart 2: Service Status Distribution
        plt.figure(figsize=(8, 6))
        status_counts = dataframe['Status'].value_counts()
        plt.pie(status_counts, labels=status_counts.index,  autopct='%1.1f%%', startangle=140, colors=['#66b3ff', '#99ff99', '#ff9999', '#ffcc99'], shadow=True, textprops={'fontsize': 17})
        plt.savefig(os.path.join(chart_dir, 'customer_chart_2.png'), transparent=True)
        plt.close()
        # Chart 3: Spending on Closed Services
        plt.figure(figsize=(14, 10))
        closed_services = dataframe[dataframe['Status'] == 'closed']
        bars = plt.bar(closed_services.index, closed_services['Price'], color='#66b3ff')
        plt.xlabel('Service', color='white', fontsize=30)
        plt.ylabel('Amount Spent', color='white', fontsize=30)
        plt.yticks(color='white', fontsize=15)
        plt.xticks([])
        for bar, label in zip(bars, category_counts.index):
            plt.text(bar.get_x() + bar.get_width() / 2, 0.1, str(label), ha='center',va='bottom',rotation=90,fontsize=30,color='white')
        plt.savefig(os.path.join(chart_dir, 'customer_chart_3.png'), transparent=True)
        plt.close()
    return (total_services, total_spent)


def professional_summary(chart_dir):
    professional_id = session["user_id"]
    services_data = Service.query.filter(Service.professional_id == professional_id).all()
    requests_data = ServiceRequest.query.filter(ServiceRequest.professional_id == professional_id).all()
    feedback_data = (Feedback.query.join(ServiceRequest, Feedback.service_request_id == ServiceRequest.id).filter(ServiceRequest.professional_id == professional_id).all())

    services_df = pd.DataFrame([{
        'Service ID': service.id,
        'Name': service.name,
        'Category': service.ServiceType,
        'Price': service.price,
        'Status': service.status_service
    } for service in services_data])

    requests_df = pd.DataFrame([{
        'Request ID': request.id,
        'Service ID': request.service.id,
        'Customer ID': request.customer_id,
        'Status': request.service_status,
        'Date': request.date_of_request,
        'Price': request.service.price
    } for request in requests_data])

    feedback_df = pd.DataFrame([{
        'Service ID': feedback.id,
        'Rating': feedback.rating,
        'Comments': feedback.remarks
    } for feedback in feedback_data])

    total_services = services_df.shape[0]
    charts = []

    def generate_empty_chart(filename):
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, 'No Data Available', fontsize=20, ha='center', va='center', color='white')
        plt.axis('on')
        plt.grid(True)
        plt.savefig(os.path.join(chart_dir, filename), transparent=True)
        plt.close()

    # Chart 1: Service Requests Status Distribution
    if not requests_df.empty:
        plt.figure(figsize=(8, 6))
        status_counts = requests_df['Status'].value_counts()
        plt.pie(status_counts, labels=status_counts.index,  autopct='%1.1f%%', startangle=140, colors=['#66b3ff', '#99ff99', '#ff9999', '#ffcc99'], shadow=True, textprops={'fontsize': 17})
        plt.savefig(os.path.join(chart_dir, 'professional_chart_1.png'), transparent=True)
        plt.close()
    else:
        generate_empty_chart('professional_chart_1.png')
    charts.append('Service Requests Status')

    # Chart 2: Services by Category
    if not services_df.empty:
        plt.figure(figsize=(8, 6))
        category_counts = services_df['Category'].value_counts()
        bars = plt.bar(category_counts.index, category_counts.values, color='#66b3ff', edgecolor='white', alpha=0.7)
        plt.ylabel('Count', fontsize=20, color='white')
        plt.xlabel('Category', fontsize=20, color='white')
        plt.yticks(color='white', fontsize=17)
        plt.xticks([])
        for bar, label in zip(bars, category_counts.index):
            plt.text(bar.get_x() + bar.get_width() / 2, 0.1, str(label), ha='center', va='bottom', rotation=90, fontsize=17, color='white')
        plt.savefig(os.path.join(chart_dir, 'professional_chart_2.png'), transparent=True)
        plt.close()
    else:
        generate_empty_chart('professional_chart_2.png')
    charts.append('Services by Category')

    # Chart 3: Service Status Distribution
    if not services_df.empty:
        status_counts = services_df['Status'].value_counts()
        plt.figure(figsize=(8, 6))
        plt.pie(
            status_counts.values, 
            labels=status_counts.index, 
            autopct='%1.1f%%', 
            startangle=140, 
            colors=['#66b3ff', '#ff9999', '#99ff99', '#ffcc99'], 
            shadow=True, 
            textprops={'fontsize': 17}
        )
        plt.savefig(os.path.join(chart_dir, 'professional_chart_3.png'), transparent=True)
        plt.close()
    else:
        generate_empty_chart('professional_chart_3.png')
    charts.append('Service Status')

    # Chart 4: Revenue Analysis (Monthly)
    if not requests_df.empty:
        closed_requests = requests_df[requests_df['Status'] == 'closed']
        closed_requests['Month'] = pd.to_datetime(closed_requests['Date']).dt.to_period('M')
        revenue_by_month = closed_requests.groupby('Month')['Price'].sum()
        plt.figure(figsize=(8, 6))
        bars = plt.bar(revenue_by_month.index.astype(str), revenue_by_month.values, color='#66b3ff', edgecolor='white', alpha=0.7)
        plt.ylabel('Revenue (₹)', fontsize=20, color='white')
        plt.xlabel('Month', fontsize=20, color='white')
        plt.yticks(fontsize=17, color='white')
        plt.xticks([])
        plt.tight_layout()
        for bar, label in zip(bars, revenue_by_month.index.astype(str)):
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), label, ha='center', va='bottom', fontsize=17, color='white')
        plt.savefig(os.path.join(chart_dir, 'professional_chart_4.png'), transparent=True)
        plt.close()
    else:
        generate_empty_chart(os.path.join(chart_dir, 'professional_chart_4.png'))
    charts.append('Revenue Analysis (Monthly)')

    # Chart 5: Revenue Over Time
    if not requests_df.empty:
        total_services_completed = requests_df['Status'].value_counts()
        if 'closed' in total_services_completed:
            total_services_completed = total_services_completed['closed']
        else:
            total_services_completed = 0
        total_revenue = requests_df[requests_df['Status'] == 'closed']['Price'].sum()
        closed_requests_df = requests_df[requests_df['Status'] == 'closed']
        revenue_over_time = closed_requests_df.groupby(closed_requests_df['Date'].dt.to_period('M'))['Price'].sum()
        plt.figure(figsize=(8, 6))
        plt.plot(revenue_over_time.index.astype(str), revenue_over_time.values, marker='o', color='orange', linestyle='solid', linewidth=3)
        plt.ylabel('Revenue (₹)', color='white', fontsize=20)
        plt.xlabel('Date', color='white', fontsize=20)
        plt.yticks(color='white', fontsize=12)
        plt.xticks(color='white', fontsize=12)
        plt.text(0.95, 0.95, f'Total Revenue: {total_revenue}', transform=plt.gca().transAxes, fontsize=15, color='white', ha='right', va='top')
        plt.savefig(os.path.join(chart_dir, 'professional_chart_5.png'), transparent=True)
        plt.close()
    else:
        total_revenue = 0
        total_services_completed = 0
        generate_empty_chart('professional_chart_5.png')
    charts.append('Revenue Over Time')

    # Chart 6: Service Requests by Category
    if not services_df.empty and not requests_df.empty:
        merged_df = requests_df.merge(services_df, on='Service ID')
        category_counts = merged_df['Category'].value_counts()
        plt.figure(figsize=(8, 6))
        bars = plt.bar(category_counts.index, category_counts.values, color='#66b3ff', edgecolor='white', alpha=0.7)
        plt.xlabel('Category',  fontsize=20, color='white')
        plt.ylabel('Number of Requests',  fontsize=20, color='white')
        plt.xticks([])
        plt.yticks(color='white', fontsize=12)
        for bar, label in zip(bars, category_counts.index):
            plt.text(bar.get_x() + bar.get_width() / 2, 0.1, str(label), ha='center', va='bottom', rotation=90, fontsize=15, color='white')
        plt.savefig(os.path.join(chart_dir, 'professional_chart_6.png'), transparent=True)
        plt.close()
    else:
        generate_empty_chart('professional_chart_6.png')
    charts.append('Service Requests by Category')

    # Chart 7: Feedback Ratings Distribution
    if not feedback_df.empty:
        rating_counts = feedback_df['Rating'].value_counts().sort_index().reindex([1, 2, 3, 4, 5], fill_value=0)
        average_rating = feedback_df['Rating'].mean()
        plt.figure(figsize=(8, 6))
        plt.bar(rating_counts.index, rating_counts.values, color='lightgreen', edgecolor='white', alpha=0.7)
        plt.ylabel('Frequency', fontsize=20, color='white')
        plt.xlabel('Rating', fontsize=20, color='white')
        plt.yticks(color='white', fontsize=17)
        plt.xticks(color='white', fontsize=17)
        plt.text(0.95, 0.95, f'Avg. Rating: {average_rating:.2f}', transform=plt.gca().transAxes, fontsize=15, color='white', ha='right', va='top')
        plt.savefig(os.path.join(chart_dir, 'professional_chart_7.png'), transparent=True)
        plt.close()
    else:
        generate_empty_chart('professional_chart_7.png')
    charts.append('Feedback Ratings')

    # Chart 8: Top Services by Demand
    if not services_df.empty and not requests_df.empty:
        top_services = requests_df['Service ID'].value_counts().head(5)
        top_service_names = services_df.set_index('Service ID').loc[top_services.index]['Name']
        plt.figure(figsize=(8, 6))
        bars = plt.barh(top_service_names, top_services.values, color='#66b3ff', edgecolor='white', alpha=0.7)
        plt.xlabel('Number of Requests', fontsize=20, color='white')
        plt.ylabel('Service Name', fontsize=20, color='white')
        plt.yticks([])
        plt.xticks(fontsize=17, color='white')
        plt.gca().invert_yaxis()
        for bar, label in zip(bars, top_service_names):
            plt.text( 0.1, bar.get_y() + bar.get_height() / 2, label, ha='left', va='center', fontsize=17, color='white')
        plt.savefig(os.path.join(chart_dir, 'professional_chart_8.png'), transparent=True)
        plt.close()
    else:
        generate_empty_chart('professional_chart_8.png')
    charts.append('Top Services by Demand')

    # Chart 9: Requests Over Time
    if not requests_df.empty:
        requests_df['Date'] = pd.to_datetime(requests_df['Date'])
        requests_over_time = requests_df.groupby(requests_df['Date'].dt.to_period('M')).size()
        plt.figure(figsize=(8, 6))
        plt.plot(requests_over_time.index.astype(str), requests_over_time.values, color='orange', marker='o', linestyle='solid', linewidth=3)
        plt.xlabel('Date', color='white', fontsize=20)
        plt.ylabel('Number of Requests', color='white', fontsize=20)
        plt.xticks(color='white', fontsize=17)
        plt.yticks(color='white', fontsize=17)
        plt.savefig(os.path.join(chart_dir, 'professional_chart_9.png'), transparent=True)
        plt.close()
    else:
        generate_empty_chart('professional_chart_9.png')
    charts.append('Requests Over Time')

    return (total_services, total_revenue, total_services_completed,charts)


def admin_summary(chart_dir):
    # user_data = User.query.filter(User.id != session['user_id']).all()
    user_data = User.query.all()
    total_user = len(user_data)
    user_df = pd.DataFrame([{
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': (
            'Admin' if user.is_admin else 
            'Professional' if user.is_professional else 
            'Customer' if user.is_customer else 
            'Unknown'
        ),
        'created_at': user.created_at
    } for user in user_data])

    services_data = Service.query.all()
    total_services = sum(1 for service in services_data if service.status_service == 'approved')
    services_df = pd.DataFrame([{
        'id': service.id,
        'name': service.name,
        'Category': service.ServiceType,
        'price': service.price,
        'description': service.description,
        'status_service': service.status_service,
        'time_required': service.time_required,
        'created_at': service.created_at,
        'professional_id': service.professional_id
    } for service in services_data])

    services_req_data = ServiceRequest.query.all()
    total_request = len(services_req_data)
    service_requests_df = pd.DataFrame([{
        'id': req.id,
        'service_id': req.service_id,
        'customer_id': req.customer_id,
        'professional_id': req.professional_id,
        'service_status': req.service_status,
        'messages': req.messages,
        'date_of_request': req.date_of_request,
        'date_of_completion': req.date_of_completion
    } for req in services_req_data])

    feedback_data = Feedback.query.all()
    feedback_df = pd.DataFrame([{
        'id': feedback.id,
        'service_request_id': feedback.service_request_id,
        'rating': feedback.rating,
        'remarks': feedback.remarks
    } for feedback in feedback_data])


    charts = []

    def generate_empty_chart(filename):
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, 'No Data Available', fontsize=20, ha='center', va='center', color='white')
        plt.axis('on')
        plt.grid(True)
        plt.savefig(os.path.join(chart_dir, filename), transparent=True)
        plt.close()

    # Chart 1: Services by Category
    if not services_df.empty:
        category_counts = services_df['Category'].value_counts()
        bars = plt.bar(
            category_counts.index, 
            category_counts.values, 
            color='skyblue', 
            width=0.8, 
            edgecolor='white'
        )
        plt.ylabel('Number of Services', fontsize=15, color='white')
        plt.xlabel('Category', fontsize=15, color='white')
        plt.yticks(fontsize=15, color='white')
        plt.xticks([])
        for bar, label in zip(bars, category_counts.index):
            plt.text(bar.get_x() + bar.get_width() / 2, 0.1, str(label), ha='center', va='bottom', rotation=90, fontsize=10, color='white')
        plt.savefig(os.path.join(chart_dir, 'admin_chart_1.png'), transparent=True)
        plt.close()
    else:
        generate_empty_chart('admin_chart_1.png')
    charts.append('Services by Category')

    # Chart 2: Users by Role
    if not user_df.empty:
        role_counts = user_df['role'].value_counts()
        plt.pie(role_counts, labels=role_counts.index, autopct='%1.1f%%', startangle=140, colors=['#66b3ff', '#99ff99', '#ff9999', '#ffcc99'], shadow=True, textprops={'fontsize': 17})
        plt.savefig(os.path.join(chart_dir, 'admin_chart_2.png'), transparent=True)
        plt.close()
    else:
        generate_empty_chart('admin_chart_2.png')
    charts.append('Users by Role')

    # Chart 3: Feedback Ratings Distribution
    if not feedback_df.empty:
        rating_counts = feedback_df['rating'].value_counts().sort_index()
        plt.bar(
            rating_counts.index, 
            rating_counts.values, 
            color='lightgreen', 
            edgecolor='white'
        )
        plt.xlabel('Rating', fontsize=15, color='white')
        plt.ylabel('Number of Ratings', fontsize=15, color='white')
        plt.xticks(rating_counts.index, fontsize=15, color='white')
        plt.yticks(fontsize=15, color='white')
        plt.savefig(os.path.join(chart_dir, 'admin_chart_3.png'), transparent=True)
        plt.close()
    else:
        generate_empty_chart('admin_chart_3.png')
    charts.append('Feedback Ratings')

    # Chart 4: Service Requests Status
    if not service_requests_df.empty:
        status_counts = service_requests_df['service_status'].value_counts()
        plt.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%', startangle=140, colors=['#66b3ff', '#99ff99', '#ff9999', '#ffcc99'], shadow=True, textprops={'fontsize': 17})
        plt.savefig(os.path.join(chart_dir, 'admin_chart_4.png'), transparent=True)
        plt.close()
    else:
        generate_empty_chart('admin_chart_4.png')
    charts.append('Service Requests Status ')

    # Chart 5: Top Performing Categories
    if not service_requests_df.empty:
        requests_with_services = service_requests_df.merge(services_df, left_on='id', right_index=True)
        category_revenue = requests_with_services.groupby('Category')['price'].sum().sort_values(ascending=False)
        bars = plt.bar(
            category_revenue.index, 
            category_revenue.values, 
            color='#66b3ff', 
            edgecolor='white'
        )
        min_height = min([bar.get_height() for bar in bars])
        plt.xlabel('Category', fontsize=20, color='white')
        plt.ylabel('Revenue (₹)', fontsize=20, color='white')
        plt.yticks(fontsize=10, color='white')
        plt.xticks([])
        for bar, label in zip(bars, category_revenue.index):
            plt.text(bar.get_x() + bar.get_width() / 2, 0.1*min_height, str(label), ha='center', va='bottom', rotation=90, fontsize=15, color='white')
        plt.savefig(os.path.join(chart_dir, 'admin_chart_5.png'), transparent=True)
        plt.close()
    else:
        generate_empty_chart('admin_chart_5.png')
    charts.append('Top Performing Categories by Revenue')

    # Chart 6: Service Status Distribution
    if not services_df.empty:
        service_status_counts = services_df['status_service'].value_counts()
        plt.pie(service_status_counts, labels=service_status_counts.index, autopct='%1.1f%%', startangle=140, colors=['#66b3ff', '#ff9999', '#99ff99'], shadow=True, textprops={'fontsize': 17})
        plt.savefig(os.path.join(chart_dir, 'admin_chart_6.png'), transparent=True)
        plt.close()
    else:
        generate_empty_chart('admin_chart_6.png')
    charts.append('Service Status')

    # Chart 7: Professional Performance (Requests Completed)
    if not service_requests_df.empty:
        closed_requests_by_professional = service_requests_df[service_requests_df['service_status'] == 'closed'].groupby('professional_id').size()
        closed_requests_by_professional.plot(kind='bar', color='#99ff99', edgecolor='white')
        plt.xlabel('Professional ID', fontsize=15, color='white')
        plt.ylabel('Requests Completed', fontsize=15, color='white')
        plt.yticks(fontsize=15, color='white')
        plt.xticks(fontsize=10, color='white')
        plt.savefig(os.path.join(chart_dir, 'admin_chart_7.png'), transparent=True)
        plt.close()
    else:
        generate_empty_chart('admin_chart_7.png')
    charts.append('Professional Performance (Requests Completed)')

    # Chart 8: Average Feedback Rating Over Time
    if not feedback_df.empty:
        feedback_over_time = service_requests_df[['date_of_request']].join(feedback_df)
        feedback_over_time['Date'] = pd.to_datetime(feedback_over_time['date_of_request'])
        avg_rating_over_time = feedback_over_time.groupby(feedback_over_time['Date'].dt.to_period('M'))['rating'].mean()
        avg_rating_over_time.plot(kind='line', marker='o', color='orange')
        plt.xlabel('Month', fontsize=15, color='white')
        plt.ylabel('Average Rating', fontsize=20, color='white')
        plt.xticks([])
        plt.yticks(fontsize=10, color='white')
        plt.tight_layout()
        plt.savefig(os.path.join(chart_dir, 'admin_chart_8.png'), transparent=True)
        plt.close() 
    else:
        generate_empty_chart('admin_chart_8.png')
    charts.append('Average Feedback Rating Over Time')

    return (total_services, total_user, total_request, charts)


@app.route('/<user_type>/summary', methods=['GET', 'POST'])
def summary(user_type):
    if request.method == "GET":
        if 'user_id' in session:
            chart_dir = os.path.join(curr_dir, "static/summary")
            os.makedirs(chart_dir, exist_ok=True)
            user = User.query.filter(User.id == session["user_id"]).first()
            if user:
                if user_type == 'customer' and session["is_customer"]:
                    total_services, total_spent = customer_summary(chart_dir)
                    return render_template("summary.html",
                                           user=user,
                                           user_type=user_type,
                                           total_services=total_services,
                                           total_spent=total_spent)
                if user_type == 'professional' and session["is_professional"]:
                    total_services, total_revenue, total_services_completed, charts = professional_summary(chart_dir)
                    charts = zip(charts, range(1, len(charts) + 1))
                    return render_template("summary.html",
                                           user=user,
                                           user_type=user_type,
                                           total_services=total_services,
                                           total_revenue=total_revenue,
                                           total_services_completed = total_services_completed,
                                           charts=charts)
                if user_type == 'admin' and session["is_admin"]:
                    total_services, total_user, total_request, charts = admin_summary(chart_dir)
                    charts = zip(charts, range(1, len(charts) + 1))
                    return render_template("summary.html",
                                           user=user,
                                           user_type=user_type,
                                           total_services=total_services,
                                           total_user=total_user,
                                           total_request=total_request,
                                           charts=charts)
                flash('Invalid user', 'danger')
            abort(404)
        flash('Please login first!', 'danger')
        return redirect('/login')
    abort(404)


def add_admin():
    name_exist = User.query.filter_by(username=ap.admin_uname).first()
    email_exist = User.query.filter_by(email=ap.admin_email).first()
    phone_exist = User.query.filter_by(phone=ap.admin_phone).first()
    if not (name_exist or email_exist or phone_exist):
        admin = User(name=ap.admin_name, username=ap.admin_uname, email=ap.admin_email,
                    phone=ap.admin_phone, street=ap.admin_street, city=ap.admin_city,
                    state=ap.admin_state, postal_code=ap.admin_postal_code,
                    password=generate_password_hash(ap.admin_password, salt_length = 16), is_admin=True)
        db.session.add(admin)
        db.session.commit()


# Initialize admin only when running locally (not in serverless)
if __name__ == '__main__':
    # Initialize database tables first
    init_db()
    # Then create admin user within application context
    with app.app_context():
        add_admin()
    app.run(host='0.0.0.0',port=8000)
