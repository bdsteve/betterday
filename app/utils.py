from datetime import datetime, timezone, timedelta, time, date
from zoneinfo import ZoneInfo
from app.models import Schedule, ScheduleActivity, ActivityInstance
from app.extensions import db
from dateutil.rrule import rrulestr
from dateutil.parser import parse
from flask_login import current_user

def create_activity_instances(schedule_activity, end_date=None):
    user_tz = ZoneInfo(current_user.timezone)

    if end_date is None:
        end_date = datetime.now(user_tz) + timedelta(days=365)

    # Calculate the start of today in user's time zone
    today_local = datetime.now(user_tz).date()
    start_of_today_local = datetime.combine(today_local, time.min, tzinfo=user_tz)

    # Delete existing instances from start_of_today_local onwards, converted to UTC
    start_of_today_utc = start_of_today_local.astimezone(timezone.utc)
    deleted_rows = ActivityInstance.query.filter(
        ActivityInstance.schedule_activity_id == schedule_activity.id,
        ActivityInstance.instance_date >= start_of_today_utc
    ).delete(synchronize_session=False)
    db.session.commit()

    # Generate new instances starting from start_of_today_local
    dtstart_local = schedule_activity.dtstart.astimezone(user_tz)
    rrule = rrulestr(schedule_activity.recurrence, dtstart=dtstart_local)
    dates = rrule.between(start_of_today_local, end_date, inc=True)

    for date in dates:
        # Combine date from recurrence rule with start_time in user's local time
        instance_datetime_local = datetime.combine(date.date(), schedule_activity.start_time, tzinfo=user_tz)
        # Convert to UTC for storage
        instance_datetime_utc = instance_datetime_local.astimezone(timezone.utc)

        activity_instance = ActivityInstance(
            schedule_activity_id=schedule_activity.id,
            instance_date=instance_datetime_utc
        )
        db.session.add(activity_instance)
    db.session.commit()

def update_future_instances(schedule_activity, changed_fields):
    current_time = datetime.now(timezone.utc)
    future_instances = ActivityInstance.query.filter(
        ActivityInstance.schedule_activity_id == schedule_activity.id,
        ActivityInstance.instance_date > current_time
    ).all()

    for instance in future_instances:
        if 'start_time' in changed_fields:
            new_time = datetime.combine(instance.instance_date.date(), schedule_activity.start_time)
            instance.instance_date = new_time.replace(tzinfo=timezone.utc)
        
        # Add other field updates as necessary

    db.session.commit()

def delete_future_instances(schedule_activity):
    current_time = datetime.now(timezone.utc)
    ActivityInstance.query.filter(
        ActivityInstance.schedule_activity_id == schedule_activity.id,
        ActivityInstance.instance_date > current_time
    ).delete()
    db.session.commit()

from datetime import datetime, time
from zoneinfo import ZoneInfo

def get_user_schedule(user_id, start_date, end_date, user_tz):
    # Start and end of the day in user's local time
    start_datetime_local = datetime.combine(start_date, time.min, tzinfo=user_tz)
    end_datetime_local = datetime.combine(end_date, time.max, tzinfo=user_tz)

    # Convert to UTC for querying
    start_datetime_utc = start_datetime_local.astimezone(timezone.utc)
    end_datetime_utc = end_datetime_local.astimezone(timezone.utc)

    # Fetch instances within the UTC time range
    instances = db.session.query(ActivityInstance).join(
        ScheduleActivity, ActivityInstance.schedule_activity_id == ScheduleActivity.id
    ).join(
        Schedule, ScheduleActivity.schedule_id == Schedule.id
    ).filter(
        Schedule.user_id == user_id,
        ActivityInstance.instance_date >= start_datetime_utc,
        ActivityInstance.instance_date <= end_datetime_utc
    ).options(
        db.joinedload(ActivityInstance.schedule_activity).joinedload(ScheduleActivity.activity)
    ).all()

    # Group instances by date in user's local time
    schedule = {}
    for instance in instances:
        # Convert instance_date to user's local time zone
        instance_date_local = instance.instance_date.astimezone(user_tz).date()
        if instance_date_local not in schedule:
            schedule[instance_date_local] = []
        schedule[instance_date_local].append(instance)

    print(f"Schedule fetched for user {user_id} from {start_datetime_utc} to {end_datetime_utc}: {schedule}")
    return schedule

def convert_to_local_time(utc_time, local_tz):
    return utc_time.astimezone(local_tz)

def convert_to_utc(local_time, local_tz):
    local_dt = local_time.replace(tzinfo=local_tz)
    return local_dt.astimezone(timezone.utc)

def check_db_content(user_id, start_date, end_date):
    # Convert date objects to datetime objects with time set to midnight
    if isinstance(start_date, date) and not isinstance(start_date, datetime):
        start_date = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    if isinstance(end_date, date) and not isinstance(end_date, datetime):
        end_date = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
    
    # Ensure start_date and end_date are in UTC
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
    
    
    instances = db.session.query(ActivityInstance).join(ScheduleActivity, ActivityInstance.schedule_activity_id == ScheduleActivity.id).join(
        Schedule, ScheduleActivity.schedule_id == Schedule.id
    ).filter(
        Schedule.user_id == user_id,
        ActivityInstance.instance_date >= start_date,
        ActivityInstance.instance_date <= end_date
    ).all()
    
    print(f"Found {len(instances)} ActivityInstance records for user {user_id} from {start_date} to {end_date}")
    for instance in instances:
        print(f"Instance ID: {instance.id}, Date: {instance.instance_date}, Activity: {instance.schedule_activity.activity.title}")
