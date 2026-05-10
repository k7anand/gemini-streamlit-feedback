import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
import time
import re

def parse_analysis(text: str) -> dict:
    """Converts unstructured LLM output (text) into a structured dictionary that the UI can use."""
    results = {}

    # Extract scores:
    summary = re.search(r"Summary:\s*(\d+|Not Provided)", text)
    experience = re.search(r"Experience:\s*(\d+|Not Provided)", text)
    skills = re.search(r"Skills:\s*(\d+|Not Provided)", text)
    overall = re.search(r"Score:\s*(\d+)", text)

    results["summary"] = summary.group(1) if summary else "N/A"
    results["experience"] = experience.group(1) if experience else "N/A"
    results["skills"] = skills.group(1) if skills else "N/A"
    results["overall"] = overall.group(1) if overall else "N/A"

    # Extract sections:
    missing = re.search(r"MISSING SKILLS:\s*(.*?)SUGGESTIONS:", text, re.S)
    suggestions = re.search(r"SUGGESTIONS:\s*(.*)", text, re.S)

    results["missing"] = missing.group(1).strip() if missing else ""
    results["suggestions"] = suggestions.group(1).strip() if suggestions else ""

    strengths = re.search(r"STRENGTHS:\s*(.*?)MISSING SKILLS:", text, re.S)
    results["strengths"] = strengths.group(1).strip() if strengths else ""

    explanation = re.search(r"SCORE EXPLANATION:\s*(.*?)STRENGTHS:", text, re.S)
    results["explanation"] = explanation.group(1).strip() if explanation else ""
    
    if not explanation:
        results["explanation"] = text 

    return results


def get_match_label_and_color(score: str or int) -> str:
    """Map a numerical score to qualitative label + UI color."""
    try:
        score = int(score)
    except:
        return "Not Available", "gray"

    if score >= 85:
        return "Strong Match", "green"
    elif score >= 65:
        return "Moderate Match", "orange"
    else:
        return "Needs Improvement", "red"


def handle_api_error(e, context = ""):
    """Acts as a centralized handler for API exceptions by detecting common failure modes such as rate limiting and
    surfacing consistent, user-friendly messages in the UI, improving robustness and maintainability of API-dependent workflows."""
    error_str = str(e).lower()

    if "429" in error_str or "quota" in error_str:
        st.warning(f"{context} is temporarily busy due to high demand. Please wait a moment and try again shortly.")
    else:
        if context:
            st.error(f"Something went wrong while {context.lower()}. Please try again.")
        else:
            st.error("Something went wrong. Please try again.")


if "last_api_call_time" not in st.session_state:
    st.session_state.last_api_call_time = 0

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "questions" not in st.session_state:
    st.session_state.questions = None

if "learning_plan" not in st.session_state:
    st.session_state.learning_plan = None

if "mode" not in st.session_state:
    st.session_state.mode = None 

if "refresh_count" not in st.session_state:
    st.session_state.refresh_count = 0


def generate_with_retry(model, prompt, retries = 3, delay = 2):
    """Performs model inference with retry logic to improve robustness against transient
    errors while skipping retries for rate limit failures."""
    for attempt in range(retries):
        try:
            return model.generate_content(prompt)
        except Exception as e:
            error_str = str(e).lower()

            if "429" in error_str or "quota" in error_str:
                raise e # do not retry rate limits

            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e


def enforce_rate_limit():
    """Enforces a minimum time interval between API requests to prevent excessive usage,
    ensuring compliance with rate limits and improving system stability."""
    now = time.time()
    last = st.session_state.get("last_api_call_time", 0)

    if now - last < 5:
        st.warning("You're making requests too quickly. Please wait a few seconds and try again.")
        return False

    st.session_state.last_api_call_time = now
    return True


# Load environment variables:
load_dotenv()

try:
    api_key = st.secrets.get("GEMINI_API_KEY")
except Exception:
    api_key = os.getenv("GEMINI_API_KEY")


if not api_key:
    st.error("API key was not found. Please check your .env file.")
    st.stop()


col_title, col_reset = st.columns([6, 1])

with col_title:
    st.title("Resume Reality Check")
    st.markdown("AI-powered analysis of how well your resume matches a job description")

with col_reset:
    if st.button("Restart"):
        for key in [
            "analysis_result", "questions", "learning_plan", "mode", "refresh_count",
            "summary_input", "experience_input", "skills_input", "job_title_input", "job_description_input"
        ]:
            st.session_state.pop(key, None)

        st.session_state["summary_input"] = ""
        st.session_state["experience_input"] = ""
        st.session_state["skills_input"] = ""
        st.session_state["job_title_input"] = ""
        st.session_state["job_description_input"] = ""
        st.rerun()

if "accepted_terms" not in st.session_state:
    st.session_state.accepted_terms = False

if not st.session_state.accepted_terms:
    st.subheader("Terms of Use")
    st.markdown("""
    - This tool does not store your data.
    - Your inputs are processed securely via an external AI service (Gemini).
    - Do not enter highly sensitive personal information.
    - This tool is for educational and informational purposes only.
    """)

    accept = st.checkbox("I understand and agree to the Terms of Use.")

    if accept:
        st.session_state.accepted_terms = True
        st.rerun()

    st.stop()


# Configure Gemini:
if "model" not in st.session_state:
    genai.configure(api_key = api_key)
    st.session_state.model = genai.GenerativeModel("gemini-flash-latest")

model = st.session_state.model


# User inputs:
summary = st.text_area("Summary", key = "summary_input", placeholder = "Provide brief summary about your background.")
experience = st.text_area("Experience", key = "experience_input", placeholder = "Paste your work experience bullet points.")
skills = st.text_area("Skills", key = "skills_input", placeholder = "Please list your technical and soft skills.")
job_title = st.text_input("Job Title", key = "job_title_input", placeholder = "Paste the job title here.")
job_description = st.text_area("Job Description", key = "job_description_input", placeholder = "Paste the full job description here.")
job_information = f"{job_title}\n{job_description}"

# Analyze Resume Button:
if st.button("Analyze Resume"):
    st.session_state.questions = None
    st.session_state.learning_plan = None
    st.session_state.mode = None
    st.session_state.refresh_count = 0

    if not job_description:
        st.warning("Please enter a job description.")
        st.stop()

    if not summary and not experience and not skills:
        st.warning("Please provide at least some resume information.")
        st.stop()

    
    prompt = f"""Analyze the candidate information against the job description.

    Follow ALL instructions strictly.

    ---------------------------
    EVALUATION RULES
    ---------------------------

    - Scores must be between 0 and 100.
    - Be consistent and realistic.
    - Be constructive and supportive in tone.

    If a section is empty:
    - DO NOT assign a score of 0.
    - Mark it as "Not Provided".
    - DO NOT penalize the overall score for missing sections.

    If the candidate appears to be a student or early-career:
    - Evaluate based on potential and relevance.
    - DO NOT heavily penalize lack of years of experience.

    Domain Alignment Rule:
    - Strongly evaluate whether the candidate’s domain aligns with the job role.
    - In cases of major domain mismatch, the overall score should typically fall below 50.
    - Transferable skills should NOT significantly increase the score when domain alignment is weak.
    - Do not reward unrelated technical skills when the job domain is different.

    ---------------------------
    INPUT
    ---------------------------

    Candidate Summary:
    {summary}

    Candidate Experience:
    {experience}

    Candidate Skills:
    {skills}

    Job Description:
    {job_information}

    ---------------------------
    OUTPUT FORMAT (STRICT)
    ---------------------------

    SECTION SCORES:
    - Summary: <score or "Not Provided">
    - Experience: <score or "Not Provided">
    - Skills: <score or "Not Provided">

    OVERALL MATCH:
    - Score: <number between 0 and 100>

    SCORE EXPLANATION:
    For each factor, provide:

    - Factor: <specific, evidence-based reason referencing the candidate’s background and job requirements>
      Impact: <Positive or Negative>
      Importance: <Low / Moderate / High / Very High>

    Guidelines:
    - Include 6-8 key factors with diversified levels of importance but Factors MUST be listed in descending order of importance from Very High to Low.
    - Each factor MUST reference specific skills, experience, or requirements from the input
    - Each factor should clearly connect a candidate attribute to a specific job requirement
    - At least 2 factors MUST highlight clear mismatches or weaknesses when present.
    - Avoid vague statements like "strong background" or "good experience"
    - Be explicit about what matches or does not match (e.g., "Experience with SQL aligns with job requirement for data querying")
    - Importance should reflect how much the factor influenced the overall score

    STRENGTHS:
    - <bullet points highlighting what the candidate is doing well>

    MISSING SKILLS:
    - <bullet points>

    SUGGESTIONS:
    - <bullet points>

    ---------------------------
    IMPORTANT
    ---------------------------

    - Do NOT add any extra sections.
    - Do NOT include explanations outside this format.
    - Keep output clean and structured.
    """
    
    try:
        with st.spinner("Analyzing..."):
            if enforce_rate_limit():
                response = generate_with_retry(model, prompt)
                st.session_state.analysis_result = response.text
                st.success("Analysis complete!")
                st.session_state.last_api_call_time = time.time()
    
    except Exception as e:
        handle_api_error(e, context = "Resume analysis")



if st.session_state.analysis_result:
    parsed = parse_analysis(st.session_state.analysis_result)
    st.session_state.parsed = parsed
    label, color = get_match_label_and_color(parsed["overall"])

    st.markdown("---")
    st.markdown(f"<h3 style='color:{color};'>{label}</h3>", unsafe_allow_html = True)
    st.subheader("Match Overview")
    st.markdown("<br>", unsafe_allow_html = True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Summary", parsed["summary"])
    col2.metric("Experience", parsed["experience"])
    col3.metric("Skills", parsed["skills"])
    col4.metric("Overall Match", parsed["overall"])

    st.markdown("---")
    st.subheader("Why This Overall Score")
    explanation_text = parsed["explanation"]

    if explanation_text:
        lines = explanation_text.split("\n")

        for line in lines:
            line = line.strip()

            if line.startswith("- Factor:"):
                st.markdown("<br>", unsafe_allow_html = True)
                st.markdown(f"**{line}**")
            elif "Impact: Positive" in line:
                st.markdown(f"<span style='color:green; font-size:0.9em'>{line}</span>", unsafe_allow_html = True)
            elif "Impact: Negative" in line:
                st.markdown(f"<span style='color:red; font-size:0.9em'>{line}</span>", unsafe_allow_html = True)
            elif "Importance:" in line:
                st.markdown(f"<span style='font-size:0.9em; font-style:italic'>{line}</span>", unsafe_allow_html = True)
            else:
                st.markdown(line)
            

    st.markdown("---")
    st.subheader("Strengths")
    st.markdown(parsed["strengths"])

    st.markdown("---")
    st.subheader("Missing Skills")

    st.markdown(parsed["missing"])

    st.markdown("---")
    st.subheader("Suggestions")

    st.markdown(parsed["suggestions"])
    st.markdown("---")



if st.session_state.analysis_result:
    st.markdown("<br><br>", unsafe_allow_html = True)
    st.markdown("### Next Steps")
    col_q, col_lp = st.columns(2)

    with col_q:
        if st.session_state.mode != "questions":
            if st.button("Generate Interview Questions", key = "gen_q"):
                st.session_state.mode = "questions"
                st.rerun()

    with col_lp:
        if st.session_state.mode != "learning":
            if st.button("Make Lesson Plan", key = "gen_lp"):
                st.session_state.mode = "learning"
                st.rerun()

    if st.session_state.mode == "questions" and st.session_state.questions is None:
        questions_prompt = f"""Please generate:
        - 2 technical interview questions
        - 2 behavioral interview questions

        Focus on:
        - skill gaps
        - relevant experience
        - job requirements

        Generate different questions each time. Return ONLY the questions as bullet points. Do not include any introductions or additional explanations.

        Candidate Summary:
        {summary}

        Candidate Experience:
        {experience}

        Candidate Skills:
        {skills}

        Job Description:
        {job_information}
        """

        try:
            with st.spinner("Generating questions..."):
                if enforce_rate_limit():
                    response_q = generate_with_retry(model, questions_prompt)
                    st.session_state.questions = response_q.text

        except Exception as e:
            handle_api_error(e, context = "Generating interview questions")


    if st.session_state.mode == "learning" and st.session_state.learning_plan is None:
        parsed = st.session_state.parsed

        lesson_prompt = f"""Based on the missing skills below, create a structured and clearly separated learning plan for each skill.

        For EACH skill listed, create a clearly separated section with:
        - What to learn (key concepts, tools, frameworks)
        - How to learn it (online courses, practice strategies, certifications)
        - A small project idea to apply the skill

        Please keep it practical, concise, and actionable.

        Return ONLY the learning plan. Do not include any introductions or additional explanations.

        Missing Skills:
        {parsed["missing"]}

        Job Title:
        {job_title}
        """

        try:
            if not parsed["missing"].strip():
                st.warning("No missing skills detected. Thus, learning plan will not be generated.")
            else:
                with st.spinner("Creating learning plan..."):
                    if enforce_rate_limit():
                        response_lp = generate_with_retry(model, lesson_prompt)
                        st.session_state.learning_plan = response_lp.text

        except Exception as e:
            handle_api_error(e, context = "Creating learning plan")
        
            
    if st.session_state.mode == "questions" and st.session_state.questions:
        st.markdown("<br><br>", unsafe_allow_html = True)
        st.markdown("### Interview Questions")
        st.caption("Interview questions are tailored to your profile. Click 'Refresh Questions' to explore more variations. You can generate up to 3 variations per session.")
        st.markdown(st.session_state.questions)
        remaining = 3 - st.session_state.refresh_count

        if remaining > 0:
            st.caption(f"Refreshes remaining: {remaining}")
        else:
            st.caption("No refreshes remaining")

        if st.button("Refresh Questions"):
            if st.session_state.refresh_count >= 3:
                st.warning("Maximum refresh limit reached!")
            else:
                st.session_state.refresh_count = st.session_state.refresh_count + 1
                st.session_state.questions = None
                st.rerun()

    if st.session_state.mode == "learning" and st.session_state.learning_plan:
        st.markdown("<br><br>", unsafe_allow_html = True)
        st.markdown("### Skill Learning Plan")
        st.markdown(st.session_state.learning_plan)
