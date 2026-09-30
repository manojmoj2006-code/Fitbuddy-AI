"""Nutrition / recovery tips with Gemini Flash (fast and cheap)."""
from app import config
from app.gemini_client import generate_text


def generate_nutrition_tip_with_flash(goal: str, intensity: str = "medium") -> str:
    prompt = f"""You are a sports nutritionist.
Give ONE concise, practical nutrition or recovery tip for someone whose fitness goal is "{goal}"
and who trains at {intensity} intensity.
Maximum 2 sentences and 45 words. Plain text only, no markdown, no greeting."""
    return generate_text(config.FLASH_MODEL, prompt, temperature=0.6)
