"""Workout plan generation with Gemini Pro."""
from app import config
from app.gemini_client import generate_text


def generate_workout_gemini(age: int, weight: float, goal: str, intensity: str) -> str:
    prompt = f"""You are an experienced certified personal trainer.
Create a personalized 7-day workout plan for this person:
- Age: {age}
- Weight: {weight} kg
- Fitness goal: {goal}
- Preferred workout intensity: {intensity}

Requirements:
- Cover Day 1 through Day 7, one section per day, each starting with "Day N - Focus".
- Include at least one rest or active-recovery day (more rest days for low intensity).
- For every training day give: Warm-up (5-10 minutes), Main workout (exercise name, sets x reps or duration, rest time), and a Cooldown or recovery tip.
- Match volume and difficulty to the intensity and goal, and to the person's age.
- Plain text only. No markdown symbols such as #, * or tables. Use hyphen bullets.
- End with one line: "Note: check with a doctor before starting a new exercise program."
"""
    return generate_text(config.PRO_MODEL, prompt, temperature=0.7)
