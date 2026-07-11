import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./paramatch.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class AthleteRow(Base):
    __tablename__ = "athletes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    height_cm = Column(Integer, nullable=False)
    arm_length_cm = Column(Integer, nullable=False)
    functional_arms = Column(Integer, nullable=False)


class TournamentRow(Base):
    __tablename__ = "tournaments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(String, nullable=True)
    athlete_ids = Column(Text, nullable=False, default="")
    published = Column(Boolean, nullable=False, default=False)
    current_round = Column(Integer, nullable=False, default=1)


class MatchRow(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, nullable=False)
    round = Column(Integer, nullable=False)
    athlete_a_id = Column(Integer, nullable=False)
    athlete_b_id = Column(Integer, nullable=True)
    ebae_score = Column(Integer, nullable=True)
    court = Column(Integer, nullable=True)
    date = Column(String, nullable=True)
    winner_id = Column(Integer, nullable=True)


class UserRow(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    athlete_id = Column(Integer, nullable=True)
    org_name = Column(String, nullable=True)


class TokenRow(Base):
    __tablename__ = "tokens"
    token = Column(String, primary_key=True)
    user_id = Column(Integer, nullable=False)


def init_db():
    Base.metadata.create_all(bind=engine)
