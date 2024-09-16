# run.py

from app.models import User, Type, UserType, UserProfile, Category, Activity, ActivityDeck, Schedule, ScheduleActivity, ActivityInstance, CoachClient, Notification
from dotenv import load_dotenv
import os

print("Loading environment variables")
load_dotenv()  # Load environment variables from .env file

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("Starting Flask server")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port)
