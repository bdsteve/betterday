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

# API Routes

class ActivityDetail(Resource):
    @jwt_required()
    def get(self, activity_id):
        activity = ScheduleActivity.query.get_or_404(activity_id)
        return {
            "id": activity.id,
            "title": activity.activity.title,
            "start_time": activity.start_time.strftime('%H:%M'),
            "duration": activity.duration,
            "recurrence": activity.recurrence
        }

class ScheduleActivityList(Resource):
    @jwt_required()
    def post(self, schedule_id):
        user_id = get_jwt_identity()
        schedule = Schedule.query.filter_by(id=schedule_id, user_id=user_id).first_or_404()

        data = request.form
        activity = Activity.query.get_or_404(data['activity_id'])

        user_tz = ZoneInfo(current_user.timezone)
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        local_dt = datetime.combine(schedule.start_date, start_time, tzinfo=user_tz)
        utc_dtstart = local_dt.astimezone(datetime.timezone.utc)

        new_activity = ScheduleActivity(
            schedule_id=schedule_id,
            activity_id=data['activity_id'],
            dtstart=utc_dtstart,
            start_time=start_time,
            duration=int(data['duration']),
            recurrence=data['recurrence']
        )
        db.session.add(new_activity)
        db.session.commit()

        create_activity_instances(new_activity)

        return {"message": "Activity added successfully", "id": new_activity.id}, 201

class ScheduleActivityDetail(Resource):
    @jwt_required()
    def put(self, schedule_id, activity_id):
        user_id = get_jwt_identity()
        schedule = Schedule.query.filter_by(id=schedule_id, user_id=user_id).first_or_404()
        activity = ScheduleActivity.query.get_or_404(activity_id)

        data = request.form
        changed_fields = []

        if 'start_time' in data:
            new_start_time = datetime.strptime(data['start_time'], '%H:%M').time()
            if activity.start_time != new_start_time:
                activity.start_time = new_start_time
                changed_fields.append('start_time')

        if 'duration' in data:
            new_duration = int(data['duration'])
            if activity.duration != new_duration:
                activity.duration = new_duration
                changed_fields.append('duration')

        if 'recurrence' in data:
            new_recurrence = data['recurrence']
            if activity.recurrence != new_recurrence:
                activity.recurrence = new_recurrence
                changed_fields.append('recurrence')

        if 'activity_id' in data:
            new_activity = Activity.query.get_or_404(data['activity_id'])
            if activity.activity_id != new_activity.id:
                activity.activity_id = new_activity.id
                changed_fields.append('activity_id')

        db.session.commit()

        if changed_fields:
            update_future_instances(activity, changed_fields)

        return {"message": "Activity updated successfully"}

    @jwt_required()
    def delete(self, schedule_id, activity_id):
        user_id = get_jwt_identity()
        schedule = Schedule.query.filter_by(id=schedule_id, user_id=user_id).first_or_404()
        activity = ScheduleActivity.query.get_or_404(activity_id)

        delete_future_instances(activity)
        db.session.delete(activity)
        db.session.commit()

        return {"message": "Activity deleted successfully"}


@main_bp.route('/edit_activity/<int:activity_id>', methods=['GET'])
@login_required
def edit_activity(activity_id):
    activity = ScheduleActivity.query.get_or_404(activity_id)
    return jsonify({
        "id": activity.id,
        "title": activity.activity.title,
        "start_time": activity.start_time.strftime('%H:%M'),
        "duration": activity.duration,
        "recurrence": activity.recurrence
    })

@main_bp.route('/update_activity/<int:schedule_id>/<int:activity_id>', methods=['POST'])
@login_required
def update_activity(schedule_id, activity_id):
    # Your logic to handle the update
    activity = ScheduleActivity.query.get_or_404(activity_id)
    # Update fields...
    db.session.commit()
    flash('Activity updated successfully!')
    return redirect(url_for('main.user_schedules'))

@main_bp.route('/delete_activity/<int:schedule_id>/<int:activity_id>', methods=['POST'])
@login_required
def delete_activity(schedule_id, activity_id):
    activity = ScheduleActivity.query.get_or_404(activity_id)
    db.session.delete(activity)
    db.session.commit()
    flash('Activity deleted successfully!')
    return redirect(url_for('main.user_schedules'))


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
    api.add_resource(ActivityDetail, '/api/activity/<int:activity_id>')
    api.add_resource(ScheduleActivityList, '/api/schedule/<int:schedule_id>/activity')
    api.add_resource(ScheduleActivityDetail, '/api/schedule/<int:schedule_id>/activity/<int:activity_id>')
