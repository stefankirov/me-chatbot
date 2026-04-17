import json
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

def send_email(subject: str, body: str) -> bool:
    smtp_host = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    recipient = os.getenv("EMAIL_RECIPIENT")

    if not all([sender, password, recipient]):
        logger.warning(
            "Email not configured — skipped. Subject: %s | Body: %s", subject, body
        )
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())

        logger.info("Email sent: %s", subject)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Email authentication failed — check EMAIL_SENDER and EMAIL_PASSWORD.")
    except smtplib.SMTPException as e:
        logger.error("SMTP error: %s", e)
    except OSError as e:
        logger.error("Network error sending email: %s", e)
    return False


# ---------------------------------------------------------------------------
# Tool functions (called by the AI)
# ---------------------------------------------------------------------------

def record_user_details(email: str, name: str = "Name not provided", notes: str = "not provided"):
    logger.info("Recording user: name=%s email=%s", name, email)
    send_email("Chatbot: New visitor contact", f"Name: {name}\nEmail: {email}\nNotes: {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question: str):
    logger.info("Recording unknown question: %s", question)
    send_email("Chatbot: Unknown question", question)
    return {"recorded": "ok"}


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "record_user_details",
            "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "The email address of this user"},
                    "name": {"type": "string", "description": "The user's name, if they provided it"},
                    "notes": {"type": "string", "description": "Any additional context worth recording"},
                },
                "required": ["email"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_unknown_question",
            "description": "Always use this tool to record any question that couldn't be answered",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The question that couldn't be answered"},
                },
                "required": ["question"],
                "additionalProperties": False,
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Chatbot
# ---------------------------------------------------------------------------

class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "Stefan Kirov"
        self.profile = self._load_profile()

    def _load_profile(self) -> str:
        # Prefer inline env var (set in Azure App Service app settings for deployment)
        content = os.getenv("PROFILE_CONTENT", "").strip()
        if content:
            logger.info("Loaded profile from PROFILE_CONTENT env var.")
            return content

        profile_path = os.getenv("PROFILE_FILE", "profile.txt")
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                text = f.read().strip()
            logger.info("Loaded profile from %s", profile_path)
            return text
        except FileNotFoundError:
            logger.warning("Profile file '%s' not found. Copy profile.example.txt to profile.txt.", profile_path)
            return "(No profile loaded — see profile.example.txt)"
        except OSError as e:
            logger.error("Error reading profile file '%s': %s", profile_path, e)
            return "(Profile could not be loaded)"

    def _system_prompt(self) -> str:
        return (
            f"You are acting as {self.name}. You are answering questions on {self.name}'s personal website, "
            f"particularly questions related to {self.name}'s career, background, skills and experience. "
            f"Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. "
            f"Be professional and engaging, as if talking to a potential client or future employer. "
            f"If you don't know the answer to any question, use your record_unknown_question tool. "
            f"If the user is engaging in discussion, try to steer them towards getting in touch — ask for their email "
            f"and record it using your record_user_details tool.\n\n"
            f"## Profile:\n{self.profile}\n\n"
            f"With this context, please chat with the user, always staying in character as {self.name}."
        )

    def _handle_tool_calls(self, tool_calls) -> list:
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError as e:
                logger.error("Failed to parse tool arguments for %s: %s", tool_name, e)
                results.append({
                    "role": "tool",
                    "content": json.dumps({"error": "invalid arguments"}),
                    "tool_call_id": tool_call.id,
                })
                continue

            logger.info("Tool called: %s args: %s", tool_name, arguments)
            fn = globals().get(tool_name)
            if fn is None:
                logger.error("Unknown tool: %s", tool_name)
                result = {"error": f"unknown tool: {tool_name}"}
            else:
                try:
                    result = fn(**arguments)
                except Exception as e:
                    logger.error("Error in tool %s: %s", tool_name, e)
                    result = {"error": str(e)}

            results.append({
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id,
            })
        return results

    def chat(self, message: str, history: list) -> str:
        messages = [{"role": "system", "content": self._system_prompt()}] + history + [{"role": "user", "content": message}]
        max_iterations = 10

        for iteration in range(max_iterations):
            try:
                response = self.openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=TOOL_SCHEMAS,
                )
            except Exception as e:
                logger.error("OpenAI API error (iteration %d): %s", iteration + 1, e)
                return "I'm sorry, I couldn't connect to my AI backend right now. Please try again later."

            choice = response.choices[0]
            if choice.finish_reason == "tool_calls":
                tool_results = self._handle_tool_calls(choice.message.tool_calls)
                messages.append(choice.message)
                messages.extend(tool_results)
            else:
                content = choice.message.content
                if not content:
                    logger.warning("Empty response from OpenAI.")
                    return "I'm sorry, I didn't have a response for that. Could you rephrase?"
                return content

        logger.error("Exceeded max tool-call iterations (%d).", max_iterations)
        return "I'm sorry, something went wrong on my end. Please try again."


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

# Rate limiter — keyed by client IP
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Stefan Kirov — Personal Chatbot API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_me: Me | None = None
_api_key: str | None = None


@app.on_event("startup")
def startup():
    global _me, _api_key
    try:
        _me = Me()
        logger.info("Chatbot initialised successfully.")
    except Exception as e:
        logger.critical("Failed to initialise chatbot: %s", e)
        raise

    _api_key = os.getenv("CHATBOT_API_KEY", "").strip() or None
    if _api_key:
        logger.info("API key authentication is enabled.")
    else:
        logger.warning(
            "CHATBOT_API_KEY is not set — the /chat endpoint is open to anyone. "
            "Set this variable in production."
        )


def _verify_api_key(request: Request) -> None:
    """Raise 401 if CHATBOT_API_KEY is configured and the request doesn't supply it."""
    if _api_key is None:
        return  # no key configured → open (dev mode)
    provided = request.headers.get("X-API-Key", "")
    if provided != _api_key:
        logger.warning("Rejected request with invalid API key from %s", request.client.host)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key.")


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
@limiter.limit("30/minute")        # max 15 messages per minute per IP
def chat(request: Request, req: ChatRequest):
    _verify_api_key(request)
    try:
        response = _me.chat(req.message, req.history)
        return {"response": response}
    except Exception as e:
        logger.error("Unhandled error in /chat: %s", e)
        return {"response": "Something went wrong. Please try again."}
