# MyAvatar AI Story Weaver (Prototype)

## Overview

A Streamlit app for collaborative storytelling with AI. Users define title, genre, and initial hook. AI generates a strong opening paragraph, then users and AI alternate contributions with consistency and context-aware prompts.

## Setup

1. Clone repo
2. Create `.env` with your available API keys (at least one):
   ```env
   OPENAI_API_KEY=your_openai_key_here
   HUGGINGFACE_API_KEY=your_hf_key_here
   OPENROUTER_API_KEY=your_openrouter_key_here
   GROQ_API_KEY=your_groq_key_here
   ```
3. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```

## Model/provider

The app supports:
- OpenAI via `gpt-3.5-turbo` (preferred)
- Hugging Face via router/direct inference
- OpenRouter (router-based)
- Groq

The default provider is `Auto`, which tries available providers in this order: OpenAI, HuggingFace, OpenRouter, Groq.

## UI controls

- Start the story: generate opening from title/hook
- Continue with AI: append AI text to story
- Give Me Choices: generate branching options
- Undo Last AI Turn: remove last generated AI paragraph
- Export as Markdown: download story rd

## Troubleshooting

- If a provider is unavailable, set another provider or keep `Auto` with at least one configured key.
- For local reset, refresh browser or stop/restart Streamlit.

## Notes

- Story history is kept in `st.session_state.story` and re-used for each LLM call.
- Prompts include a consistent system prompt from `app.py` and previous context for continuity.

- OpenAI `gpt-3.5-turbo` via `openai` Python SDK.

## Prompt

System prompt in `app.py`:

"You are a masterful collaborative storyteller..."

User prompt pattern includes current story context, next action instructions, and genre consistency.

## Consistency strategy

- Full story history is sent on every API call.
- System prompt enforces no contradictions + character/plot consistency.
- History is stored in `st.session_state.story` and reused for each AI completion.

## Bonus features implemented

- Undo last AI turn
- Export full story as Markdown

## Known issue / what didn’t work first

- Initially user contributions were not preserved in context; fixed by appending them to story before invoking AI actions.

## Next improvements

- Add character tracker extraction, visualization prompt generation, and rate-limit retry logic.
- Add better multi-turn state packaging to avoid exceeding token limits (summarize old context).