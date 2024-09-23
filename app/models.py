# app/models.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, Date, Time, text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.associationproxy import association_proxy
from typing import List, Optional
from datetime import date, time, datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db
from zoneinfo import ZoneInfo

class Base(db.Model):
    __abstract__ = True

class User(Base, UserMixin):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_name: Mapped[str] = mapped_column(String(100))
    first_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(120), unique=True)
    mobile: Mapped[str] = mapped_column(String(20), unique=True)
    alt_email: Mapped[Optional[str]] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(512))
    subscription: Mapped[Optional[str]] = mapped_column(String(50))
    timezone: Mapped[str] = mapped_column(String(50), default='UTC')
    default_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default=text('true'))
    
    user_types: Mapped[List["UserType"]] = relationship(back_populates="user")
    types: Mapped[List["Type"]] = association_proxy("user_types", "type")
    profile: Mapped["UserProfile"] = relationship(back_populates="user", uselist=False)
    schedules: Mapped[List["Schedule"]] = relationship(back_populates="user")
    coach_clients: Mapped[List["CoachClient"]] = relationship(back_populates="coach", foreign_keys="[CoachClient.coach_id]")
    client_coaches: Mapped[List["CoachClient"]] = relationship(back_populates="client", foreign_keys="[CoachClient.client_id]")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)

class Type(Base):
    __tablename__ = "types"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(20))

class UserType(Base):
    __tablename__ = "user_types"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    type_id: Mapped[int] = mapped_column(ForeignKey("types.id"))
    
    user: Mapped["User"] = relationship(back_populates="user_types")
    type: Mapped["Type"] = relationship()

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    type_id: Mapped[int] = mapped_column(ForeignKey("types.id"))
    sex: Mapped[Optional[str]] = mapped_column(String(10))
    birthdate: Mapped[Optional[date]] = mapped_column(Date)
    goal: Mapped[Optional[str]] = mapped_column(Text)
    diagnosis: Mapped[Optional[str]] = mapped_column(Text)
    
    user: Mapped["User"] = relationship(back_populates="profile")

class Category(Base):
    __tablename__ = "categories"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    
    activities: Mapped[List["Activity"]] = relationship(back_populates="category")

class Activity(Base):
    __tablename__ = "activities"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    welcome: Mapped[Optional[str]] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(200))
    step: Mapped[int] = mapped_column(Integer)
    text: Mapped[Optional[str]] = mapped_column(Text)
    image: Mapped[Optional[str]] = mapped_column(String(200))
    audio: Mapped[Optional[str]] = mapped_column(String(200))
    video: Mapped[Optional[str]] = mapped_column(String(200))
    action: Mapped[Optional[str]] = mapped_column(String(20))
    duration: Mapped[int] = mapped_column(Integer)  # in minutes
    difficulty: Mapped[str] = mapped_column(String(20))
    exertion: Mapped[str] = mapped_column(String(20))
    
    category: Mapped["Category"] = relationship(back_populates="activities")
    activity_decks: Mapped[List["ActivityDeck"]] = relationship(back_populates="activity")

class ActivityDeck(Base):
    __tablename__ = "activity_decks"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"))
    level: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    
    activity: Mapped["Activity"] = relationship(back_populates="activity_decks")

class Schedule(Base):
    __tablename__ = "schedules"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(100))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    
    user: Mapped["User"] = relationship(back_populates="schedules")
    schedule_activities: Mapped[List["ScheduleActivity"]] = relationship(back_populates="schedule")

class ScheduleActivity(db.Model):
    __tablename__ = "schedule_activities"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    schedule_id: Mapped[int] = mapped_column(ForeignKey('schedules.id'), nullable=False)
    activity_id: Mapped[int] = mapped_column(ForeignKey('activities.id'), nullable=False)
    start_time: Mapped[datetime] = mapped_column(Time, nullable=False)
    dtstart: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # Store as UTC
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    recurrence: Mapped[str] = mapped_column(String, nullable=False)
    generate_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    schedule: Mapped["Schedule"] = relationship(back_populates="schedule_activities")
    activity: Mapped["Activity"] = relationship()
    instances: Mapped[List["ActivityInstance"]] = relationship(back_populates="schedule_activity", cascade="all, delete-orphan")

    @classmethod
    def get_default_notifications(cls, user_id):
        user = User.query.get(user_id)
        return user.default_notifications if user else True
    
    def __init__(self, **kwargs):
        super(ScheduleActivity, self).__init__(**kwargs)
        if 'generate_notifications' not in kwargs:
            self.generate_notifications = self.get_default_notifications(self.schedule.user_id)

class ActivityInstance(db.Model):
    __tablename__ = "activity_instances"
    __table_args__ = (
        db.UniqueConstraint('schedule_activity_id', 'instance_date', name='unique_activity_instance'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    schedule_activity_id: Mapped[int] = mapped_column(ForeignKey("schedule_activities.id"))
    instance_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    mood: Mapped[Optional[str]] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    generate_notifications: Mapped[bool] = mapped_column(Boolean, nullable=False)
    
    schedule_activity: Mapped["ScheduleActivity"] = relationship(back_populates="instances")

class CoachClient(Base):
    __tablename__ = "coach_clients"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coach_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    coach: Mapped["User"] = relationship(back_populates="coach_clients", foreign_keys=[coach_id])
    client: Mapped["User"] = relationship(foreign_keys=[client_id])

class Notification(Base):
    __tablename__ = "notifications"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    schedule_activity_id: Mapped[int] = mapped_column(ForeignKey("schedule_activities.id"))
    notification_time: Mapped[time] = mapped_column(Time)
    notification_type: Mapped[str] = mapped_column(String(20))  # SMS, email, or app notification
    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    
    user: Mapped["User"] = relationship()
    schedule_activity: Mapped["ScheduleActivity"] = relationship()