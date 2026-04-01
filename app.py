# app.py

import streamlit as st
from llm import make_llm_request
from prompts import build_rules

GENRES = ["Fantasy", "Sci-Fi", "Mystery", "Romance", "Horror", "Comedy"]


# ---------------- STATE ---------------- #

def init_state():
    if "story" not in st.session_state:
        st.session_state.story = []
    if "ai_history" not in st.session_state:
        st.session_state.ai_history = []
    if "choices" not in st.session_state:
        st.session_state.choices = []
    if "story_metadata" not in st.session_state:
        st.session_state.story_metadata = {
            "title": "",
            "genre": GENRES[0],
            "hook": "",
            "temperature": 0.7,
        }


def build_story_context(max_parts=6):
    return "\n\n".join(st.session_state.story[-max_parts:])


# ---------------- AI FUNCTIONS ---------------- #

def ai_generate_opening():
    title = st.session_state.story_metadata["title"]
    genre = st.session_state.story_metadata["genre"]
    hook = st.session_state.story_metadata["hook"]

    if not title or not hook:
        st.error("Please provide both a title and hook.")
        return

    rules = build_rules(genre)

    prompt = (
        f"Story Title: {title}\n"
        f"Genre: {genre}\n"
        f"Hook: {hook}\n"
        "Write an engaging opening (150-250 words)."
    )

    try:
        with st.spinner("Generating opening..."):
            output = make_llm_request(prompt, rules, st.session_state.story_metadata["temperature"], 400)
            st.session_state.story = [output]
            st.success("Story started!")
    except Exception as e:
        st.error(str(e))


def ai_continue_story():
    if not st.session_state.story:
        st.error("Start the story first.")
        return

    genre = st.session_state.story_metadata["genre"]
    rules = build_rules(genre)
    context = build_story_context()

    prompt = f"Story so far:\n{context}\n\nContinue the story."

    try:
        with st.spinner("Writing..."):
            output = make_llm_request(prompt, rules)
            st.session_state.story.append(output)
            st.session_state.ai_history.append(output)
    except Exception as e:
        st.error(str(e))


def ai_branch_choices():
    genre = st.session_state.story_metadata["genre"]
    rules = build_rules(genre)
    context = build_story_context()

    prompt = f"Story so far:\n{context}\n\nGive 3 next plot choices."

    try:
        with st.spinner("Thinking..."):
            output = make_llm_request(prompt, rules)

            import re
            choices = re.split(r"\n?\d+\.\s", output)
            st.session_state.choices = [c.strip() for c in choices if c.strip()]
    except Exception as e:
        st.error(str(e))


def ai_apply_choice(index):
    genre = st.session_state.story_metadata["genre"]
    rules = build_rules(genre)
    context = build_story_context()
    choice = st.session_state.choices[index]

    prompt = f"{context}\n\nContinue this direction: {choice}"

    try:
        with st.spinner("Continuing..."):
            output = make_llm_request(prompt, rules)
            st.session_state.story.append(output)
            st.session_state.ai_history.append(output)
            st.session_state.choices = []
    except Exception as e:
        st.error(str(e))


def undo_last():
    if st.session_state.ai_history:
        last = st.session_state.ai_history.pop()
        if st.session_state.story and st.session_state.story[-1] == last:
            st.session_state.story.pop()


# ---------------- UI ---------------- #

def main():
    st.set_page_config(page_title="AI Story Weaver", layout="wide")
    init_state()

    st.title("🧙‍♂️ AI Story Weaver")

    with st.expander("Setup", expanded=True):
        st.session_state.story_metadata["title"] = st.text_input("Title")
        st.session_state.story_metadata["hook"] = st.text_area("Hook")
        st.session_state.story_metadata["genre"] = st.selectbox("Genre", GENRES)

        if st.button("Start Story"):
            ai_generate_opening()

    with st.expander("Story", expanded=True):
        
        st.session_state.story_metadata["temperature"] = st.slider(
        "Creativity (Temperature)", 0.1, 1.0,
        st.session_state.story_metadata["temperature"],
        step=0.05
            )
        for i, part in enumerate(st.session_state.story, 1):
            st.markdown(f"**Part {i}:** {part}")

            

        user_input = st.text_area("Add idea (optional)")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Continue"):
                if user_input.strip():
                    st.session_state.story.append(f"User: {user_input}")
                ai_continue_story()

        with col2:
            if st.button("Choices"):
                ai_branch_choices()

        with col3:
            if st.button("Undo"):
                undo_last()

        if st.session_state.choices:
            for i, c in enumerate(st.session_state.choices):
                if st.button(f"{i+1}: {c[:60]}", key=f"c{i}"):
                    ai_apply_choice(i)

    with st.expander("Export"):
        if st.button("Download"):
            md = "# Story\n\n" + "\n\n".join(st.session_state.story)
            st.download_button("Download .md", md, "story.md")


if __name__ == "__main__":
    main()