# app/routes.py

from flask import request, jsonify, render_template, flash, redirect, url_for, Blueprint, current_app, abort
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_login import login_user, login_required, logout_user, current_user
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.models import User, Schedule, Activity, ScheduleActivity, ActivityInstance
from app.forms import RegistrationForm, LoginForm, ScheduleActivityForm
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

@main_bp.route('/profile')
@login_required
def user_profile():
    db.session.refresh(current_user)
    return render_template('profile.html', user=current_user)

@main_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.landing'))

@main_bp.route('/logout', methods=['GET'])
def logout_get():
    abort(405)  # Method Not Allowed

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
        schedule_heading = f"{current_date.strftime('%A, %b %d')} Schedule"

    # Fetch schedule for the current user and date
    schedule = get_user_schedule(current_user.id, current_date, current_date, user_tz)

    # Sort activities by start time for each date
    for date, instances in schedule.items():
        schedule[date] = sorted(instances, key=lambda x: x.schedule_activity.start_time)

    # Correctly interpret `start_time` as a local time
    for date, instances in schedule.items():
        for instance in instances:
            # Interpret the `start_time` as a local time in the user's timezone
            local_time = instance.schedule_activity.start_time  # Naive `time` object representing local time
            # Combine date with local `start_time` and set to user's timezone
            instance_date_local = datetime.combine(instance.instance_date.date(), local_time).replace(tzinfo=user_tz)
            # Convert local time to UTC for display or further processing
            instance.instance_date_utc = instance_date_local.astimezone(timezone.utc)
            instance.instance_date_local = instance_date_local

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
            timezone=form.timezone.data,
            default_notifications=True
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

@main_bp.route('/update_default_notifications', methods=['POST'])
@login_required
def update_default_notifications():
    data = request.get_json()  # Retrieve JSON data from the request
    default_notifications = data.get('default_notifications', False)
    current_user.default_notifications = default_notifications
    db.session.commit()

    return jsonify({"success": True})

@main_bp.route('/doactivity/<int:instance_id>')
@login_required
def doactivity(instance_id):
    instance = ActivityInstance.query.get_or_404(instance_id)
    schedule_activity = instance.schedule_activity

    # Get user's timezone
    user_tz = ZoneInfo(current_user.timezone)

    # Calculate `instance_date_local` for display
    local_time = instance.instance_date.astimezone(user_tz)
    instance_date_local = local_time

    # Pass `instance_date_local` and `user` to the template
    return render_template(
        'doactivity.html',
        instance=instance,
        schedule_activity=schedule_activity,
        instance_date_local=instance_date_local,
        user=current_user  # Pass the current user
    )

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
    
    recurrence_rule = request.form['recurrence']  # Get the selected RRULE from the form

    new_activity = ScheduleActivity(
        schedule_id=request.form['schedule_id'],
        activity_id=request.form['activity_id'],
        dtstart=utc_dtstart,
        start_time=start_time,
        duration=int(request.form['duration']),
        recurrence=recurrence_rule  # Store the RRULE string in the recurrence field
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

@main_bp.route('/api/activities', methods=['GET'])
@login_required
def get_all_activities():
    activities = Activity.query.all()
    activities_data = [{
        "id": activity.id,
        "title": activity.title,
        "duration": activity.duration,
        "difficulty": activity.difficulty,
        "exertion": activity.exertion
    } for activity in activities]
    
    return jsonify(activities_data)

@main_bp.route('/add_activity_to_schedule', methods=['POST'])
@login_required
def add_activity_to_schedule():
    # Retrieve form data
    schedule_id = request.form.get('scheduleId')
    activity_id = request.form.get('activity_id')
    start_time_str = request.form.get('start_time')
    duration = request.form.get('duration')
    recurrence = request.form.get('recurrence')
    generate_notifications = 'generate_notifications' in request.form

    # Parse start_time
    start_time = datetime.strptime(start_time_str, '%H:%M').time()

    new_activity = ScheduleActivity(
        schedule_id=schedule_id,
        activity_id=activity_id,
        start_time=start_time,
        duration=int(duration),
        recurrence=recurrence,
        generate_notifications=generate_notifications,
        dtstart=datetime.now(timezone.utc)
    )
    db.session.add(new_activity)
    db.session.commit()
    create_activity_instances(new_activity)
    flash('Activity added successfully!', 'success')
    return redirect(url_for('main.user_schedules'))

@main_bp.route('/update_activity_notifications/<int:activity_id>', methods=['POST'])
@login_required
def update_activity_notifications(activity_id):
    data = request.json
    schedule_activity = ScheduleActivity.query.get_or_404(activity_id)
    
    if schedule_activity.schedule.user_id != current_user.id:
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    schedule_activity.generate_notifications = data.get('generate_notifications', False)
    db.session.commit()
    
    return jsonify({"success": True, "new_state": schedule_activity.generate_notifications})

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

@main_bp.route('/toggle_instance_notifications/<int:instance_id>', methods=['POST'])
@login_required
def toggle_instance_notifications(instance_id):
    data = request.json
    activity_instance = ActivityInstance.query.get_or_404(instance_id)
    
    if activity_instance.schedule_activity.schedule.user_id != current_user.id:
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    activity_instance.generate_notifications = data.get('generate_notifications', False)
    db.session.commit()
    
    return jsonify({"success": True})

@main_bp.route('/delete_activity/<int:schedule_id>/<int:activity_id>', methods=['POST'])
@login_required
def delete_activity(schedule_id, activity_id):
    try:
        activity = ScheduleActivity.query.filter_by(id=activity_id, schedule_id=schedule_id).first_or_404()
        
        # Ensure the activity belongs to a schedule owned by the current user
        if activity.schedule.user_id != current_user.id:
            return jsonify({"error": "You do not have permission to delete this activity."}), 403

        delete_future_instances(activity)
        db.session.delete(activity)
        db.session.commit()
        
        return jsonify({"message": "Activity deleted successfully"}), 200
    except Exception as e:
        current_app.logger.error(f"Error in delete_activity: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "An error occurred while deleting the activity"}), 500

@main_bp.route('/generate_instances', methods=['GET', 'POST'])
@login_required
def generate_instances():
    activities = ScheduleActivity.query.all()
    print(f"Total ScheduleActivities found: {len(activities)}")
    for activity in activities:
        print(f"Processing ScheduleActivity ID: {activity.id}")
        create_activity_instances(activity)
    
    flash('Activity instances generated for all scheduled activities!', 'success')
    return redirect(url_for('main.user_schedules'))

@main_bp.route('/edit_activity/<int:schedule_id>/<int:activity_id>', methods=['POST'])
@login_required
def edit_activity(schedule_id, activity_id):
    activity = ScheduleActivity.query.filter_by(id=activity_id, schedule_id=schedule_id).first_or_404()

    # Check if the current user owns the schedule
    if activity.schedule.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.user_schedules'))

    # Get form data
    start_time_str = request.form.get('start_time')
    duration = request.form.get('duration')
    recurrence = request.form.get('recurrence')
    generate_notifications = 'generate_notifications' in request.form

    # Parse start_time
    start_time = datetime.strptime(start_time_str, '%H:%M').time()

    activity.start_time = start_time
    activity.duration = int(duration)
    activity.recurrence = recurrence
    activity.generate_notifications = generate_notifications

    db.session.commit()
    create_activity_instances(activity)  # Regenerate instances
    flash('Activity updated successfully!', 'success')
    return redirect(url_for('main.user_schedules'))

@main_bp.route('/edit_activity/<int:schedule_id>/<int:activity_id>', methods=['GET'])
@login_required
def get_activity_details(schedule_id, activity_id):
    activity = ScheduleActivity.query.filter_by(id=activity_id, schedule_id=schedule_id).first_or_404()

    # Check if the current user owns the schedule
    if activity.schedule.user_id != current_user.id:
        return jsonify({"error": "Unauthorized access."}), 403

    return jsonify({
        "id": activity.id,
        "title": activity.activity.title,
        "start_time": activity.start_time.strftime('%H:%M'),
        "duration": activity.duration,
        "recurrence": activity.recurrence,
        "generate_notifications": activity.generate_notifications
    })

# app/routes.py end