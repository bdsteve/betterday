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
            'first_name': 'Christina',
            'last_name': 'Kishimoto',
            'email': 'kishimoto.christina@gmail.com',
            'mobile': '808-304-2801',
            'password': 'bd2024!',
            'types': ['client'],
            'timezone': 'America/Los_Angeles'
        },
        {
            'first_name': 'Admin',
            'last_name': 'User',
            'email': 'admin@voice4equity.com',
            'mobile': '8083042801',
            'password': 'bd2024!',
            'types': ['admin'],
            'timezone': 'America/Los_Angeles'
        },
        # New user Marta DeJesus
        {
            'first_name': 'Marta',
            'last_name': 'DeJesus',
            'email': 'cstevins@gmail.com',
            'mobile': '8081234567',
            'password': 'bd2024!',
            'types': ['client'],
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

    # Create Categories
    categories = [
        Category(code='mindfulness', name='Mindfulness'),
        Category(code='exercise', name='Exercise'),
        Category(code='nutrition', name='Nutrition'),
        Category(code='fitness', name='Fitness')
    ]
    db.session.add_all(categories)
    db.session.commit()

    # Map category codes to category instances
    category_dict = {category.code: category for category in categories}

    # Get the admin user
    admin_user = user_dict.get('admin@voice4equity.com')

    # Create Activities
    activities_data = [
        {'category': 'mindfulness', 'title': 'Mindfulness Meditation', 'duration': 15, 'difficulty': 'Easy', 'exertion': 'Low'},
        {'category': 'mindfulness', 'title': 'Gratitude Journaling', 'duration': 10, 'difficulty': 'Easy', 'exertion': 'Low'},
        {'category': 'exercise', 'title': 'Morning Jog', 'duration': 30, 'difficulty': 'Moderate', 'exertion': 'Medium'},
        {'category': 'exercise', 'title': 'Yoga Stretch', 'duration': 30, 'difficulty': 'Moderate', 'exertion': 'Medium'},
        {'category': 'nutrition', 'title': 'Salad Preparation', 'duration': 20, 'difficulty': 'Easy', 'exertion': 'Low'},
        {'category': 'nutrition', 'title': 'Water Intake Tracker', 'duration': 0, 'difficulty': 'Easy', 'exertion': 'Low'},
        {'category': 'fitness', 'title': 'Push-ups', 'duration': 10, 'difficulty': 'Moderate', 'exertion': 'Medium'},
        {'category': 'fitness', 'title': 'Pull-ups', 'duration': 10, 'difficulty': 'Moderate', 'exertion': 'High'},
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
        # Add for "Puerto Rican Dinner" with link to: https://www.discoverpuertorico.com/article/puerto-ricos-top-chefs-share-their-recipes
        # New activities for Marta's schedule
        {'category': 'exercise', 'title': 'Brisk Walk', 'duration': 30, 'difficulty': 'Moderate', 'exertion': 'Medium'},
        {'category': 'fitness', 'title': 'Strength Training (Upper Body)', 'duration': 20, 'difficulty': 'Moderate', 'exertion': 'Medium'},
        {'category': 'mindfulness', 'title': 'Yoga Session (Flexibility)', 'duration': 30, 'difficulty': 'Easy', 'exertion': 'Low'},
        {'category': 'mindfulness', 'title': 'Brain Games', 'duration': 20, 'difficulty': 'Easy', 'exertion': 'Low'},
        {'category': 'exercise', 'title': 'Stationary Cycling or Swimming', 'duration': 30, 'difficulty': 'Moderate', 'exertion': 'Medium'},
        {'category': 'mindfulness', 'title': 'Reading/Learning Activity', 'duration': 30, 'difficulty': 'Easy', 'exertion': 'Low'},
        {'category': 'fitness', 'title': 'Strength Training (Lower Body)', 'duration': 20, 'difficulty': 'Moderate', 'exertion': 'Medium'},
        {'category': 'exercise', 'title': 'Pilates or Tai Chi Class', 'duration': 30, 'difficulty': 'Moderate', 'exertion': 'Low'},
        {'category': 'mindfulness', 'title': 'Journal About the Week', 'duration': 15, 'difficulty': 'Easy', 'exertion': 'Low'},
        {'category': 'fitness', 'title': 'Strength Training (Full-Body)', 'duration': 20, 'difficulty': 'Moderate', 'exertion': 'Medium'},
        {'category': 'exercise', 'title': 'Hiking or Nature Walk', 'duration': 60, 'difficulty': 'Moderate', 'exertion': 'Medium'},
        {'category': 'nutrition', 'title': 'Meal Planning and Grocery Shopping', 'duration': 60, 'difficulty': 'Easy', 'exertion': 'Low'},
        {'category': 'mindfulness', 'title': 'Relaxation and Leisure Time', 'duration': 60, 'difficulty': 'Easy', 'exertion': 'Low'},
        {'category': 'mindfulness', 'title': 'Hobby Engagement', 'duration': 60, 'difficulty': 'Easy', 'exertion': 'Low'},
        {'category': 'mindfulness', 'title': 'Schedule Review and Goal Setting', 'duration': 30, 'difficulty': 'Easy', 'exertion': 'Low'},
        {'category': 'mindfulness', 'title': 'Morning Stretch Yoga', 'duration': 30, 'difficulty': 'Easy', 'exertion': 'Low'},
    ]

    activities = []
    for activity_data in activities_data:
        activity = Activity(
            owner_id=admin_user.id,
            access_level='public',
            is_system=True,
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

    # Map activity titles to activity instances
    activity_dict = {activity.title: activity for activity in activities}

    # Create Schedule for Steve
    client = user_dict.get('stevin.smith@gmail.com')

    if client:
        schedule = Schedule(
            owner_id=client.id,
            user_id=client.id,
            name='Steve\'s Fitness Routine',
            start_date=date.today(),
            end_date=None  # Ongoing schedule
        )
        db.session.add(schedule)
        db.session.commit()

        # Get the specific activities by title
        morning_stretch = activity_dict.get('Morning Stretch and Meditation')
        breakfast = activity_dict.get('Breakfast')
        water_snack = activity_dict.get('Water and Snack')
        lunch = activity_dict.get('Lunch')
        yoga = activity_dict.get('Yoga Stretch')
        sleep_meditation = activity_dict.get('Sleep Meditation')

        # Create ScheduleActivities
        client_tz = ZoneInfo(client.timezone)

        def local_to_utc(local_time):
            local_dt = datetime.combine(date.today(), local_time)
            local_dt = local_dt.replace(tzinfo=client_tz)
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
            schedule_activity = ScheduleActivity(
                schedule_id=schedule.id,
                activity_id=activity_id,
                dtstart=dtstart,
                start_time=start_time,
                duration=duration,
                recurrence=recurrence,
                generate_notifications=client.default_notifications
            )
            db.session.add(schedule_activity)
            schedule_activities.append(schedule_activity)

        db.session.commit()
        print(f"Successfully added {len(schedule_activities)} scheduled activities for Steve.")

    # Create Schedule for Marta DeJesus
    marta = user_dict.get('cstevins@gmail.com')

    if marta:
        marta_schedule = Schedule(
            owner_id=marta.id,
            user_id=marta.id,
            name='Marta\'s Wellness Routine',
            start_date=date.today(),
            end_date=None  # Ongoing schedule
        )
        db.session.add(marta_schedule)
        db.session.commit()

        # Map days to RRULE recurrence patterns
        day_to_rrule = {
            'Monday': 'FREQ=WEEKLY;BYDAY=MO',
            'Tuesday': 'FREQ=WEEKLY;BYDAY=TU',
            'Wednesday': 'FREQ=WEEKLY;BYDAY=WE',
            'Thursday': 'FREQ=WEEKLY;BYDAY=TH',
            'Friday': 'FREQ=WEEKLY;BYDAY=FR',
            'Saturday': 'FREQ=WEEKLY;BYDAY=SA',
            'Sunday': 'FREQ=WEEKLY;BYDAY=SU',
        }

        # List of tuples: (day, time, activity_title, duration)
        marta_activities_data = [
            # Monday
            ('Monday', time(7, 0), 'Brisk Walk', 30),
            ('Monday', time(14, 0), 'Mindfulness Meditation', 15),
            ('Monday', time(18, 0), 'Strength Training (Upper Body)', 20),
            # Tuesday
            ('Tuesday', time(7, 0), 'Yoga Session (Flexibility)', 30),
            ('Tuesday', time(14, 0), 'Brain Games', 20),
            ('Tuesday', time(18, 0), 'Stationary Cycling or Swimming', 30),
            # Wednesday
            ('Wednesday', time(7, 0), 'Brisk Walk', 30),
            ('Wednesday', time(14, 0), 'Reading/Learning Activity', 30),
            ('Wednesday', time(18, 0), 'Strength Training (Lower Body)', 20),
            # Thursday
            ('Thursday', time(7, 0), 'Morning Stretch Yoga', 30),
            ('Thursday', time(14, 0), 'Mindfulness Meditation', 15),
            ('Thursday', time(18, 0), 'Brisk Walk', 30),
            # Friday
            ('Friday', time(7, 0), 'Brisk Walk', 30),
            ('Friday', time(14, 0), 'Journal About the Week', 15),
            ('Friday', time(18, 0), 'Strength Training (Full-Body)', 20),
            # Saturday
            ('Saturday', time(8, 0), 'Hiking or Nature Walk', 60),
            ('Saturday', time(13, 0), 'Meal Planning and Grocery Shopping', 60),
            ('Saturday', time(19, 0), 'Relaxation and Leisure Time', 60),
            # Sunday
            ('Sunday', time(8, 0), 'Yoga Session (Flexibility)', 60),
            ('Sunday', time(14, 0), 'Hobby Engagement', 60),
            ('Sunday', time(18, 0), 'Schedule Review and Goal Setting', 30),
        ]

        marta_tz = ZoneInfo(marta.timezone)

        schedule_activities = []
        for day, start_time, activity_title, duration in marta_activities_data:
            activity = activity_dict.get(activity_title)
            if not activity:
                # If activity not found, create it
                new_activity_data = {
                    'category': 'mindfulness' if 'Yoga' in activity_title or 'Meditation' in activity_title else 'exercise',
                    'title': activity_title,
                    'duration': duration,  # Use provided duration
                    'difficulty': 'Easy',
                    'exertion': 'Low'
                }
                activity = Activity(
                    owner_id=admin_user.id,
                    access_level='public',
                    is_system=True,
                    category_id=category_dict[new_activity_data['category']].id,
                    title=new_activity_data['title'],
                    step=1,
                    text=f"Description for {new_activity_data['title']}",
                    duration=new_activity_data['duration'],
                    difficulty=new_activity_data['difficulty'],
                    exertion=new_activity_data['exertion']
                )
                db.session.add(activity)
                db.session.commit()
                activities.append(activity)
                activity_dict[activity.title] = activity
            dtstart = datetime.combine(date.today(), start_time)
            dtstart = dtstart.replace(tzinfo=marta_tz).astimezone(timezone.utc)
            recurrence = day_to_rrule[day]
            schedule_activity = ScheduleActivity(
                schedule_id=marta_schedule.id,
                activity_id=activity.id,
                dtstart=dtstart,
                start_time=start_time,
                duration=duration,
                recurrence=recurrence,
                generate_notifications=marta.default_notifications
            )
            db.session.add(schedule_activity)
            schedule_activities.append(schedule_activity)
        db.session.commit()
        print(f"Successfully added {len(schedule_activities)} scheduled activities for Marta.")

    print("Seed data added successfully.")
