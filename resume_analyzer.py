import os
import streamlit as st
import nltk
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
from extract_text import extract_text_from_pdf, extract_text_from_docx

nltk.download('punkt')
nltk.download('stopwords')
from nltk.corpus import stopwords

# Function to clean, tokenize, and analyze resume content
def analyze_resume(resume_text, job_keywords):
    stop_words = set(stopwords.words('english'))
    tokens = nltk.word_tokenize(resume_text)
    filtered_tokens = [word for word in tokens if word.isalnum() and word.lower() not in stop_words]
    filtered_text = ' '.join(filtered_tokens)

    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([filtered_text] + job_keywords)
    similarity_scores = cosine_similarity(vectors[0:1], vectors[1:]).flatten()

    return similarity_scores

# Function to extract individual skill experience
def extract_experience(resume_text, skills):
    experience_data = {}
    for skill in skills:
        pattern = rf'({skill})\s*(\d+)\s*(years|yrs|months|mos)'
        matches = re.findall(pattern, resume_text, re.IGNORECASE)
        total_experience = sum(int(match[1]) if "year" in match[2].lower() else int(match[1])/12 for match in matches)
        experience_data[skill] = total_experience if total_experience > 0 else 0
    return experience_data

# Function to extract total experience from the resume
def extract_total_experience(resume_text):
    matches = re.findall(r'(\d+)\s*(years|yrs|months|mos) of experience', resume_text, re.IGNORECASE)
    total_experience = sum(int(match[0]) if "year" in match[1].lower() else int(match[0])/12 for match in matches)
    return total_experience if total_experience > 0 else 0

# Streamlit UI
st.set_page_config(page_title="Resume Analyzer with Experience Matching", layout="centered")
st.title("📄 Resume Analyzer with Experience Match")
st.markdown("Upload your resume and compare it with the required skills and experience levels.")

# User inputs for required job experience and skill-based experience
overall_experience_required = st.text_input("📅 Enter overall job experience required (in years)", "5")
skills_input = st.text_input("🛠️ Enter required skills (comma-separated)", "python, machine learning, data analysis")
experience_input = st.text_input("⏳ Enter required experience per skill (comma-separated, in years)", "3,2,2")

# File uploader
uploaded_file = st.file_uploader("Upload your resume (.pdf or .docx)", type=["pdf", "docx"])

if uploaded_file and skills_input and experience_input and overall_experience_required:
    required_skills = [skill.strip().lower() for skill in skills_input.split(",") if skill.strip()]
    expected_experience = [int(exp.strip()) for exp in experience_input.split(",") if exp.strip()]
    min_overall_experience = int(overall_experience_required.strip())

    if len(required_skills) != len(expected_experience):
        st.error("Mismatch between the number of skills and experience entries.")
        st.stop()

    file_name = uploaded_file.name.lower()
    ext = file_name.split('.')[-1]
    temp_path = f"temp.{ext}"

    with open(temp_path, "wb") as f:
        f.write(uploaded_file.read())

    if ext == "pdf":
        resume_text = extract_text_from_pdf(temp_path)
    elif ext == "docx":
        resume_text = extract_text_from_docx(temp_path)
    else:
        st.error("Unsupported file format.")
        st.stop()

    os.remove(temp_path)

    # Extract overall experience and skill-specific experience
    overall_experience = extract_total_experience(resume_text)
    experience_data = extract_experience(resume_text, required_skills)

    # Analyze skill match
    similarity_scores = analyze_resume(resume_text, required_skills)

    st.subheader("🔍 Match Scores and Experience Analysis")
    
    final_scores = []
    for skill, sim_score, exp, exp_req in zip(required_skills, similarity_scores, experience_data.values(), expected_experience):
        # Adjust experience value based on overall experience
        adjusted_experience = max(exp, overall_experience / len(required_skills))  # Distribute overall experience
        experience_match = min(adjusted_experience / exp_req, 1)  # Normalize experience match (1 = full match)
        final_score = (sim_score + experience_match) / 2  # Averaging similarity and experience match
        final_scores.append(final_score)
        
        st.write(f"**{skill.capitalize()}**: {sim_score:.2f} (Skill Match) | {adjusted_experience:.1f} years (Adjusted Experience) | {exp_req} years required | Final Score: {final_score:.2f}")

    # Overall experience match evaluation
    overall_match = min(overall_experience / min_overall_experience, 1)  # Normalize
    st.subheader("🎯 Overall Experience Match")
    st.write(f"🔹 **Total Experience Found:** {overall_experience:.1f} years")
    st.write(f"🔹 **Required Experience:** {min_overall_experience} years")
    st.write(f"🔹 **Match Percentage:** {overall_match:.2f}")

    # Plotting
    st.subheader("📊 Skill & Experience Match Overview")
    fig, ax = plt.subplots()
    ax.barh(required_skills, final_scores, color='mediumseagreen')
    ax.set_xlabel("Final Match Score")
    ax.set_xlim([0, 1])
    ax.invert_yaxis()
    st.pyplot(fig)

elif not skills_input or not experience_input or not overall_experience_required:
    st.info("Enter the required skills, experience levels, and overall job experience.")
else:
    st.info("Upload a resume to begin.")