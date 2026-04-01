# 🧙‍♂️ AI Story Weaver

## Overview

AI Story Weaver is a Streamlit-based app for **collaborative storytelling** using OpenAI.

Users define a story title, genre, and initial hook. The AI generates an engaging opening, and then the story evolves through:

- AI-generated continuations
- User contributions
- Branching story choices

The app maintains **context and consistency** across the story using structured prompts.

---

## 🚀 Features

- ✨ AI-generated story opening
- 🔁 Continue story with AI
- 🎮 Branching choices (multiple plot directions)
- ↩️ Undo last AI response
- 🎚 Creativity control (temperature slider)
- 💾 Export story as Markdown

---

## 🛠 Setup

### 1. Clone the repo
```bash
git clone https://github.com/sryada15-rgb/storyteller-ai.git
cd storyteller-ai

## Create .env
-OPENAI_API_KEY=your_openai_key_here

## Install dependencies
pip install -r requirements.txt

## Run the app
streamlit run app.py
## Model
-Uses OpenAI gpt-4o-mini
-Optimized for:
-storytelling
-coherence
-cost efficiency


## How It Works

-The app stores story history in:

st.session_state.story
-Each AI request includes:
--system prompt (storytelling rules)
--genre-specific constraints
--recent story context
-Context is trimmed to prevent token overflow.
## Project Structure
storyteller-ai/
├── app.py        # Streamlit UI + logic
├── llm.py        # OpenAI API calls
├── prompts.py    # system prompts + rules
├── .env

## Prompt Strategy
-System Prompt

-Ensures:

--consistency
--no contradictions
--engaging narrative tone

##User Prompts

-Include:

--story so far
--next action instruction
--genre constraints


## Known Limitations
Long stories may lose early details (no summarization yet)
Choice parsing depends on text formatting


🚀 Future Improvements
🧠 Story memory (summarization)
🎭 Character tracking
🔁 Regenerate response button
💾 Save/load stories
🌐 Deploy online

🧑‍💻 Author

Built as an AI storytelling project using Streamlit and OpenAI.

---

# 🔥 What I Fixed / Improved

### ❌ Removed:
- HuggingFace / OpenRouter / Groq (no longer used)
- `gpt-3.5-turbo` (outdated)

### ✅ Added:
- modern model (`gpt-4o-mini`)
- features section (important for recruiters)
- clean structure section
- better readability

---

# 🚀 How to Update README in Git

After replacing your README:

```bash
git add README.md
git commit -m "Updated README with OpenAI-only architecture and new features"
git push