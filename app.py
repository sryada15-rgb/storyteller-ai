import os
import streamlit as st
import openai
import requests
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")
client = openai.OpenAI(api_key=openai_api_key) if openai_api_key else None

GENRES = ["Fantasy", "Sci-Fi", "Mystery", "Romance", "Horror", "Comedy"]
LLM_PROVIDERS = ["Auto", "OpenAI", "HuggingFace", "OpenRouter", "Groq"]
HUGGINGFACE_MODELS = ["gpt-4o-mini", "h2oai/h2ogpt-oig", "OpenAssistant/oasst-sft-4-real-v1", "claude-2.1"]
OPENROUTER_MODELS = ["gpt-4o-mini", "gpt-4o", "gpt-4.1", "mistral-7b-chat"]
GROQ_MODELS = ["groq-sonic-1.0.0"]

DEFAULT_SYSTEM_PROMPT = (
    "You are a masterful collaborative storyteller. Continue the story in the chosen genre "
    "while staying 100% consistent with all previous events, character personalities, and world rules. "
    "Never contradict earlier parts of the story. Write in vivid but concise third-person narrative. "
    "Keep tone engaging and fun, and remember all prior story content from the story history."
)

RULE_TEMPLATE = "Genre: {genre}. Keep consistency with character names, plot hooks, tone, and setting. "
"Use immersive language and avoid contradictions."


def init_state():
    if "story" not in st.session_state:
        st.session_state.story = []
    if "user_contributions" not in st.session_state:
        st.session_state.user_contributions = []
    if "ai_history" not in st.session_state:
        st.session_state.ai_history = []
    if "choices" not in st.session_state:
        st.session_state.choices = []
    if "last_ai" not in st.session_state:
        st.session_state.last_ai = ""
    if "story_metadata" not in st.session_state:
        st.session_state.story_metadata = {
            "title": "",
            "genre": GENRES[0],
            "provider": "Auto",
            "hf_model": HUGGINGFACE_MODELS[0],
            "openrouter_model": OPENROUTER_MODELS[0],
            "groq_model": GROQ_MODELS[0],
            "hook": "",
            "rules": "",
            "temperature": 0.7,
        }


def make_huggingface_request(prompt_text, temp=0.7, max_tokens=280, model="gpt2"):
    if not hf_api_key:
        raise RuntimeError("HUGGINGFACE_API_KEY is not set in environment")

    router_url = "https://router.huggingface.co/api/chat/completions"
    headers = {
        "Authorization": f"Bearer {hf_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
            {"role": "user", "content": prompt_text},
        ],
        "temperature": temp,
        "max_tokens": max_tokens,
    }

    response = requests.post(router_url, headers=headers, json=payload, timeout=60)
    if response.status_code in (404, 410):
        # some models may not support the router chat path; retry via direct model endpoint
        fd_url = f"https://api-inference.huggingface.co/models/{model}"
        direct_payload = {
            "inputs": f"{DEFAULT_SYSTEM_PROMPT}\n\n{prompt_text}",
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temp,
                "return_full_text": False,
            },
        }
        response = requests.post(fd_url, headers={"Authorization": f"Bearer {hf_api_key}"}, json=direct_payload, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(f"Hugging Face error: {response.status_code} - {response.text}")

    data = response.json()

    if isinstance(data, dict) and "choices" in data and data["choices"]:
        text = data["choices"][0]["message"].get("content", "")
    elif isinstance(data, list) and data:
        text = data[0].get("generated_text", "")
    elif isinstance(data, dict) and "generated_text" in data:
        text = data.get("generated_text", "")
    else:
        raise RuntimeError("Unexpected Hugging Face response format")

    return text.strip()


def make_openrouter_request(prompt_text, temp=0.7, max_tokens=280, model="gpt-4o-mini"):
    if not openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set in environment")
    url = "https://api.openrouter.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
            {"role": "user", "content": prompt_text},
        ],
        "temperature": temp,
        "max_tokens": max_tokens,
    }
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"OpenRouter error: {response.status_code} - {response.text}")
    data = response.json()
    if "choices" in data and data["choices"]:
        text = data["choices"][0]["message"].get("content", "")
    else:
        raise RuntimeError("Unexpected OpenRouter response format")
    return text.strip()


def make_groq_request(prompt_text, temp=0.7, max_tokens=280, model="groq-sonic-1.0.0"):
    if not groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not set in environment")
    url = f"https://api.groq.ai/v1/models/{model}/infer"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "input": f"{DEFAULT_SYSTEM_PROMPT}\n\n{prompt_text}",
        "max_output_tokens": max_tokens,
        "temperature": temp,
    }
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"Groq error: {response.status_code} - {response.text}")

    data = response.json()
    if "outputs" in data and data["outputs"]:
        if isinstance(data["outputs"], list) and data["outputs"]:
            text = data["outputs"][0].get("text", "")
        elif isinstance(data["outputs"], dict):
            text = data["outputs"].get("text", "")
        else:
            raise RuntimeError("Unexpected Groq response format")
    elif "output" in data:
        text = data.get("output", "")
    else:
        raise RuntimeError("Unexpected Groq response format")

    return text.strip()


def make_llm_request(prompt_text, temp=0.7, max_tokens=280, provider="Auto"):
    errors = []

    def try_openai():
        if not openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in environment")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt_text},
            ],
            temperature=temp,
            max_tokens=max_tokens,
        )
        return response.choices[0].message["content"].strip()

    def try_huggingface():
        if not hf_api_key:
            raise RuntimeError("HUGGINGFACE_API_KEY is not set in environment")
        hf_model = st.session_state.story_metadata.get("hf_model", HUGGINGFACE_MODELS[0])
        return make_huggingface_request(prompt_text, temp=temp, max_tokens=max_tokens, model=hf_model)

    def try_openrouter():
        if not openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set in environment")
        or_model = st.session_state.story_metadata.get("openrouter_model", OPENROUTER_MODELS[0])
        return make_openrouter_request(prompt_text, temp=temp, max_tokens=max_tokens, model=or_model)

    def try_groq():
        if not groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not set in environment")
        groq_model = st.session_state.story_metadata.get("groq_model", GROQ_MODELS[0])
        return make_groq_request(prompt_text, temp=temp, max_tokens=max_tokens, model=groq_model)

    if provider == "Auto":
        if openai_api_key:
            try:
                return try_openai()
            except Exception as e:
                errors.append(f"OpenAI failed: {e}")
        if hf_api_key:
            try:
                return try_huggingface()
            except Exception as e:
                errors.append(f"HuggingFace failed: {e}")
        if openrouter_api_key:
            try:
                return try_openrouter()
            except Exception as e:
                errors.append(f"OpenRouter failed: {e}")
        if groq_api_key:
            try:
                return try_groq()
            except Exception as e:
                errors.append(f"Groq failed: {e}")
        raise RuntimeError("; ".join(errors) or "No provider configured")

    if provider == "OpenAI":
        try:
            return try_openai()
        except Exception as e:
            errors.append(f"OpenAI failed: {e}")
            if hf_api_key:
                try:
                    return try_huggingface()
                except Exception as e2:
                    errors.append(f"HuggingFace failed: {e2}")
            raise RuntimeError("; ".join(errors))

    if provider == "HuggingFace":
        try:
            return try_huggingface()
        except Exception as e:
            errors.append(f"HuggingFace failed: {e}")
            if openai_api_key:
                try:
                    return try_openai()
                except Exception as e2:
                    errors.append(f"OpenAI failed: {e2}")
            raise RuntimeError("; ".join(errors))

    if provider == "OpenRouter":
        try:
            return try_openrouter()
        except Exception as e:
            errors.append(f"OpenRouter failed: {e}")
            if openai_api_key:
                try:
                    return try_openai()
                except Exception as e2:
                    errors.append(f"OpenAI failed: {e2}")
            if hf_api_key:
                try:
                    return try_huggingface()
                except Exception as e2:
                    errors.append(f"HuggingFace failed: {e2}")
            if groq_api_key:
                try:
                    return try_groq()
                except Exception as e2:
                    errors.append(f"Groq failed: {e2}")
            raise RuntimeError("; ".join(errors))

    if provider == "Groq":
        try:
            return try_groq()
        except Exception as e:
            errors.append(f"Groq failed: {e}")
            if openai_api_key:
                try:
                    return try_openai()
                except Exception as e2:
                    errors.append(f"OpenAI failed: {e2}")
            if hf_api_key:
                try:
                    return try_huggingface()
                except Exception as e2:
                    errors.append(f"HuggingFace failed: {e2}")
            if openrouter_api_key:
                try:
                    return try_openrouter()
                except Exception as e2:
                    errors.append(f"OpenRouter failed: {e2}")
            raise RuntimeError("; ".join(errors))

    raise RuntimeError(f"Unknown provider: {provider}")


def build_story_context():
    return "\n\n".join(st.session_state.story)


def ai_generate_opening():
    title = st.session_state.story_metadata["title"]
    genre = st.session_state.story_metadata["genre"]
    hook = st.session_state.story_metadata["hook"]
    if not title or not hook:
        st.error("Please provide both a title and initial hook to start.")
        return

    prompt = (
        f"Story Title: {title}\n"
        f"Genre: {genre}\n"
        f"Initial hook/setting: {hook}\n"
        "Generate a strong opening for this story (150-250 words), immersive and genre-specific. "
        "Use third-person narrative and set the tone."
    )

    try:
        with st.spinner("Generating opening paragraph..."):
            output = make_llm_request(prompt, temp=st.session_state.story_metadata["temperature"], max_tokens=400, provider=st.session_state.story_metadata.get("provider", "OpenAI"))
            st.session_state.story = [output]
            st.session_state.last_ai = output
            st.success("Story started. A strong opening paragraph is ready!")
    except Exception as e:
        st.error(f"Failed to generate opening: {e}")


def ai_continue_story():
    if not st.session_state.story:
        st.error("Start the story first.")
        return

    context = build_story_context()
    prompt = (
        f"Existing story so far:\n{context}\n\n"
        "Continue with 1-2 coherent paragraphs (100-220 words), staying consistent with tone, characters, and plot. "
        "Do not recap too much; move the plot forward."
    )

    try:
        with st.spinner("AI is writing the next section..."):
            output = make_llm_request(prompt, temp=st.session_state.story_metadata["temperature"], max_tokens=350, provider=st.session_state.story_metadata.get("provider", "OpenAI"))
            st.session_state.story.append(output)
            st.session_state.ai_history.append(output)
            st.session_state.last_ai = output
            st.success("AI continuation added to story.")
    except Exception as e:
        st.error(f"Failed to continue story: {e}")


def ai_branch_choices():
    if not st.session_state.story:
        st.error("Start the story first.")
        return

    context = build_story_context()
    prompt = (
        f"Existing story so far:\n{context}\n\n"
        "Propose 3 distinct plot directions (2-3 sentences each) as choices for next moves. "
        "Number them as 1., 2., 3. Include a short rationale for each."
    )

    try:
        with st.spinner("AI is generating branching choices..."):
            output = make_llm_request(prompt, temp=st.session_state.story_metadata["temperature"], max_tokens=240, provider=st.session_state.story_metadata.get("provider", "OpenAI"))
            st.session_state.choices = output.split("\n")
            st.success("Choices ready. Please select one to continue.")
    except Exception as e:
        st.error(f"Failed to generate choices: {e}")


def ai_apply_choice(choice_index):
    if not st.session_state.choices or choice_index < 0 or choice_index >= len(st.session_state.choices):
        st.error("Valid choice required.")
        return

    choice_text = st.session_state.choices[choice_index]
    context = build_story_context()
    prompt = (
        f"Existing story so far:\n{context}\n\n"
        f"Selected direction: {choice_text}\n"
        "Continue the story in that direction with 1-2 paragraphs, staying consistent with established characters and rules."
    )

    try:
        with st.spinner("AI is applying selected choice..."):
            output = make_llm_request(prompt, temp=st.session_state.story_metadata["temperature"], max_tokens=300, provider=st.session_state.story_metadata.get("provider", "OpenAI"))
            st.session_state.story.append(output)
            st.session_state.ai_history.append(output)
            st.session_state.last_ai = output
            st.session_state.choices = []
            st.success("Story continued based on your choice.")
    except Exception as e:
        st.error(f"Failed to apply selected choice: {e}")


def undo_last_ai_turn():
    if not st.session_state.ai_history:
        st.warning("No AI turn to undo.")
        return
    last = st.session_state.ai_history.pop()
    if st.session_state.story and st.session_state.story[-1] == last:
        st.session_state.story.pop()
        st.success("Last AI turn undone.")
    else:
        st.warning("No matching AI turn found in story content.")


def main():
    st.set_page_config(page_title="AI Story Weaver", layout="wide")
    init_state()

    st.title("🧙‍♂️ AI Story Weaver")
    st.markdown("Collaborative storytelling with strong continuity and genre consistency.")

    if openai_api_key:
        st.success("OpenAI API key loaded ✅")
    else:
        st.warning("OPENAI_API_KEY missing: add it to .env and restart the app.")

    if hf_api_key:
        st.success("Hugging Face API key loaded ✅")
    else:
        st.info("HUGGINGFACE_API_KEY not set; Hugging Face provider will be unavailable until key is added.")

    if openrouter_api_key:
        st.success("OpenRouter API key loaded ✅")
    else:
        st.info("OPENROUTER_API_KEY not set; OpenRouter provider will be unavailable until key is added.")

    if groq_api_key:
        st.success("Groq API key loaded ✅")
    else:
        st.info("GROQ_API_KEY not set; Groq provider will be unavailable until key is added.")

    with st.expander("Story Setup", expanded=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.session_state.story_metadata["title"] = st.text_input("Title", st.session_state.story_metadata["title"])
            st.session_state.story_metadata["hook"] = st.text_area("Initial Hook / Setting", st.session_state.story_metadata["hook"], height=120)
        with col2:
            st.session_state.story_metadata["genre"] = st.selectbox("Genre", GENRES, index=GENRES.index(st.session_state.story_metadata["genre"]))
            st.session_state.story_metadata["provider"] = st.selectbox("LLM Provider", LLM_PROVIDERS, index=LLM_PROVIDERS.index(st.session_state.story_metadata.get("provider", "Auto")))
            if st.session_state.story_metadata["provider"] == "HuggingFace":
                st.session_state.story_metadata["hf_model"] = st.selectbox("HF Chat Model", HUGGINGFACE_MODELS, index=HUGGINGFACE_MODELS.index(st.session_state.story_metadata.get("hf_model", HUGGINGFACE_MODELS[0])))
            if st.session_state.story_metadata["provider"] == "OpenRouter":
                st.session_state.story_metadata["openrouter_model"] = st.selectbox("OpenRouter Model", OPENROUTER_MODELS, index=OPENROUTER_MODELS.index(st.session_state.story_metadata.get("openrouter_model", OPENROUTER_MODELS[0])))
            if st.session_state.story_metadata["provider"] == "Groq":
                st.session_state.story_metadata["groq_model"] = st.selectbox("Groq Model", GROQ_MODELS, index=GROQ_MODELS.index(st.session_state.story_metadata.get("groq_model", GROQ_MODELS[0])))
            st.session_state.story_metadata["rules"] = RULE_TEMPLATE.format(genre=st.session_state.story_metadata["genre"])
            st.write("### Current Genre, Provider, and Rules")
            st.write(f"**{st.session_state.story_metadata['genre']} (Provider: {st.session_state.story_metadata['provider']})**")
            if st.session_state.story_metadata["provider"] == "HuggingFace":
                st.write(f"Selected HF model: {st.session_state.story_metadata['hf_model']}")
            if st.session_state.story_metadata["provider"] == "OpenRouter":
                st.write(f"Selected OpenRouter model: {st.session_state.story_metadata['openrouter_model']}")
            if st.session_state.story_metadata["provider"] == "Groq":
                st.write(f"Selected Groq model: {st.session_state.story_metadata['groq_model']}")
            st.write(st.session_state.story_metadata["rules"])

        if st.button("Start the Story"):
            ai_generate_opening()

    with st.expander("Main Storytelling", expanded=True):
        st.write("### Full Story So Far")
        if st.session_state.story:
            for idx, paragraph in enumerate(st.session_state.story, 1):
                st.markdown(f"**Part {idx}:** {paragraph}")

        user_text = st.text_area("Your contribution (optional, 1-2 sentences)")

        colA, colB, colC = st.columns(3)
        with colA:
            if st.button("Continue with AI"):
                if user_text.strip():
                    st.session_state.story.append("[User contribution] " + user_text.strip())
                ai_continue_story()
        with colB:
            if st.button("Give Me Choices"):
                if user_text.strip():
                    st.session_state.story.append("[User contribution] " + user_text.strip())
                ai_branch_choices()
        with colC:
            if st.button("Undo Last AI Turn"):
                undo_last_ai_turn()

        st.session_state.story_metadata["temperature"] = st.slider("Temperature / Creativity", 0.1, 1.0, st.session_state.story_metadata["temperature"], step=0.05)

        if st.session_state.choices:
            st.write("### AI Suggested Choices")
            for i, option in enumerate(st.session_state.choices):
                if option.strip():
                    if st.button(f"Choose {i+1}: {option[:60]}", key=f"choice_{i}"):
                        ai_apply_choice(i)

    with st.expander("Export (Bonus)"):
        if st.button("Export as Markdown"):
            md = f"# {st.session_state.story_metadata['title']}\n\n"
            for p in st.session_state.story:
                md += p + "\n\n"
            st.download_button(label="Download Story as .md", data=md, file_name="story.md", mime="text/markdown")

    if not openai_api_key:
        st.warning("Set OPENAI_API_KEY in .env to enable OpenAI AI calls.")


if __name__ == "__main__":
    main()
