# tests/test_app.py

import pytest
from app.models import User, Schedule, Activity, ScheduleActivity
from flask import url_for
from werkzeug.security import generate_password_hash

def test_register(client, db):
    response = client.post('/register', data={
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'test@example.com',
        'mobile': '1234567890',
        'password': 'testpassword',
        'password2': 'testpassword',
        'timezone': 'UTC',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Congratulations, you are now a registered user!' in response.data
    user = User.query.filter_by(email='test@example.com').first()
    assert user is not None

def test_login_logout(client, db):
    # First, register a user
    user = User(
        first_name='Test',
        last_name='User',
        email='test@example.com',
        mobile='1234567890',
        timezone='UTC',
        password_hash=generate_password_hash('testpassword')
    )
    db.session.add(user)
    db.session.commit()

    # Login
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Hi Test!' in response.data

    # Logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in to access this page.' in response.data

def test_protected_route_requires_login(client):
    response = client.get('/home', follow_redirects=True)
    assert b'Please log in to access this page.' in response.data

def test_create_schedule(client, db, session):
    # Register and login a user
    user = User(
        first_name='Test',
        last_name='User',
        email='test@example.com',
        mobile='1234567890',
        timezone='UTC',
        password_hash=generate_password_hash('testpassword')
    )
    session.add(user)
    session.commit()

    # Login
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)

    # Create a schedule
    schedule = Schedule(
        user_id=user.id,
        name='Test Schedule',
        start_date='2023-01-01'
    )
    session.add(schedule)
    session.commit()

    # Verify schedule appears in user's schedules
    response = client.get('/schedules')
    assert b'Test Schedule' in response.data

def test_add_activity(client, db, session):
    # Set up user and login
    user = User(
        first_name='Test',
        last_name='User',
        email='test@example.com',
        mobile='1234567890',
        timezone='UTC',
        password_hash=generate_password_hash('testpassword')
    )
    session.add(user)
    session.commit()

    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)

    # Create a schedule and activity
    schedule = Schedule(
        user_id=user.id,
        name='Test Schedule',
        start_date='2023-01-01'
    )
    activity = Activity(
        category_id=1,  # Assuming a category with id=1 exists
        title='Test Activity',
        duration=30,
        difficulty='Easy',
        exertion='Low'
    )
    session.add(schedule)
    session.add(activity)
    session.commit()

    # Add activity to schedule
    response = client.post('/add_activity', data={
        'schedule_id': schedule.id,
        'activity_id': activity.id,
        'date': '2023-01-02',
        'hour': '10',
        'minute': '00',
        'duration': '30',
        'recurrence': 'FREQ=DAILY;COUNT=5'
    }, follow_redirects=True)
    assert b'Activity added successfully!' in response.data

    # Verify activity instances are created
    schedule_activity = ScheduleActivity.query.filter_by(schedule_id=schedule.id).first()
    assert schedule_activity is not None
    assert len(schedule_activity.instances) == 5

def test_api_user_registration(client, db):
    response = client.post('/api/register', json={
        'first_name': 'API',
        'last_name': 'User',
        'email': 'apiuser@example.com',
        'mobile': '0987654321',
        'password': 'apipassword'
    })
    assert response.status_code == 201
    assert response.get_json()['message'] == 'User created successfully'

def test_api_user_login(client, db):
    # Register user
    user = User(
        first_name='API',
        last_name='User',
        email='apiuser@example.com',
        mobile='0987654321',
        timezone='UTC',
        password_hash=generate_password_hash('apipassword')
    )
    db.session.add(user)
    db.session.commit()

    response = client.post('/api/login', json={
        'email': 'apiuser@example.com',
        'password': 'apipassword'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data

def test_api_user_profile(client, db):
    # Register and login user
    user = User(
        first_name='API',
        last_name='User',
        email='apiuser@example.com',
        mobile='0987654321',
        timezone='UTC',
        password_hash=generate_password_hash('apipassword')
    )
    db.session.add(user)
    db.session.commit()

    login_response = client.post('/api/login', json={
        'email': 'apiuser@example.com',
        'password': 'apipassword'
    })
    access_token = login_response.get_json()['access_token']

    # Access profile
    response = client.get('/api/profile', headers={
        'Authorization': f'Bearer {access_token}'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['email'] == 'apiuser@example.com'

def test_complete_activity(client, db, session):
    # Set up user, login, and create activity instance
    user = User(
        first_name='Test',
        last_name='User',
        email='test@example.com',
        mobile='1234567890',
        timezone='UTC',
        password_hash=generate_password_hash('testpassword')
    )
    session.add(user)
    session.commit()

    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)

    # Create schedule, activity, and schedule activity
    schedule = Schedule(
        user_id=user.id,
        name='Test Schedule',
        start_date='2023-01-01'
    )
    activity = Activity(
        category_id=1,  # Ensure this category exists
        title='Test Activity',
        duration=30,
        difficulty='Easy',
        exertion='Low'
    )
    session.add(schedule)
    session.add(activity)
    session.commit()

    schedule_activity = ScheduleActivity(
        schedule_id=schedule.id,
        activity_id=activity.id,
        start_time='10:00:00',
        dtstart='2023-01-02T10:00:00Z',
        duration=30,
        recurrence='FREQ=DAILY;COUNT=1'
    )
    session.add(schedule_activity)
    session.commit()

    # Create activity instance
    from datetime import datetime, timezone
    instance_date = datetime(2023, 1, 2, 10, 0, tzinfo=timezone.utc)
    activity_instance = schedule_activity.create_instances()[0]
    session.add(activity_instance)
    session.commit()

    # Complete activity
    response = client.post(f'/complete_activity/{activity_instance.id}', follow_redirects=True)
    assert b'Activity marked as completed!' in response.data
    assert activity_instance.completed is True

