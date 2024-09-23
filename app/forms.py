# app/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, IntegerField, TimeField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from app.models import User, Activity
from zoneinfo import ZoneInfo, available_timezones

def get_timezone_choices():
    return [(tz, tz) for tz in sorted(available_timezones())]

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    mobile = StringField('Mobile', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    timezone = SelectField('Timezone', choices=get_timezone_choices(), validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Please use a different email address.')

    def validate_mobile(self, mobile):
        user = User.query.filter_by(mobile=mobile.data).first()
        if user:
            raise ValidationError('Please use a different mobile number.')
        
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class ScheduleActivityForm(FlaskForm):
    activity_id = SelectField('Activity', coerce=int)
    start_time = TimeField('Start Time', validators=[DataRequired()])
    duration = IntegerField('Duration (minutes)', validators=[DataRequired()])
    recurrence = SelectField('Recurrence', choices=[
        ('RRULE:FREQ=DAILY', 'Every day'),
        ('RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR', 'Every weekday'),
        ('RRULE:FREQ=WEEKLY;BYDAY=SA,SU', 'Every weekend'),
        # Add more choices as needed
    ], validators=[DataRequired()])
    generate_notifications = BooleanField('Generate Notifications', default=True)

    def __init__(self, *args, **kwargs):
        super(ScheduleActivityForm, self).__init__(*args, **kwargs)
        self.activity_id.choices = [(activity.id, activity.title) for activity in Activity.query.all()]