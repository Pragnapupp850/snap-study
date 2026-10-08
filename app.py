
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import streamlit as st
from google import genai
from google.genai import types

from prompts import (
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
    SUMMARY_REQUEST_PROMPT,
)


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="Snap & Study",
    page_icon="📚",
    layout="centered",
)


# ---------------------------------------------------------
# SECRETS
# ---------------------------------------------------------

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
GMAIL_ADDRESS = st.secrets["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = st.secrets["GMAIL_APP_PASSWORD"]

MODEL_NAME = "gemini-3.8-flash"


# ---------------------------------------------------------
# GEMINI CLIENT
# ---------------------------------------------------------

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()


# ---------------------------------------------------------
# EMAIL
# ---------------------------------------------------------

def send_email(to_address, subject, body):
    """
    Send an email using Gmail SMTP.
    """

    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = GMAIL_ADDRESS
    message["To"] = to_address

    message.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(message)

        return True, "Email sent successfully."

    except Exception as error:
        return False, str(error)


# ---------------------------------------------------------
# MESSAGE DISPLAY
# ---------------------------------------------------------

def render_message(message):
    with st.chat_message(message["role"]):

        if message["kind"] == "text":
            st.write(message["content"])

        elif message["kind"] == "image":
            st.image(message["content"])


def add_message(role, kind, content):
    message = {
        "role": role,
        "kind": kind,
        "content": content,
    }

    st.session_state.messages.append(message)

    render_message(message)


# ---------------------------------------------------------
# GEMINI CHAT
# ---------------------------------------------------------

def create_chat():
    return gemini_client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        ),
    )


def ask_gemini(parts):
    import time

    last_error = None

    for attempt in range(3):
        try:
            response = st.session_state.chat.send_message(parts)
            return response.text

        except Exception as error:
            last_error = error

            if "503" in str(error) or "UNAVAILABLE" in str(error):
                if attempt < 2:
                    time.sleep(5)
                    continue

            break

    return (
        "Gemini is temporarily busy. "
        "Please try your question again in a moment."
    )


# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------

def create_summary():
    return ask_gemini([SUMMARY_REQUEST_PROMPT])


# ---------------------------------------------------------
# ONBOARDING
# ---------------------------------------------------------

if "onboarded" not in st.session_state:

    st.title("📚 Snap & Study")

    st.caption(
        "Snap it. Understand it. Study smarter."
    )

    st.write(
        "Upload a question, diagram, textbook page, "
        "worksheet, or your notes and I'll explain it "
        "in simple language."
    )

    with st.form("onboarding_form"):

        name = st.text_input(
            "Your name",
            placeholder="Enter your name",
        )

        email = st.text_input(
            "Your email address",
            placeholder="you@example.com",
        )

        submitted = st.form_submit_button(
            "Let's Study 🚀",
            use_container_width=True,
        )

        if submitted:

            if not name.strip() or not email.strip():

                st.warning(
                    "Please enter both your name and email."
                )

            else:

                st.session_state.name = name.strip()
                st.session_state.email = email.strip()

                st.session_state.chat = create_chat()

                st.session_state.messages = []

                st.session_state.onboarded = True

                st.rerun()

    st.stop()


# ---------------------------------------------------------
# MAIN HEADER
# ---------------------------------------------------------

header_col, button_col = st.columns(
    [5, 2],
    vertical_alignment="center",
)


with header_col:

    st.title("📚 Snap & Study")

    st.caption(
        f"Studying with {st.session_state.name}"
    )


with button_col:

    send_disabled = (
        len(st.session_state.messages) <= 1
    )

    if st.button(
        "📧 Email My Explanation",
        disabled=send_disabled,
        use_container_width=True,
    ):

        with st.spinner("Preparing your study summary..."):

            summary = create_summary()

        with st.spinner("Sending your email..."):

            success, info = send_email(
                st.session_state.email,
                "📚 Your Snap & Study Revision Summary",
                summary,
            )

        if success:

            st.success(
                "Sent! Check your email 📧"
            )

        else:

            st.error(
                f"Couldn't send the email: {info}"
            )


st.divider()


# ---------------------------------------------------------
# CHAT HISTORY
# ---------------------------------------------------------

if not st.session_state.messages:

    add_message(
        "assistant",
        "text",
        WELCOME_MESSAGE_TEMPLATE.format(
            name=st.session_state.name
        ),
    )

else:

    for message in st.session_state.messages:

        render_message(message)


# ---------------------------------------------------------
# CHAT INPUT
# ---------------------------------------------------------

user_input = st.chat_input(
    "Ask a question or attach a study image...",
    accept_file=True,
    file_type=[
        "jpg",
        "jpeg",
        "png",
        "webp",
    ],
)


# ---------------------------------------------------------
# PROCESS USER INPUT
# ---------------------------------------------------------

if user_input:

    photo = (
        user_input.files[0]
        if user_input.files
        else None
    )

    text = user_input.text

    parts = []


    # ---------------------------------------------
    # IMAGE
    # ---------------------------------------------

    if photo is not None:

        photo_bytes = photo.getvalue()

        add_message(
            "user",
            "image",
            photo_bytes,
        )

        parts.append(
            types.Part.from_bytes(
                data=photo_bytes,
                mime_type=photo.type,
            )
        )


    # ---------------------------------------------
    # TEXT
    # ---------------------------------------------

    if text:

        add_message(
            "user",
            "text",
            text,
        )

        parts.append(text)


    # ---------------------------------------------
    # IMAGE WITHOUT TEXT
    # ---------------------------------------------

    elif photo is not None:

        parts.append(
            "Explain this study material clearly "
            "and step by step. Identify the main "
            "question or concept first."
        )


    # ---------------------------------------------
    # GEMINI
    # ---------------------------------------------

    if parts:

        with st.spinner(
            "🔍 Reading and understanding..."
        ):

            answer = ask_gemini(parts)

        add_message(
            "assistant",
            "text",
            answer,
        )