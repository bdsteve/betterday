# run.py

from app.models import User, Type, UserType, UserProfile, Category, Activity, ActivityDeck, Schedule, ScheduleActivity, ActivityInstance, CoachClient, Notification
from dotenv import load_dotenv
import os

from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, port=port)
