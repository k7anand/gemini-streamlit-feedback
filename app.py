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

if "show_questions" not in st.session_state:
    st.session_state.show_questions = False

if "learning_plan" not in st.session_state:
    st.session_state.learning_plan = None

if "show_learning_plan" not in st.session_state:
    st.session_state.show_learning_plan = False

# Load environment variables:
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")


col_title, col_reset = st.columns([6, 1])

with col_title:
    st.title("Resume Reality Check")
    st.markdown("AI-powered analysis of how well your resume matches a job description")

with col_reset:
    if st.button("Restart"):
        st.session_state.clear()
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


if not api_key:
    st.error("API key was not found. Please check your .env file.")
    st.stop()


# Configure Gemini:
if "model" not in st.session_state:
    genai.configure(api_key = api_key)
    st.session_state.model = genai.GenerativeModel("gemini-flash-latest")

model = st.session_state.model


# User inputs:
summary = st.text_area("Summary", placeholder = "Provide brief summary about your background.")
experience = st.text_area("Experience", placeholder = "Paste your work experience bullet points.")
skills = st.text_area("Skills", placeholder = "Please list your technical and soft skills.")
job_title = st.text_input("Job Title")
job_description = st.text_area("Job Description", placeholder = "Paste the full job description here.")
job_information = f"{job_title}\n{job_description}"

# Analyze Resume Button:
if st.button("Analyze Resume"):
    st.session_state.questions = None
    st.session_state.learning_plan = None
    st.session_state.show_questions = False
    st.session_state.show_learning_plan = False

    current_time = time.time()

    # 5-second cooldown
    cooldown = 5

    if current_time - st.session_state.last_api_call_time < cooldown:
        remaining = int(cooldown - (current_time - st.session_state.last_api_call_time))
        st.warning(f"Please wait {remaining} seconds before trying again.")
        st.stop()

    if not job_description:
        st.warning("Please enter a job description.")
        st.stop()

    if not summary and not experience and not skills:
        st.warning("Please provide at least some resume information.")
        st.stop()

    
    prompt = f"""You are an expert recruiter.
    Analyze the candidate information against the job description.

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
    - <bullet points explaining the main factors contributing to the overall score>

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
            response = model.generate_content(prompt)

        st.success("Analysis complete!")
        st.session_state.last_api_call_time = time.time()
        st.session_state.analysis_result = response.text
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
    st.markdown(parsed["explanation"])

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
    st.markdown("---")
    st.markdown("### Next Steps")
    col_q, col_lp = st.columns(2)

    with col_q:
        if st.button("Generate Interview Questions", key = "gen_q"):
            st.session_state.show_questions = True
            st.session_state.questions = None

    with col_lp:
        if st.button("Make Lesson Plan", key = "gen_lp"):
            st.session_state.show_learning_plan = True
            st.session_state.learning_plan = None

    if st.session_state.show_questions and st.session_state.questions is None:
        questions_prompt = f"""You are an expert interviewer.
        Based on the candidate and job description:

        Generate:
        - 2 technical interview questions
        - 2 behavioral interview questions

        Focus on:
        - skill gaps
        - relevant experience
        - job requirements

        Generate different questions each time.

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
                response_q = model.generate_content(questions_prompt)

            st.session_state.questions = response_q.text

        except Exception as e:
            handle_api_error(e, context = "Generating interview questions")


    if st.session_state.show_learning_plan and st.session_state.learning_plan is None:
        parsed = st.session_state.parsed

        lesson_prompt = f"""You are an expert career coach.

        Based on the missing skills below, create a structured and clearly separated learning plan for each skill.

        For EACH skill listed, create a clearly separated section with:
        - What to learn (key concepts, tools, frameworks)
        - How to learn it (online courses, practice strategies, certifications)
        - A small project idea to apply the skill

        Please keep it practical, concise, and actionable.

        Missing Skills:
        {parsed["missing"]}

        Job Title:
        {job_title}
        """

        try:
            if not parsed["missing"].strip():
                st.warning("No missing skills detected. Learning plan not generated.")
            else:
                with st.spinner("Creating learning plan..."):
                    response_lp = model.generate_content(lesson_prompt)

                st.session_state.learning_plan = response_lp.text

        except Exception as e:
            handle_api_error(e, context = "Creating learning plan")
        
            
    if st.session_state.questions:
        st.markdown("---")
        st.markdown("### Interview Questions")
        st.markdown(st.session_state.questions)

        if st.button("Refresh Questions"):
            st.session_state.questions = None

    if st.session_state.learning_plan:
        st.markdown("---")
        st.markdown("### Skill Learning Plan")
        st.markdown(st.session_state.learning_plan)
