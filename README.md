# __Resume Reality Check__
__Last Updated__: May 16, 2026

*Try the app here*: [Resume Reality Check](https://gemini-app-feedback-dbt7fton4mez79shselvyh.streamlit.app/)

__Note on App Availability__: This application is hosted on Streamlit Community Cloud. If the app has been inactive for a period of time, it may take a few minutes to start when you first open it. Please allow the app to fully load before interacting.  

__User Responsibility__: Users are responsible for reviewing and verifying all outputs before using them in a job application.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## __Key Features__

- Structured resume-to-job evaluation with section-level and overall match scores.
- Explainable AI outputs with evidence-based reasoning and ranked importance.  
- Tailored interview question generation with controlled refresh limits.  
- Skill gap identification with personalized learning plans.  
- Stateful, multi-step workflow within a single interactive interface. 

## __Introduction__
Resume Reality Check is an AI-powered web application that evaluates how well a resume aligns with a specific job description. It analyzes three core sections of the resume, namely summary, experience, and skills, and generates structured insights including match scores, strengths, skill gaps, and actionable suggestions. 

The system also provides targeted interview questions and a skill-based learning plan, transforming resume feedback from static evaluation into a guided, decision-support experience for job preparation. The system consolidates resume evaluation, skill gap analysis, interview preparation, and learning plan development into a single structured workflow, eliminating the need for repeated chatbot interactions.

To use the application, please begin by entering your resume content into the provided fields. You can paste your professional summary, work experience, and skills into their respective sections. Then, input the job title and paste the full job description of the role that you are targeting. Once all relevant information is entered, click "Analyze Resume" to initiate the evaluation.

After analysis, the application displays a structured breakdown of your match with the job. This includes section-level scores, an overall match score, an explanation of the score, identified strengths, missing skills, and suggestions for improvement. These outputs are designed to provide both high-level evaluation and specific, actionable feedback.

Users can then proceed to the _Next Steps_ section to deepen their preparation. The "Generate Interview Questions" feature produces tailored technical and behavioral questions based on your profile and the job requirements. The "Make Lesson Plan" feature creates a structured learning roadmap based on identified skill gaps, outlining what to learn, how to learn it, and a small project idea to apply each skill.

To ensure fair usage and maintain system responsiveness, interview question generation includes a limited refresh mechanism. Users can regenerate interview questions up to 3 times per session, allowing for variation in outputs while preventing excessive API usage. This design balances flexibility with responsible resource management.

This application is designed for students, early-career professionals, and job seekers who want to better understand how their experience aligns with specific roles and how to improve their positioning.

## __Problem and Motivation__
Many job seekers increasingly rely on general-purpose chatbots to evaluate their resumes against job descriptions. However, this process can be repetitive, time-consuming, and inconsistent. Users must repeatedly craft prompts, reformat inputs, and manually interpret unstructured responses for each application.

This project addresses that inefficiency by providing a structured, guided workflow for resume evaluation. Instead of relying on ad-hoc prompting, the system standardizes how inputs are processed and how outputs are generated. This ensures consistency across evaluations, reduces variability in feedback quality, and minimizes the cognitive effort required to extract actionable insights.

By transforming unstructured chatbot interactions into a repeatable pipeline, the application streamlines resume analysis, surfaces relevant skill gaps, and supports targeted preparation through interview questions and learning plans. The result is a more efficient and reliable approach to job preparation for candidates navigating multiple applications. 

While many AI-assisted resume evaluation tools are available, Resume Reality Check specifically focuses on how feedback is structured and presented. This application specifically demonstrates how a transparent, pipeline-driven approach can be used to orchestrate LLMs to produce consistent, interpretable, and actionable outputs. 

This is particularly important because job seekers often evaluate multiple roles simultaneously, and inefficiencies in resume feedback can significantly slow down preparation and reduce the quality of applications. Overall, the system transforms resume evaluation from an unstructured, repetitive task into a consistent and actionable workflow that supports more effective job preparation.

## __Architecture__
This application is designed as a multi-stage AI pipeline that combines user input, large language model (LLM) inference, structured data extraction, and interactive visualization within a single Streamlit interface. The system flow is as follows:

1. __User Input Layer__: You enter resume content (summary, experience, skills) along with a target job title and description through the Streamlit interface.
2. __LLM Inference Layer__: The input is sent to the Google Gemini API through Google AI Studio, where a structured prompt is used to generate a detailed evaluation of the resume.
3. __Structured Parsing Layer__: The raw LLM output is processed using regular expressions (regex) to extract key components such as section scores, overall match score, strengths, skill gaps, and suggestions. This converts unstructured text into structured data that can be used reliably within the application.
4. __State Management Layer__: Parsed results and generated outputs are stored using Streamlit session state, enabling multi-step interactions without re-running previous computations.
5. __Visualization Layer__: Structured data is displayed using metrics, formatted sections, and color-coded labels to provide an intuitive and interpretable user experience.
6. __Secondary AI Workflows__: Additional LLM calls are triggered based on user actions. For example, Interview Question Generation produces technical and behavioral questions tailored to the candidate and job description. Similarly, Skill Learning Plan Generation uses extracted skill gaps to generate a structured, actionable learning roadmap.

## __Key Design Decisions__
- __Structured Prompting__: The model is constrained to a strict output format to ensure consistent parsing and reliable downstream processing.
- __Separation of Concerns__: The LLM is responsible for reasoning and content generation, while Python handles structure, validation, and UI rendering.
- __Multi-Stage Pipeline__: Outputs from the initial analysis are reused as inputs for subsequent AI tasks, enabling chained reasoning and more personalized results.
- __Stateful Interaction__: Streamlit session state is used to manage user flow and preserve intermediate results across interactions.
- __Explainable AI__: The system explicitly generates score explanations and highlights strengths to make AI outputs more transparent and actionable.

## __Design Tradeoffs__
- The system prioritizes simplicity, interpretability, and responsiveness over full automation and scale.
- The application uses structured prompting combined with regex-based parsing instead of fully-structured JSON outputs. This approach simplifies prompt design and maintains flexibility in LLM responses, but introduces some sensitivity to formatting inconsistencies.
- The system is designed for interactive, single-user workflows within Streamlit rather than large-scale deployment. This enables fast iteration and a responsive user experience, but is not optimized for high-concurrency production environments.
- Finally, the application operates on the free tier of the Google Gemini API, which imposes limits on the number of requests per day and per minute. To ensure fair usage and prevent errors, the system includes rate-limiting logic and lightweight request control. This design keeps the application accessible without requiring paid infrastructure, but may temporarily restrict usage during high-frequency interactions.

## __Deployment__
This application is deployed using Streamlit Community Cloud, which provides a lightweight and interactive environment for hosting data-driven web applications. Streamlit was chosen to support a stateful, multi-step user experience within a single interface, allowing users to move seamlessly between resume evaluation, interview preparation, and learning plan generation without navigating across multiple pages. Streamlit Community Cloud enables rapid deployment and iteration, making it well-suited for prototyping and user-facing applications that prioritize usability and responsiveness. This deployment approach aligns with the design goals of this project, focusing on accessibility, ease of use, and a guided workflow experience.

## __Data Usage and Privacy__
- This application does not store or persist user data. All inputs provided by the user, including resume content and job descriptions, are processed in real time and are not saved after the session ends.
- User inputs are sent to the Google Gemini API for analysis. This means that the data is transmitted to an external AI service for processing. You should avoid entering highly sensitive personal information.
- The application includes a Terms of Use acknowledgment step before interaction, ensuring that you are aware of how your data is handled. By using the application, you agree to this processing behavior.
- This application provides informational guidance only and does not guarantee job outcomes or hiring decisions. 
- __Important Note__: No user data is logged, stored, or used for model training within this application.

## __Running the Application Locally__
1. Clone the repository
2. Install dependencies: pip install -r requirements.txt
3. Create a .env file in the project root and add your API key:
GEMINI_API_KEY=your_api_key_here
4. Run the application: streamlit run app.py

__Note__: You can obtain your Gemini API key from Google AI Studio.
