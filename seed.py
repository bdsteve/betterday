from app import create_app
from app.extensions import db
from app.models import (
    Type, UserType, UserProfile, Category, Activity, ActivityDeck,
    Schedule, ScheduleActivity, ActivityInstance, CoachClient, Notification, User
)
from datetime import date, time, datetime, timezone
from zoneinfo import ZoneInfo

# Initialize the app and application context
app = create_app()

with app.app_context():
    # Clear existing data
    db.session.query(UserType).delete()
    db.session.query(Type).delete()
    db.session.query(UserProfile).delete()
    db.session.query(CoachClient).delete()
    db.session.query(ActivityInstance).delete()
    db.session.query(Notification).delete()
    db.session.query(ScheduleActivity).delete()
    db.session.query(Schedule).delete()
    db.session.query(ActivityDeck).delete()
    db.session.query(Activity).delete()
    db.session.query(Category).delete()
    db.session.query(User).delete()
    db.session.commit()

    # Create Types
    types = [
        Type(type='coach'),
        Type(type='client'),
        Type(type='admin')
    ]
    db.session.add_all(types)
    db.session.commit()

    # Create Users
    users_data = [
        {
            'first_name': 'Steve',
            'last_name': 'Smith',
            'email': 'stevin.smith@gmail.com',
            'mobile': '8084649192',
            'password': 'bd2024!',
            'types': ['client'],
            'timezone': 'America/Los_Angeles'
        },
        {
            'first_name': 'Charles',
            'last_name': 'Smith',
            'email': 'stevin.smith@outlook.com',
            'mobile': '4802809815',
            'password': 'bd2024!',
            'types': ['coach'],
            'timezone': 'America/New_York'
        },
        {
            'first_name': 'Ada',
            'last_name': 'DeJesus',
            'email': 'ada@aol.com',
            'mobile': '2222222222',
            'password': 'db2024!',
            'types': ['client'],
            'timezone': 'America/New_York'
        },
        {
            'first_name': 'Admin',
            'last_name': 'User',
            'email': 'admin@voice4equity.com',
            'mobile': '3333333333',
            'password': 'db2024!',
            'types': ['admin'],
            'timezone': 'America/New_York'
        },
    ]

    users = []
    for user_data in users_data:
        user = User(
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            email=user_data['email'],
            mobile=user_data['mobile'],
            timezone=user_data['timezone']
        )
        user.set_password(user_data['password'])
        db.session.add(user)
        users.append(user)
    db.session.commit()

    # Debugging output
    print("Users created:", User.query.all())

    # Map emails to user instances
    user_dict = {user.email: user for user in users}

    # Assign Types to Users
    for user_data in users_data:
        user = user_dict.get(user_data['email'])
        if user:
            for type_name in user_data['types']:
                user_type = Type.query.filter_by(type=type_name).first()
                if user_type:
                    user_type_entry = UserType(user_id=user.id, type_id=user_type.id)
                    db.session.add(user_type_entry)
    db.session.commit()

    # Debugging output
    print("User types assigned:", UserType.query.all())

    # Create Categories
    categories = [
        Category(code='mindfulness', name='Mindfulness'),
        Category(code='exercise', name='Exercise'),
        Category(code='nutrition', name='Nutrition'),
        Category(code='fitness', name='Fitness')
    ]
    db.session.add_all(categories)
    db.session.commit()

    # Debugging output
    print("Categories created:", Category.query.all())

    # Map category codes to category instances
    category_dict = {category.code: category for category in categories}

    # Create Activities
    activities_data = [
        {'category': 'mindfulness', 'title': 'Mindfulness Meditation', 'duration': 15, 'difficulty': 'Easy', 'exertion': 'Low'},
        {'category': 'mindfulness', 'title': 'Gratitude Journaling', 'duration': 10, 'difficulty': 'Easy', 'exertion': 'Low'},
        {'category': 'exercise', 'title': 'Morning Jog', 'duration': 30, 'difficulty': 'Moderate', 'exertion': 'Medium'},
        {'category': 'exercise', 'title': 'Yoga Session', 'duration': 45, 'difficulty': 'Moderate', 'exertion': 'Medium'},
        {'category': 'nutrition', 'title': 'Salad Preparation', 'duration': 20, 'difficulty': 'Easy', 'exertion': 'Low'},
        {'category': 'nutrition', 'title': 'Water Intake Tracker', 'duration': 0, 'difficulty': 'Easy', 'exertion': 'Low'},
        {'category': 'fitness', 'title': 'Push-ups', 'duration': 10, 'difficulty': 'Moderate', 'exertion': 'Medium'},
        {'category': 'fitness', 'title': 'Sit-ups', 'duration': 10, 'difficulty': 'Moderate', 'exertion': 'Medium'},
        {'category': 'fitness', 'title': 'Squats', 'duration': 10, 'difficulty': 'Moderate', 'exertion': 'Medium'},
        {'category': 'fitness', 'title': 'Lunges', 'duration': 10, 'difficulty': 'Moderate', 'exertion': 'Medium'},
        {'category': 'fitness', 'title': 'Plank', 'duration': 5, 'difficulty': 'Hard', 'exertion': 'High'},
        {'category': 'fitness', 'title': 'Treadmill Intervals', 'duration': 20, 'difficulty': 'Hard', 'exertion': 'High'},
        {'category': 'mindfulness', 'title': 'Morning Stretch and Meditation', 'duration': 10, 'difficulty': 'Easy', 'exertion': 'Low'},
        {'category': 'nutrition', 'title': 'Breakfast', 'duration': 20, 'difficulty': 'Easy', 'exertion': 'Low'},
        {'category': 'nutrition', 'title': 'Water and Snack', 'duration': 10, 'difficulty': 'Easy', 'exertion': 'Low'},
        {'category': 'nutrition', 'title': 'Lunch', 'duration': 30, 'difficulty': 'Easy', 'exertion': 'Low'},
        {'category': 'mindfulness', 'title': 'Sleep Meditation', 'duration': 15, 'difficulty': 'Easy', 'exertion': 'Low'},
    ]

    activities = []
    for activity_data in activities_data:
        activity = Activity(
            category_id=category_dict[activity_data['category']].id,
            title=activity_data['title'],
            step=1,
            text=f"Description for {activity_data['title']}",
            duration=activity_data['duration'],
            difficulty=activity_data['difficulty'],
            exertion=activity_data['exertion']
        )
        db.session.add(activity)
        activities.append(activity)
    db.session.commit()

    # Debugging output
    print("Activities created:", Activity.query.all())

    # Create Schedules for 'stevin.smith@gmail.com'
    client = user_dict.get('stevin.smith@gmail.com')

    if client:
        schedule = Schedule(
            user_id=client.id,
            name='Steve\'s Fitness Routine',
            start_date=date.today(),
            end_date=None  # Ongoing schedule
        )
        db.session.add(schedule)
        db.session.commit()

        # Get the specific activities by title
        morning_stretch = next(activity for activity in activities if activity.title == 'Morning Stretch and Meditation')
        breakfast = next(activity for activity in activities if activity.title == 'Breakfast')
        water_snack = next(activity for activity in activities if activity.title == 'Water and Snack')
        lunch = next(activity for activity in activities if activity.title == 'Lunch')
        yoga = next(activity for activity in activities if activity.title == 'Yoga Session')
        sleep_meditation = next(activity for activity in activities if activity.title == 'Sleep Meditation')

        # Create ScheduleActivities
        pacific_tz = ZoneInfo(client.timezone)

        def local_to_utc(local_time):
            local_dt = datetime.combine(date.today(), local_time)
            local_dt = local_dt.replace(tzinfo=pacific_tz)
            return local_dt.astimezone(timezone.utc)

        # Add new activities to the schedule
        new_activities_data = [
            (time(6, 0), morning_stretch.id, 10, 'FREQ=DAILY'),
            (time(7, 0), breakfast.id, 20, 'FREQ=DAILY'),
            (time(10, 0), water_snack.id, 10, 'FREQ=DAILY'),
            (time(13, 30), lunch.id, 30, 'FREQ=DAILY'),
            (time(20, 0), yoga.id, 30, 'FREQ=DAILY'),
            (time(21, 30), sleep_meditation.id, 15, 'FREQ=DAILY'),
        ]

        schedule_activities = []
        for start_time, activity_id, duration, recurrence in new_activities_data:
            dtstart = local_to_utc(start_time)
            schedule_activities.append(
                ScheduleActivity(
                    schedule_id=schedule.id,
                    activity_id=activity_id,
                    dtstart=dtstart,
                    start_time=start_time,
                    duration=duration,
                    recurrence=recurrence
                )
            )

        db.session.add_all(schedule_activities)
        db.session.commit()
        print(f"Successfully added {len(schedule_activities)} scheduled activities.")

    print("Seed data added successfully.")
