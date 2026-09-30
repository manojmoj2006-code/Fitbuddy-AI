# FitBuddy - AI Fitness Plan Generator (Gemini)

FastAPI + SQLite + Jinja2 web app that uses Google Gemini to generate a personalized 7-day workout plan,
a nutrition/recovery tip, and feedback-based plan updates, with an admin page listing all users.

## Project structure

```
fitbuddy/
├── app/
│   ├── main.py                    # FastAPI app, static files, DB init
│   ├── routes.py                  # /, /generate-workout, /submit-feedback, /view-all-users
│   ├── config.py                  # env vars (.env), model names, paths
│   ├── database.py                # SQLAlchemy models + save_user/save_plan/update_plan/...
│   ├── schemas.py                 # UserInput, FeedbackRequest (Pydantic)
│   ├── gemini_client.py           # shared Gemini client + error handling
│   ├── gemini_generator.py        # generate_workout_gemini()  (Pro)
│   ├── gemini_flash_generator.py  # generate_nutrition_tip_with_flash()  (Flash)
│   ├── updated_plan.py            # update_workout_plan()  (Pro)
│   ├── templates/                 # base.html, index.html, result.html, all_users.html
│   └── static/images/             # optional gym-bg.jpg background
├── tests/test_app.py              # tests with Gemini mocked
├── .vscode/                       # interpreter, pytest and debug settings
├── requirements.txt / requirements-dev.txt
├── .env.example
└── pytest.ini
```

## 1. Prerequisites

- Python 3.10 or newer, and VS Code with the **Python** extension
- A free Gemini API key from https://aistudio.google.com/apikey

## 2. Setup in VS Code

1. Unzip the project, then **File > Open Folder...** and pick the `fitbuddy` folder.
2. Open the terminal: **Terminal > New Terminal**.
3. Create and activate a virtual environment:

   Windows (PowerShell):
   ```
   python -m venv venv
   venv\Scripts\Activate.ps1
   ```
   (If activation is blocked, run `Set-ExecutionPolicy -Scope Process RemoteSigned` first, or use `venv\Scripts\activate.bat` in cmd.)

   macOS / Linux:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Install dependencies:
   ```
   pip install -r requirements-dev.txt
   ```
   (Use `requirements.txt` instead if you don't want the test tools.)
5. In VS Code press `Ctrl+Shift+P` (`Cmd+Shift+P` on Mac), run **Python: Select Interpreter**, and choose the one inside `venv`.
6. Create your `.env` file:
   ```
   cp .env.example .env        # Windows: copy .env.example .env
   ```
   Open `.env` and replace `your_gemini_api_key_here` with your real key.

## 3. Run

```
uvicorn app.main:app --reload
```

- App: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- Admin page: http://127.0.0.1:8000/view-all-users

Or press **F5** in VS Code and choose **FitBuddy (uvicorn)** to run with the debugger.
The SQLite database (`fitbuddy.db`) is created automatically on first start.

## 4. Test

**Automated tests** (no API key or internet needed, Gemini is mocked):
```
pytest
```

**Manual test in the browser:**
1. Open http://127.0.0.1:8000, fill the form (for example: Name `Asha`, User ID `asha01`, Age `28`, Weight `62`, Goal `Weight Loss`, Intensity `Medium`) and click **Generate Plan**. Wait up to ~30 seconds. You should see the 7-day plan and a nutrition tip.
2. On the result page, enter feedback such as `include more rest days` and click **Update My Plan**. You should see a green confirmation and a revised plan; the original stays under "Show original plan".
3. Open **View all users**. You should see the user with original and updated plans, and a Delete button.

**Manual test of the API docs:** open `/docs`, expand `POST /generate-workout`, click **Try it out**, fill the fields, **Execute**.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | (required) | Your Gemini key (`GOOGLE_API_KEY` also works) |
| `GEMINI_PRO_MODEL` | `gemini-2.5-pro` | Model for workout plans and updates |
| `GEMINI_FLASH_MODEL` | `gemini-2.5-flash` | Model for nutrition tips |
| `DATABASE_URL` | `sqlite:///./fitbuddy.db` | Database location |

## Troubleshooting

- **"Gemini API key is missing"**: check that `.env` is in the project root (next to `requirements.txt`), then restart the server.
- **"Gemini request failed ... 404 / model not found"**: model names change over time. Set `GEMINI_PRO_MODEL` / `GEMINI_FLASH_MODEL` in `.env` to a model listed in Google AI Studio.
- **"Gemini request failed ... 429"**: free-tier rate limit; wait a minute or switch the Pro model to Flash in `.env`.
- **`ModuleNotFoundError: app`**: run commands from the project root folder, with the venv active.
- **Port already in use**: `uvicorn app.main:app --reload --port 8001`.
- To reset all data, stop the server and delete `fitbuddy.db`.

## Notes

- The admin page has no login, which is fine for local use. Add authentication before deploying it anywhere public.
- Generated plans are general guidance, not medical advice.
