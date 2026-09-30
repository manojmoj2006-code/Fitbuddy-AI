"""SQLite persistence via SQLAlchemy. All helpers return plain dicts/strings, never ORM objects."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app import config

_connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(config.DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    age: Mapped[int] = mapped_column(Integer)
    weight: Mapped[float] = mapped_column(Float)
    goal: Mapped[str] = mapped_column(String(30))
    intensity: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), unique=True, index=True)
    original_plan: Mapped[str] = mapped_column(Text)
    updated_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nutrition_tip: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def _user_dict(u: User) -> dict:
    return {
        "user_id": u.user_id,
        "username": u.username,
        "age": u.age,
        "weight": u.weight,
        "goal": u.goal,
        "intensity": u.intensity,
        "created_at": u.created_at,
    }


def _plan_dict(p: Plan) -> dict:
    return {
        "user_id": p.user_id,
        "original_plan": p.original_plan,
        "updated_plan": p.updated_plan,
        "nutrition_tip": p.nutrition_tip,
        "feedback": p.feedback,
        "updated_at": p.updated_at,
    }


# ---------- users ----------
def save_user(user_id: str, username: str, age: int, weight: float, goal: str, intensity: str) -> dict:
    """Create the user, or update their details if the user_id already exists."""
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user is None:
            user = User(user_id=user_id)
            db.add(user)
        user.username, user.age, user.weight = username, age, weight
        user.goal, user.intensity = goal, intensity
        db.commit()
        return _user_dict(user)


def get_user(user_id: str) -> Optional[dict]:
    with SessionLocal() as db:
        user = db.get(User, user_id)
        return _user_dict(user) if user else None


def get_all_users() -> list[dict]:
    with SessionLocal() as db:
        users = db.scalars(select(User).order_by(User.created_at.desc())).all()
        return [_user_dict(u) for u in users]


def delete_user(user_id: str) -> bool:
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user is None:
            return False
        plan = db.scalar(select(Plan).where(Plan.user_id == user_id))
        if plan:
            db.delete(plan)
        db.delete(user)
        db.commit()
        return True


# ---------- plans ----------
def save_plan(user_id: str, original_plan: str, nutrition_tip: Optional[str] = None) -> dict:
    """Store a freshly generated plan. Regenerating for the same user resets any earlier update."""
    with SessionLocal() as db:
        plan = db.scalar(select(Plan).where(Plan.user_id == user_id))
        if plan is None:
            plan = Plan(user_id=user_id, original_plan=original_plan)
            db.add(plan)
        plan.original_plan = original_plan
        plan.updated_plan = None
        plan.feedback = None
        plan.nutrition_tip = nutrition_tip
        plan.updated_at = _now()
        db.commit()
        return _plan_dict(plan)


def update_plan(user_id: str, updated_plan: str, feedback: str, nutrition_tip: Optional[str] = None) -> Optional[dict]:
    """Save the feedback-based revision in its own column so the original is preserved."""
    with SessionLocal() as db:
        plan = db.scalar(select(Plan).where(Plan.user_id == user_id))
        if plan is None:
            return None
        plan.updated_plan = updated_plan
        plan.feedback = feedback
        if nutrition_tip:
            plan.nutrition_tip = nutrition_tip
        plan.updated_at = _now()
        db.commit()
        return _plan_dict(plan)


def get_plan(user_id: str) -> Optional[dict]:
    with SessionLocal() as db:
        plan = db.scalar(select(Plan).where(Plan.user_id == user_id))
        return _plan_dict(plan) if plan else None


def get_original_plan(user_id: str) -> Optional[str]:
    plan = get_plan(user_id)
    return plan["original_plan"] if plan else None


def get_all_plans() -> list[dict]:
    with SessionLocal() as db:
        return [_plan_dict(p) for p in db.scalars(select(Plan)).all()]
