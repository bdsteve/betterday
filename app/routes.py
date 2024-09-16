# app/routes.py

from flask import request, jsonify, render_template, flash, redirect, url_for, Blueprint
from flask_restful import Resource
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_login import login_user, login_required, logout_user, current_user
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.models import User, Schedule, Activity, ScheduleActivity, ActivityInstance
from app.forms import RegistrationForm, LoginForm
from app.extensions import db
from app.utils import get_user_schedule, convert_to_local_time, convert_to_utc, create_activity_instances, update_future_instances, delete_future_instances, check_db_content
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from datetime import timezone, time

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return render_template('landing.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(select(User).where(User.email == form.email.data)).scalar_one_or_none()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.home')
            return redirect(next_page)
        flash('Invalid email or password')
    return render_template('login.html', title='Sign In', form=form)

# In app/routes.py
@main_bp.route('/profile')
@login_required
def user_profile():
    return render_template('profile.html', user=current_user)

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.landing'))

@main_bp.route('/home')
@login_required
def home():
    date_str = request.args.get('date')
    user_tz = ZoneInfo(current_user.timezone)
    today = datetime.now(user_tz).date()

    try:
        current_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else today
    except ValueError:
        flash('Invalid date format. Showing today\'s schedule.')
        current_date = today

    if current_date == today:
        schedule_heading = "Today's Schedule"
    elif current_date == today + timedelta(days=1):
        schedule_heading = "Tomorrow's Schedule"
    else:
        schedule_heading = f"{current_date.strftime('%A, %B %d')}'s Schedule"

    # Fetch schedule for the current user and date
    schedule = get_user_schedule(current_user.id, current_date, current_date, user_tz)


    # No need to convert times here since it's already handled in get_user_schedule
    return render_template('home.html', user=current_user, schedule=schedule, current_date=current_date, schedule_heading=schedule_heading)

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            mobile=form.mobile.data,
            timezone=form.timezone.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

@main_bp.route('/doactivity/<int:instance_id>')
@login_required
def doactivity(instance_id):
    instance = ActivityInstance.query.get_or_404(instance_id)
    user_tz = ZoneInfo(current_user.timezone)
    instance_date_local = instance.instance_date.astimezone(user_tz)
    return render_template('doactivity.html', instance=instance, instance_date_local=instance_date_local, user=current_user)

@main_bp.route('/complete_activity/<int:instance_id>', methods=['POST'])
@login_required
def complete_activity(instance_id):
    instance = ActivityInstance.query.get_or_404(instance_id)
    instance.completed = True
    instance.completion_date = datetime.now(timezone.utc)
    db.session.commit()
    flash('Activity marked as completed!')
    return redirect(url_for('main.home'))

@main_bp.route('/schedules')
@login_required
def user_schedules():
    schedules = Schedule.query.filter_by(user_id=current_user.id).options(
        joinedload(Schedule.schedule_activities).joinedload(ScheduleActivity.activity)
    ).all()
    return render_template('schedules.html', schedules=schedules)

@main_bp.route('/add_activity', methods=['POST'])
@login_required
def add_activity():
    user_tz = ZoneInfo(current_user.timezone)
    
    # Get date and time from the form
    activity_date_str = request.form['date']  # Expecting 'YYYY-MM-DD'
    activity_date = datetime.strptime(activity_date_str, '%Y-%m-%d').date()
    
    start_time = time(hour=int(request.form['hour']), minute=int(request.form['minute']))
    
    # Combine date and time in user's timezone
    local_dt = datetime.combine(activity_date, start_time, tzinfo=user_tz)
    
    # Convert to UTC
    utc_dtstart = local_dt.astimezone(timezone.utc)
    
    new_activity = ScheduleActivity(
        schedule_id=request.form['schedule_id'],
        activity_id=request.form['activity_id'],
        dtstart=utc_dtstart,
        start_time=start_time,
        duration=int(request.form['duration']),
        recurrence=request.form['recurrence']
    )
    db.session.add(new_activity)
    db.session.commit()
    
    create_activity_instances(new_activity)
    
    flash('Activity added successfully!')
    return redirect(url_for('main.home'))

@main_bp.route('/create_activity', methods=['POST'])
@login_required
def create_activity():
    # This is the function for creating a new activity
    
    new_activity = Activity(
        schedule_id=request.form['schedule_id'],
        activity_id=request.form['activity_id'],
        dtstart=utc_time,
        start_time=start_time,
        duration=int(request.form['duration']),
        recurrence=request.form['recurrence']
    )
    db.session.add(new_activity)
    db.session.commit()
    
    flash('Activity successfully created!')
    return redirect(url_for('main.home'))

@main_bp.route('/update_activity/<int:activity_id>', methods=['POST'])
@login_required
def update_activity(activity_id):
    activity = ScheduleActivity.query.get_or_404(activity_id)
    changed_fields = []
    
    # Get new data from form
    new_start_time = time(hour=int(request.form['hour']), minute=int(request.form['minute']))
    if activity.start_time != new_start_time:
        activity.start_time = new_start_time
        changed_fields.append('start_time')
    
    new_recurrence = request.form['recurrence']
    if activity.recurrence != new_recurrence:
        activity.recurrence = new_recurrence
        changed_fields.append('recurrence')
    
    # Update dtstart if provided and changed
    activity_date_str = request.form.get('date')
    if activity_date_str:
        activity_date = datetime.strptime(activity_date_str, '%Y-%m-%d').date()
        user_tz = ZoneInfo(current_user.timezone)
        local_dt = datetime.combine(activity_date, new_start_time, tzinfo=user_tz)
        new_dtstart = local_dt.astimezone(timezone.utc)
        if activity.dtstart != new_dtstart:
            activity.dtstart = new_dtstart
            changed_fields.append('dtstart')
    
    db.session.commit()
    
    if 'start_time' in changed_fields or 'recurrence' in changed_fields or 'dtstart' in changed_fields:
        # Delete and regenerate future instances
        create_activity_instances(activity)
    
    flash('Activity updated successfully!')
    return redirect(url_for('main.home'))

@main_bp.route('/delete_activity/<int:activity_id>', methods=['POST'])
@login_required
def delete_activity(activity_id):
    activity = ScheduleActivity.query.get_or_404(activity_id)
    delete_future_instances(activity)
    db.session.delete(activity)
    db.session.commit()
    flash('Activity deleted successfully!')
    return redirect(url_for('main.home'))

@main_bp.route('/generate_instances', methods=['POST', 'GET'])
@login_required
def generate_instances():
    activities = ScheduleActivity.query.all()
    print(f"Total ScheduleActivities found: {len(activities)}")
    schedule_activity_ids = [activity.id for activity in activities]
    print(f"ScheduleActivity IDs: {schedule_activity_ids}")
    unique_ids = set(schedule_activity_ids)
    if len(unique_ids) != len(schedule_activity_ids):
        print("Duplicate ScheduleActivity IDs found!")
        # Optional: Remove duplicates
        activities = [activity for idx, activity in enumerate(activities) if schedule_activity_ids.index(activity.id) == idx]
    for activity in activities:
        print(f"Processing ScheduleActivity ID: {activity.id}")
        create_activity_instances(activity)
    
    flash('Activity instances generated for all scheduled activities!')
    return redirect(url_for('main.home'))

# API Routes
class UserRegistration(Resource):
    def post(self):
        data = request.get_json()
        if User.query.filter_by(email=data['email']).first():
            return {"message": "User already exists"}, 400
        new_user = User(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            mobile=data['mobile']
        )
        new_user.set_password(data['password'])
        db.session.add(new_user)
        db.session.commit()
        return {"message": "User created successfully"}, 201

class UserLogin(Resource):
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        if user and user.check_password(data['password']):
            access_token = create_access_token(identity=user.id)
            return {"access_token": access_token}, 200
        return {"message": "Invalid credentials"}, 401

class UserProfile(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        return {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "mobile": user.mobile
        }

class ScheduleList(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        schedules = Schedule.query.filter_by(user_id=user_id).all()
        return jsonify([{
            "id": s.id,
            "name": s.name,
            "start_date": s.start_date.isoformat(),
            "end_date": s.end_date.isoformat() if s.end_date else None
        } for s in schedules])
    
    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        data = request.get_json()
        new_schedule = Schedule(
            user_id=user_id,
            name=data['name'],
            start_date=data['start_date'],
            end_date=data.get('end_date')
        )
        db.session.add(new_schedule)
        db.session.commit()
        return {"message": "Schedule created successfully", "id": new_schedule.id}, 201

class ScheduleDetail(Resource):
    @jwt_required()
    def get(self, schedule_id):
        user_id = get_jwt_identity()
        schedule = Schedule.query.filter_by(id=schedule_id, user_id=user_id).first()
        if not schedule:
            return {"message": "Schedule not found"}, 404
        
        activities = ScheduleActivity.query.filter_by(schedule_id=schedule_id).all()
        return {
            "id": schedule.id,
            "name": schedule.name,
            "start_date": schedule.start_date.isoformat(),
            "end_date": schedule.end_date.isoformat() if schedule.end_date else None,
            "activities": [{
                "id": sa.id,
                "activity_id": sa.activity_id,
                "start_time": sa.start_time.isoformat(),
                "duration": sa.duration,
                "recurrence": sa.recurrence
            } for sa in activities]
        }

def init_api(api):
    api.add_resource(UserRegistration, '/api/register')
    api.add_resource(UserLogin, '/api/login')
    api.add_resource(UserProfile, '/api/profile')
    api.add_resource(ScheduleList, '/api/schedules')
    api.add_resource(ScheduleDetail, '/api/schedules/<int:schedule_id>')