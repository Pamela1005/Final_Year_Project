# Career Counseling System 🚀

An AI-powered career dashboard that analyzes resumes (PDF/DOCX) using SpaCy and Scikit-learn, predicts career paths, and suggests relevant courses and job opportunities.

## 🌐 Live Deployment

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Pamela1005/Final_Year_Project)

### How to get your live link:
1.  **Click the "Deploy to Render" button above.**
2.  Log in to Render and name your service.
3.  **Crucial Step**: In the "Environment Variables" section, add your `SUPABASE_URL` and `SUPABASE_KEY` from your local `.env` file.
4.  Once the build is complete, Render will provide your unique **Live URL**.

---

## 🛠 Features
- **Resume Parsing**: Extract text from PDF and DOCX files.
- **Skill Extraction**: Uses NLP (SpaCy) to identify key professional skills.
- **Career Prediction**: Machine Learning model (Random Forest) for career path mapping.
- **Dashboard**: Interactive user and admin dashboards with activity tracking.
- **Integrations**: Connected to Supabase for authentication and profile management.

## 📦 Local Setup
1. `pip install -r requirements.txt`
2. Create a `.env` file with your credentials.
3. `python app.py`
