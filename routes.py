"""All FitBuddy routes: form page, plan generation, feedback, admin view."""
import logging

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app import config, database
from app.gemini_client import GeminiError
from app.gemini_flash_generator import generate_nutrition_tip_with_flash
from app.gemini_generator import generate_workout_gemini
from app.schemas import GOALS, INTENSITIES, FeedbackRequest, UserInput
from app.updated_plan import update_workout_plan

logger = logging.getLogger("fitbuddy")
router = APIRouter()
templates = Jinja2Templates(directory=str(config.TEMPLATE_DIR))

TIP_FALLBACK = "Nutrition tip unavailable right now. Stay hydrated and eat protein with each meal."


def _index(request: Request, error: str | None = None, status_code: int = 200, form: dict | None = None):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"error": error, "goals": GOALS, "intensities": INTENSITIES, "form": form or {}},
        status_code=status_code,
    )


def _result(request: Request, user: dict, plan: dict, message: str | None = None, error: str | None = None,
            status_code: int = 200):
    current = plan["updated_plan"] or plan["original_plan"]
    return templates.TemplateResponse(
        request,
        "result.html",
        {
            "username": user["username"],
            "user_id": user["user_id"],
            "age": user["age"],
            "weight": user["weight"],
            "goal": user["goal"],
            "intensity": user["intensity"],
            "workout_plan": current,
            "original_plan": plan["original_plan"],
            "updated_plan": plan["updated_plan"],
            "nutrition_tip": plan["nutrition_tip"],
            "last_feedback": plan["feedback"],
            "message": message,
            "error": error,
        },
        status_code=status_code,
    )


def _friendly_error(exc: ValidationError) -> str:
    parts = []
    for err in exc.errors():
        field = ".".join(str(p) for p in err["loc"]) or "input"
        parts.append(f"{field}: {err['msg']}")
    return "Please check your input. " + "; ".join(parts)


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return _index(request)


@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout(
    request: Request,
    username: str = Form(...),
    user_id: str = Form(...),
    age: str = Form(...),
    weight: str = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
):
    form = {"username": username, "user_id": user_id, "age": age, "weight": weight,
            "goal": goal, "intensity": intensity}
    try:
        data = UserInput(username=username, user_id=user_id, age=age, weight=weight,
                         goal=goal, intensity=intensity)
    except ValidationError as exc:
        return _index(request, _friendly_error(exc), 422, form)

    try:
        workout_plan = generate_workout_gemini(data.age, data.weight, data.goal, data.intensity)
    except GeminiError as exc:
        logger.error("Workout generation failed: %s", exc)
        return _index(request, str(exc), 502, form)

    try:
        tip = generate_nutrition_tip_with_flash(data.goal, data.intensity)
    except GeminiError as exc:  # the tip is a bonus; do not lose the plan over it
        logger.warning("Nutrition tip failed: %s", exc)
        tip = TIP_FALLBACK

    user = database.save_user(data.user_id, data.username, data.age, data.weight, data.goal, data.intensity)
    plan = database.save_plan(data.user_id, workout_plan, tip)
    return _result(request, user, plan)


@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback(request: Request, user_id: str = Form(...), feedback: str = Form(...)):
    try:
        data = FeedbackRequest(user_id=user_id, feedback=feedback)
    except ValidationError as exc:
        user = database.get_user(user_id.strip())
        plan = database.get_plan(user_id.strip())
        if user and plan:
            return _result(request, user, plan, error=_friendly_error(exc), status_code=422)
        return _index(request, _friendly_error(exc), 422)

    user = database.get_user(data.user_id)
    plan = database.get_plan(data.user_id)
    if not user or not plan:
        return _index(request, f"No plan found for User ID '{data.user_id}'. Generate a plan first.", 404)

    # Build on the latest version so several rounds of feedback accumulate.
    base_plan = plan["updated_plan"] or plan["original_plan"]
    try:
        new_plan = update_workout_plan(base_plan, data.feedback, user["goal"], user["intensity"])
    except GeminiError as exc:
        logger.error("Plan update failed: %s", exc)
        return _result(request, user, plan, error=str(exc), status_code=502)

    try:
        tip = generate_nutrition_tip_with_flash(user["goal"], user["intensity"])
    except GeminiError as exc:
        logger.warning("Nutrition tip failed: %s", exc)
        tip = None  # keep the existing tip

    plan = database.update_plan(data.user_id, new_plan, data.feedback, tip)
    return _result(request, user, plan, message="Your workout plan was updated based on your feedback.")


@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request):
    plans = {p["user_id"]: p for p in database.get_all_plans()}
    users = [{**u, "plan": plans.get(u["user_id"])} for u in database.get_all_users()]
    return templates.TemplateResponse(request, "all_users.html", {"users": users})


@router.post("/delete-user/{user_id}")
def delete_user(user_id: str):
    database.delete_user(user_id)
    return RedirectResponse("/view-all-users", status_code=303)


@router.get("/health")
def health():
    return {"status": "ok"}
