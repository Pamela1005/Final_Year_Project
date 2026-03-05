import spacy
import PyPDF2

nlp = spacy.load("en_core_web_sm")

def extract_text(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def extract_skills(text):
    keywords = ["python", "machine learning", "data analysis",
                "marketing", "management", "communication"]

    doc = nlp(text)
    skills = []

    for token in doc:
        if token.text.lower() in keywords:
            skills.append(token.text.lower())

    return list(set(skills))