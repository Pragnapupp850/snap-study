# 📚 Snap & Study

Snap & Study is an AI-powered study assistant built with Streamlit and Google Gemini.

Students can upload study material such as questions, diagrams, textbook pages,
worksheets, or handwritten notes and receive clear, step-by-step explanations.

## ✨ Features

- 📸 Upload study images
- 🤖 AI-powered explanations using Google Gemini
- 💬 Ask follow-up questions
- 🧠 Maintains conversation context
- 📧 Email a revision summary to the student's email
- 👋 Simple onboarding with name and email
- 🔐 API credentials stored securely using Streamlit secrets
- 🔄 Automatic retry for temporary Gemini service errors

## 🛠️ Tech Stack

- Python
- Streamlit
- Google Gemini API
- Google GenAI Python SDK
- Gmail SMTP

## 📁 Project Structure

```text
snap-study/
├── .streamlit/
│   ├── secrets.toml
│   └── secrets.toml.example
├── app.py
├── prompts.py
├── requirements.txt
├── README.md
├── .gitignore
└── venv/