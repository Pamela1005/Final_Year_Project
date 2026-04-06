import os, json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import PyPDF2, docx, spacy, numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "replace-this-with-a-strong-key")
app.config["UPLOAD_FOLDER"] = "uploads"

def log_activity(user_email, action, details=""):
    log_file = "tracker.json"
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                logs = json.load(f)
        except:
            pass
    logs.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user_email or "Anonymous",
        "action": action,
        "details": details
    })
    # Keep only last 100 logs to avoid bloating
    if len(logs) > 100:
        logs = logs[-100:]
    with open(log_file, "w") as f:
        json.dump(logs, f, indent=4)

# Initialize Supabase Client
url = os.getenv("SUPABASE_URL", "")
key = os.getenv("SUPABASE_KEY", "")
supabase: Client = create_client(url, key) if url and key else None

if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

try:
    nlp = spacy.load("en_core_web_sm")
except:
    print("Download spacy model: python -m spacy download en_core_web_sm")

# Exhaustive skill mapping across practically every conceivable field
SKILL_CAREER_MAP = {
    # Tech & Software
    "python": "Software Developer / Data Scientist", "java": "Software Developer", "javascript": "Web Developer",
    "react": "Web Developer", "angular": "Web Developer", "nodejs": "Web Developer", "c++": "Software Developer",
    "c#": "Software Developer", "php": "Web Developer", "html": "Web Developer", "css": "Web Developer",
    "machine learning": "Data Scientist", "deep learning": "Data Scientist", "tensorflow": "Data Scientist",
    "pytorch": "Data Scientist", "data analysis": "Data Analyst", "sql": "Data Analyst", "tableau": "Data Analyst",
    "power bi": "Data Analyst", "excel": "Data Analyst", "cybersecurity": "Cybersecurity Specialist",
    "network": "Network Engineer", "cloud": "Cloud Engineer", "aws": "Cloud Engineer", "azure": "Cloud Engineer",
    "devops": "DevOps Engineer", "docker": "DevOps Engineer", "kubernetes": "DevOps Engineer",
    
    # Design, Media & Marketing
    "design": "UI/UX Designer", "figma": "UI/UX Designer", "ui": "UI/UX Designer", "ux": "UI/UX Designer",
    "adobe xd": "UI/UX Designer", "photoshop": "Graphic Designer", "illustrator": "Graphic Designer",
    "graphic design": "Graphic Designer", "marketing": "Digital Marketing Specialist", "digital marketing": "Digital Marketing Specialist",
    "seo": "Digital Marketing Specialist", "social media": "Digital Marketing Specialist", "content marketing": "Digital Marketing Specialist",
    "writing": "Content Writer / Editor", "content writing": "Content Writer / Editor", "editing": "Content Writer / Editor",
    "copywriting": "Content Writer / Editor", "video editing": "Media Professional", "journalism": "Media Professional",
    "broadcasting": "Media Professional", "premiere pro": "Media Professional", "photography": "Media Professional",
    "public relations": "PR Specialist", "communications": "PR Specialist",
    
    # Business, Management & HR
    "leadership": "Project Manager", "project management": "Project Manager", "agile": "Project Manager", "scrum": "Project Manager",
    "operations": "Operations Manager", "supply chain": "Supply Chain Analyst", "logistics": "Supply Chain Analyst", 
    "inventory management": "Operations Manager", "procurement": "Supply Chain Analyst",
    "hr": "HR Specialist", "human resources": "HR Specialist", "recruitment": "HR Specialist",
    "talent acquisition": "HR Specialist", "onboarding": "HR Specialist", "payroll": "HR Specialist", "employee relations": "HR Specialist",
    
    # Sales, Support & Real Estate
    "sales": "Sales Professional", "customer service": "Customer Success Manager", "cold calling": "Sales Professional",
    "crm": "Sales Professional", "b2b": "Sales Professional", "account management": "Sales Professional",
    "customer support": "Customer Success Manager", "customer success": "Customer Success Manager",
    "real estate": "Real Estate Agent", "property management": "Real Estate Agent", "leasing": "Real Estate Agent", "mortgage": "Real Estate Agent",
    
    # Healthcare, Medicine & Social Services
    "nursing": "Healthcare Professional", "medicine": "Healthcare Professional", "patient care": "Healthcare Professional",
    "surgery": "Healthcare Professional", "clinical": "Healthcare Professional", "healthcare": "Healthcare Professional",
    "pharmacy": "Pharmacist", "dentistry": "Dentist", "physical therapy": "Physical Therapist",
    "counseling": "Social Worker / Counselor", "social work": "Social Worker / Counselor", "therapy": "Social Worker / Counselor",
    "psychology": "Social Worker / Counselor", "child care": "Social Worker / Counselor",
    
    # Science, Research & Academia
    "biology": "Research Scientist", "chemistry": "Research Scientist", "lab research": "Research Scientist",
    "genetics": "Research Scientist", "biochemistry": "Research Scientist", "clinical trials": "Research Scientist",
    "physics": "Research Scientist", "mathematics": "Academic / Researcher", "research": "Academic / Researcher",
    
    # Education & Training
    "teaching": "Teacher / Educator", "tutoring": "Teacher / Educator", "curriculum development": "Teacher / Educator",
    "lesson planning": "Teacher / Educator", "classroom management": "Teacher / Educator", "e-learning": "Teacher / Educator",
    "instructional design": "Teacher / Educator", "training": "Corporate Trainer",
    
    # Legal & Law Enforcement
    "litigation": "Legal Professional", "legal research": "Legal Professional", "contract drafting": "Legal Professional",
    "corporate law": "Legal Professional", "compliance": "Legal Professional", "paralegal": "Legal Professional",
    "defense": "Military / Law Enforcement", "police": "Military / Law Enforcement", "security": "Military / Law Enforcement",
    "forensics": "Military / Law Enforcement",
    
    # Finance, Accounting & Economics
    "accounting": "Financial Analyst / Accountant", "finance": "Financial Analyst / Accountant", "investment": "Financial Analyst / Accountant",
    "bookkeeping": "Financial Analyst / Accountant", "taxation": "Financial Analyst / Accountant", "auditing": "Financial Analyst / Accountant",
    "financial modeling": "Financial Analyst / Accountant", "bloomberg": "Financial Analyst / Accountant", "economics": "Economist",
    
    # Engineering (Traditional) & Construction
    "civil engineering": "Civil Engineer", "autocad": "Civil Engineer", "structural analysis": "Civil Engineer",
    "mechanical engineering": "Mechanical Engineer", "solidworks": "Mechanical Engineer", "CAD": "Mechanical Engineer",
    "electrical engineering": "Electrical Engineer", "circuit design": "Electrical Engineer", "construction management": "Construction Professional",
    
    # Trades, Vocational & Agriculture
    "plumbing": "Skilled Trades Professional", "welding": "Skilled Trades Professional", "carpentry": "Skilled Trades Professional",
    "electrical wiring": "Skilled Trades Professional", "machining": "Manufacturing Professional", "assembly": "Manufacturing Professional",
    "farming": "Agriculture Professional", "agronomy": "Agriculture Professional", "veterinary": "Agriculture Professional",
    
    # Hospitality, Tourism & Transportation
    "cooking": "Hospitality / Culinary", "culinary": "Hospitality / Culinary", "hotel management": "Hospitality / Culinary",
    "event planning": "Hospitality / Culinary", "tourism": "Hospitality / Culinary", "catering": "Hospitality / Culinary",
    "transit": "Transportation / Logistics", "truck driving": "Transportation / Logistics", "piloting": "Transportation / Logistics",
    "aviation": "Transportation / Logistics", "maritime": "Transportation / Logistics",
    
    # Fitness, Sports & Arts
    "personal training": "Fitness / Sports Professional", "coaching": "Fitness / Sports Professional", "nutrition": "Fitness / Sports Professional",
    "acting": "Performing Arts", "music production": "Performing Arts", "dancing": "Performing Arts", "painting": "Visual Arts",
    
    # High School Subjects & Extracurriculars (Class 10, 11, 12)
    "calculus": "Academic / Researcher", "algebra": "Academic / Researcher", "geometry": "Academic / Researcher",
    "robotics": "Software Developer / Data Scientist", "coding club": "Software Developer", "science fair": "Research Scientist",
    "ap biology": "Research Scientist", "ap chemistry": "Research Scientist", "ap physics": "Research Scientist", 
    "astronomy": "Research Scientist", "history": "Academic / Researcher", "geography": "Academic / Researcher", 
    "political science": "Legal Professional", "debate": "Legal Professional", "model un": "Legal Professional", 
    "speech": "PR Specialist", "creative writing": "Content Writer / Editor", "literature": "Content Writer / Editor", 
    "journalism club": "Media Professional", "yearbook": "Media Professional", "school newspaper": "Media Professional", 
    "art club": "Visual Arts", "drama club": "Performing Arts", "choir": "Performing Arts", "band": "Performing Arts",
    "economics": "Economist", "business studies": "Financial Analyst / Accountant", "student council": "Project Manager", 
    "volunteer": "Social Worker / Counselor", "community service": "Social Worker / Counselor", "peer tutoring": "Teacher / Educator", 
    "athletics": "Fitness / Sports Professional", "varsity": "Fitness / Sports Professional", "sports": "Fitness / Sports Professional",
    "football": "Fitness / Sports Professional", "soccer": "Fitness / Sports Professional", "basketball": "Fitness / Sports Professional", 
    "cricket": "Fitness / Sports Professional", "tennis": "Fitness / Sports Professional", "swimming": "Fitness / Sports Professional",
    "volleyball": "Fitness / Sports Professional", "baseball": "Fitness / Sports Professional", "gymnastics": "Fitness / Sports Professional",
    "track and field": "Fitness / Sports Professional", "badminton": "Fitness / Sports Professional", "table tennis": "Fitness / Sports Professional"
}

COURSE_MAP = {
    # Tech
    "Software Developer / Data Scientist": ["Python for Data Science", "Machine Learning A-Z", "Data Structures & Algorithms"],
    "Web Developer": ["React Fundamentals", "JavaScript Mastery", "Full Stack Development"],
    "Data Scientist": ["Machine Learning Advanced", "Deep Learning with TensorFlow", "NLP Basics"],
    "Data Analyst": ["Data Analysis with Python", "SQL Bootcamp", "Tableau Desktop Specialist"],
    "UI/UX Designer": ["UI Design Fundamentals", "Figma Masterclass", "User Research & Testing"],
    "Graphic Designer": ["Adobe Creative Cloud Masterclass", "Graphic Design Theory"],
    "Cybersecurity Specialist": ["Ethical Hacking", "Network Security", "CISSP Prep"],
    "Cloud Engineer": ["AWS Solutions Architect", "Azure Fundamentals", "Cloud Security"],
    "DevOps Engineer": ["Docker & Kubernetes: The Practical Guide", "DevOps Bootcamp"],
    
    # Business, Marketing & Legal
    "Project Manager": ["Project Management Professional (PMP)", "Agile Scrum Master"],
    "Digital Marketing Specialist": ["Google Digital Marketing Course", "SEO Fundamentals", "Social Media Strategy"],
    "PR Specialist": ["Public Relations Foundations", "Crisis Communication"],
    "Operations Manager": ["Operations Management Foundations", "Supply Chain Logistics"],
    "Supply Chain Analyst": ["Supply Chain Management Principles", "Inventory Analytics"],
    "HR Specialist": ["Human Resources Foundations", "Technical Recruiting", "Organizational Behavior"],
    "Sales Professional": ["Salesforce Administrator", "B2B Sales Masterclass"],
    "Customer Success Manager": ["Customer Success Management", "Conflict Resolution Basics"],
    "Content Writer / Editor": ["Creative Writing", "Content Marketing Basics", "Technical Writing"],
    "Legal Professional": ["Introduction to Corporate Law", "Legal Research and Writing", "Contracts and Negotiation"],
    
    # Healthcare, Science & Education
    "Healthcare Professional": ["Medical Terminology Basics", "Healthcare Management", "Patient Care Fundamentals"],
    "Pharmacist": ["Pharmacology Fundamentals", "Clinical Trials Management"],
    "Dentist": ["Advanced Dentistry Practices", "Dental Practice Management"],
    "Physical Therapist": ["Kinesiology Basics", "Rehabilitation Strategies"],
    "Social Worker / Counselor": ["Psychological Counseling", "Child Abuse Prevention"],
    "Research Scientist": ["Clinical Research Protocols", "Data Analysis for Life Sciences"],
    "Academic / Researcher": ["Academic Writing & Publishing", "Statistical Methods"],
    "Teacher / Educator": ["Instructional Design Models", "Classroom Management and Leadership", "e-Learning Tools"],
    "Corporate Trainer": ["Train the Trainer Masterclass", "Corporate Learning Strategies"],
    
    # Finance & Engineering
    "Financial Analyst / Accountant": ["Financial Modeling & Valuation", "Accounting Basics", "Corporate Finance"],
    "Economist": ["Macroeconomics", "Econometrics Using Python"],
    "Civil Engineer": ["AutoCAD 2024 Masterclass", "Structural Engineering Foundations"],
    "Mechanical Engineer": ["SolidWorks Basics", "Thermodynamics & Fluid Mechanics"],
    "Electrical Engineer": ["Circuit Design and Analysis", "Power Systems Basics"],
    "Construction Professional": ["Construction Management Foundations", "OSHA Safety Training"],
    
    # Trades, Hospitality, Misc
    "Skilled Trades Professional": ["Basic Electrical Wiring", "Plumbing Basics", "Welding Certification Prep"],
    "Manufacturing Professional": ["Six Sigma Yellow Belt", "Industrial Safety Protocols"],
    "Agriculture Professional": ["Modern Agronomy", "Sustainable Farming Practices"],
    "Hospitality / Culinary": ["Culinary Arts Fundamentals", "Hotel Operations Management", "Event Planning 101"],
    "Transportation / Logistics": ["Logistics and Supply Chain Management", "Fleet Operations Basics"],
    "Real Estate Agent": ["Real Estate License Prep", "Property Management Fundamentals"],
    "Military / Law Enforcement": ["Criminal Justice Basics", "Security & Risk Management"],
    "Fitness / Sports Professional": ["Certified Personal Trainer Prep", "Sports Nutrition Foundation"],
    "Media Professional": ["Video Editing with Premiere Pro", "Digital Journalism Basics"],
    "Performing Arts": ["Acting Masterclass", "Music Production using Ableton"],
    "Visual Arts": ["Drawing and Painting Fundamentals", "Digital Art Studio"]
}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"pdf", "docx"}

def extract_text(filepath):
    text = ""
    if filepath.lower().endswith(".pdf"):
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
    elif filepath.lower().endswith(".docx"):
        doc = docx.Document(filepath)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    return text.lower()

def nlp_tokenize_and_extract_skills(text):
    """Extract skills using both keyword matching and NLP"""
    skills = {}
    
    # Direct keyword matching (case-insensitive)
    for skill_keyword in SKILL_CAREER_MAP.keys():
        count = text.count(skill_keyword)
        if count > 0:
            skills[skill_keyword] = count
    
    # NLP-based extraction
    try:
        doc = nlp(text)
        for token in doc:
            word = token.lemma_.lower()
            if word in SKILL_CAREER_MAP and word not in skills:
                skills[word] = 1
    except:
        pass
    
    # Return top skills (sorted by frequency)
    return dict(sorted(skills.items(), key=lambda x: x[1], reverse=True)[:10])

def ml_predict_career(text):
    """Predict career based on ML model"""
    texts, labels = [], []
    for skill, career in SKILL_CAREER_MAP.items():
        texts.append(f"I have experience in {skill}.")
        labels.append(career)
        texts.append(f"My skills include {skill}.")
        labels.append(career)
    
    vectorizer = TfidfVectorizer(max_features=1000, stop_words="english")
    X = vectorizer.fit_transform(texts)
    y = np.array(labels)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    prediction = model.predict(vectorizer.transform([text]))[0]
    return prediction

def suggest_courses(career):
    return COURSE_MAP.get(career, ["Explore online courses on Udemy, Coursera, or LinkedIn Learning"])

def job_recommendations(career, skills):
    # Match profiles according to both career role and top skills found in resume
    skill_keywords = "+".join([skill.replace(" ", "+") for skill in list(skills.keys())[:3]])
    career_query = career.replace(" / ", "+").replace("/", "+").replace(" ", "+")
    
    combined_query = f"{career_query}+{skill_keywords}" if skill_keywords else career_query
    naukri_query = career.replace(" / ", "-").replace("/", "-").replace(" ", "-").lower()

    return {
        "LinkedIn (Matched Skills Profile)": f"https://www.linkedin.com/jobs/search/?keywords={combined_query}",
        "Naukri.com (Relevant Roles)": f"https://www.naukri.com/{naukri_query}-jobs",
        "Indeed (Skills & Role Match)": f"https://www.indeed.com/jobs?q={combined_query}"
    }

@app.route("/")
def index():
     return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", user_email=session.get("user_email"), username=session.get("username", session.get("user_email", "").split("@")[0] if session.get("user_email") else ""))

@app.route("/create_resume")
def create_resume():
    return render_template("create_resume.html")

@app.route("/generate_resume", methods=["POST"])
def generate_resume():
    data = request.form.to_dict()
    log_activity(session.get("user_email"), "Generated Quick Resume", f"Level: {data.get('education_level', 'Unknown')}")
    
    # Automatically analyze the generated resume text
    combined_text = " ".join(str(v) for v in data.values()).lower()
    skills = nlp_tokenize_and_extract_skills(combined_text)
    
    analysis = {}
    if skills:
        career = ml_predict_career(combined_text)
        courses = suggest_courses(career)
        job_links = job_recommendations(career, skills)
        sorted_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)
        expert_skills = [skill.title() for skill, count in sorted_skills[:3]]
        
        analysis = {
            "prediction": career,
            "expert_in": expert_skills,
            "charts": skills,
            "courses": courses,
            "job_links": job_links
        }
        
    return render_template("resume_template.html", **data, analysis=analysis)

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/signin", methods=["POST"])
def signin():
    email = request.form.get("email", "")
    password = request.form.get("password", "")
    
    if not supabase:
        flash("Supabase is not configured. Check your .env file.", "error")
        return redirect(url_for("login"))

    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response.user:
            session["user_email"] = response.user.email
            session["username"] = response.user.user_metadata.get("username", email.split("@")[0]) if hasattr(response.user, 'user_metadata') and response.user.user_metadata else email.split("@")[0]
            log_activity(response.user.email, "Logged In")
            
            # Check if admin
            admin_email = os.getenv("ADMIN_EMAIL", "admin@admin.com")
            if email == admin_email:
                return redirect(url_for("admin_dashboard"))
                
            return redirect(url_for("dashboard"))
    except Exception as e:
        flash(f"Invalid email or password", "error")
        
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear()
    try:
        supabase.auth.sign_out()
    except:
        pass
    return redirect(url_for("login"))

@app.route("/signup", methods=["POST"])
def signup():
    username = request.form.get("username", "")
    email = request.form.get("email", "")
    password = request.form.get("password", "")
    
    if not supabase:
        flash("Supabase is not configured. Check your .env file.", "error")
        return redirect(url_for("login"))

    if not email or not password:
        flash("All fields required", "error")
        return redirect(url_for("login"))
        
    try:
        response = supabase.auth.sign_up({
            "email": email, 
            "password": password,
            "options": {"data": {"username": username}}
        })
        # If successfully submitted
        if response.user:
            # Handle Supabase scenario where user already exists and confirm_email is true
            if hasattr(response.user, 'identities') and response.user.identities is not None and len(response.user.identities) == 0:
                raise Exception("User already registered")

            session["user_email"] = response.user.email
            session["username"] = username if username else response.user.email.split("@")[0]
            log_activity(response.user.email, f"User Registered: {username}")
            flash("Signup successful!", "success")
            
            admin_email = os.getenv("ADMIN_EMAIL", "admin@admin.com")
            if email == admin_email:
                return redirect(url_for("admin_dashboard"))
                
            return redirect(url_for("dashboard"))
        else:
            flash("Signup failed. Please try again.", "error")
    except Exception as e:
        # Check if user already exists
        if "already registered" in str(e).lower() or "already exists" in str(e).lower():
            try:
                # Attempt to log them in automatically
                login_resp = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if login_resp.user:
                    session["user_email"] = login_resp.user.email
                    session["username"] = login_resp.user.user_metadata.get("username", email.split("@")[0]) if hasattr(login_resp.user, 'user_metadata') and login_resp.user.user_metadata else email.split("@")[0]
                    log_activity(login_resp.user.email, "Logged In via Signup Form (Account Existed)")
                    
                    admin_email = os.getenv("ADMIN_EMAIL", "admin@admin.com")
                    if email == admin_email:
                        return redirect(url_for("admin_dashboard"))
                    return redirect(url_for("dashboard"))
            except Exception as login_e:
                flash("Account already exists. Please log in with your correct password.", "error")
        else:
            flash(f"Error during signup: {e}", "error")
            
    return redirect(url_for("login"))

@app.route("/admin_dashboard")
def admin_dashboard():
    admin_email = os.getenv("ADMIN_EMAIL", "admin@admin.com")
    if session.get("user_email") != admin_email:
        flash("Unauthorized Access", "error")
        return redirect(url_for("login"))
        
    log_file = "tracker.json"
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                logs = json.load(f)
        except:
            pass
            
    # Reverse so newest is first
    logs.reverse()
    return render_template("admin_dashboard.html", logs=logs)

@app.route("/upload_resume", methods=["POST"])
def upload_resume():
    log_activity(session.get("user_email"), "Uploaded Resume PDF/Docx")
    if "resume" not in request.files:
        return render_template("dashboard.html", error="No file selected")
    file = request.files["resume"]
    if file.filename == "" or not allowed_file(file.filename):
        return render_template("dashboard.html", error="Please upload a PDF or DOCX file")
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)
    
    # Extract and analyze
    text = extract_text(filepath)
    skills = nlp_tokenize_and_extract_skills(text)
    
    if not skills:
        return render_template(
            "dashboard.html",
            user_email=session.get("user_email"),
            username=session.get("username", session.get("user_email", "").split("@")[0] if session.get("user_email") else ""),
            error="No specific career keywords were found in this document (it might be an image-based PDF or simply missing standard keywords). Here is a general dashboard instead!",
            prediction="General Explorer",
            expert_in=["Discovery & Foundations"],
            courses=["Explore online courses on LinkedIn Learning", "General Career Foundations"],
            job_links={"LinkedIn Jobs (General)": "https://www.linkedin.com/jobs"}
        )
    
    career = ml_predict_career(text)
    courses = suggest_courses(career)
    job_links = job_recommendations(career, skills)
    
    # Identify expertise based on top mentioned skills
    # Consider them an expert in their top 3 most mentioned skills rather than just the absolute max
    sorted_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)
    expert_skills = [skill.title() for skill, count in sorted_skills[:3]]
    
    return render_template(
        "dashboard.html",
        prediction=career,
        expert_in=expert_skills,
        charts=skills,
        courses=courses,
        job_links=job_links
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)