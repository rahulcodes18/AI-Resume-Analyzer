import os
import uuid
import shutil

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

print("API KEY LOADED:", bool(os.getenv("GOOGLE_API_KEY")))

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from my_agent.agent import root_agent


app = FastAPI()

# Folder for uploaded resumes
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name="resume_analyzer_app",
    session_service=session_service,
)


@app.get("/")
def home():
    return {
        "message": "AI Resume Analyzer Backend is Running"
    }


@app.post("/run")
async def analyze_resume(
    resume: UploadFile = File(...),
    target_role: str = Form(...)
):

    try:
        # Only allow PDF
        if not resume.filename.lower().endswith(".pdf"):
            return {
                "status": "error",
                "message": "Please upload a PDF file only."
            }

        # Create unique filename
        unique_filename = f"{uuid.uuid4()}_{resume.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

        # Save uploaded PDF
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)

        user_id = "resume_user"
        session_id = str(uuid.uuid4())

        await session_service.create_session(
            app_name="resume_analyzer_app",
            user_id=user_id,
            session_id=session_id,
        )

        prompt = f"""
Analyze the uploaded resume located at:

{file_path}

Target Role:
{target_role}

First use the extract_resume_text tool to extract the resume.

Then analyze ONLY the information actually present in the resume.

Provide:

1. Resume Summary
2. Strongest Skills
3. Key Strengths
4. Weaknesses or Areas for Improvement
5. What Should Be Highlighted
6. Target Role Match
   - Strong Match
   - Partial Match
   - Relevant Gaps
7. Suitable Job Roles
8. Resume Improvement Suggestions

IMPORTANT:
- Do not invent skills, experience, projects, achievements, or metrics.
- Do not assume the candidate knows technologies not present.
- Do not give a large generic learning roadmap.
- Do not recommend random technologies.
- Focus on improving and presenting the existing resume.
- For the target role, mention only relevant gaps.
- Clearly separate "Found in Resume" from "Suggestions for Improvement".
- Keep the response practical and focused.

At the end ask:
"Would you like me to create an improved ATS-friendly version of this resume based only on the information already present?"
"""

        content = types.Content(
            role="user",
            parts=[types.Part(text=prompt)],
        )

        final_response = ""

        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            final_response += part.text

        if not final_response:
            return {
                "status": "error",
                "message": "Agent completed but returned no response."
            }

        return {
            "status": "success",
            "result": final_response
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }