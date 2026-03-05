from flask import Flask, request, render_template_string
import pandas as pd
import random
import spacy
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
nlp = spacy.load("en_core_web_sm")

# ------------------------------
# Create Hypothetical Dataset
# ------------------------------

careers = ["Data Scientist","Web Developer","Cyber Security","AI Engineer","Business Analyst"]

data = []

for i in range(500):

    python = random.randint(0,10)
    math = random.randint(0,10)
    communication = random.randint(0,10)
    logic = random.randint(0,10)

    score = python + math + logic

    if score > 25:
        career = "AI Engineer"
    elif python > 6:
        career = "Data Scientist"
    elif communication > 7:
        career = "Business Analyst"
    elif logic > 6:
        career = "Cyber Security"
    else:
        career = "Web Developer"

    data.append([python,math,communication,logic,career])

df = pd.DataFrame(data,columns=["python","math","communication","logic","career"])

X = df[["python","math","communication","logic"]]
y = df["career"]

# ------------------------------
# Train ML Model
# ------------------------------

model = RandomForestClassifier()
model.fit(X,y)

accuracy = model.score(X,y)

# ------------------------------
# Homepage
# ------------------------------

home_page = """

<h1>AI Career Recommendation System</h1>

<h2>Enter Your Skills</h2>

<form action="/predict" method="post">

Python Skill (0-10)<br>
<input name="python"><br>

Math Skill (0-10)<br>
<input name="math"><br>

Communication Skill (0-10)<br>
<input name="communication"><br>

Logic Skill (0-10)<br>
<input name="logic"><br><br>

<button type="submit">Predict Career</button>

</form>

<br>

<h3>Upload Resume</h3>

<form action="/resume" method="post" enctype="multipart/form-data">

<input type="file" name="resume">

<button type="submit">Analyze Resume</button>

</form>

<br>

<a href="/admin">Admin Dashboard</a>

"""

# ------------------------------
# Career Prediction
# ------------------------------

@app.route("/")
def home():
    return render_template_string(home_page)

@app.route("/predict",methods=["POST"])
def predict():

    python = int(request.form["python"])
    math = int(request.form["math"])
    communication = int(request.form["communication"])
    logic = int(request.form["logic"])

    prediction = model.predict([[python,math,communication,logic]])[0]

    # Create Chart

    skills = [python,math,communication,logic]

    labels = ["Python","Math","Communication","Logic"]

    plt.bar(labels,skills)

    plt.title("Skill Analysis")

    chart_path = "chart.png"

    plt.savefig(chart_path)

    plt.close()

    return f"""

    <h1>Recommended Career: {prediction}</h1>

    <h3>Model Accuracy: {accuracy}</h3>

    <img src="/chart">

    <br><br>

    <a href="/">Back</a>

    """

# ------------------------------
# Display Chart
# ------------------------------

@app.route("/chart")
def chart():
    from flask import send_file
    return send_file("chart.png", mimetype="image/png")

# ------------------------------
# Resume NLP Analysis
# ------------------------------

@app.route("/resume",methods=["POST"])
def resume():

    file = request.files["resume"]

    text = file.read().decode("utf-8")

    doc = nlp(text)

    skills = []

    skill_keywords = ["python","machine learning","data","ai","sql","analysis","security"]

    for token in doc:
        if token.text.lower() in skill_keywords:
            skills.append(token.text)

    return f"""

    <h1>Resume Skill Extraction</h1>

    Skills Found: {set(skills)}

    <br><br>

    <a href="/">Back</a>

    """

# ------------------------------
# Admin Dashboard
# ------------------------------

@app.route("/admin")
def admin():

    return f"""

    <h1>Admin Dashboard</h1>

    <h3>Total Dataset Records: {len(df)}</h3>

    <h3>Model Accuracy: {accuracy}</h3>

    <h3>Careers Available:</h3>

    {careers}

    <br><br>

    <a href="/">Back</a>

    """

# ------------------------------

@app.route("/resume", methods=["POST"])
def resume():

    file = request.files["resume"]

    text = file.read().decode("utf-8")

    skills = []

    keywords = ["python","machine learning","data","ai","sql","analysis","security"]

    for word in keywords:
        if word in text.lower():
            skills.append(word)

    return f"""

    <h1>Resume Skill Extraction</h1>

    <h3>Detected Skills:</h3>

    {skills}

    <br><br>

    <a href="/dashboard">Back to Dashboard</a>

    """

if __name__ == "__main__":
    app.run(debug=True)