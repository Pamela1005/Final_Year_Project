import pandas as pd
import numpy as np

np.random.seed(42)

n = 600  # more than 500 students

data = {
    "math_score": np.random.randint(40, 100, n),
    "programming_skill": np.random.randint(1, 10, n),
    "communication_skill": np.random.randint(1, 10, n),
    "interest_tech": np.random.randint(1, 10, n),
    "interest_management": np.random.randint(1, 10, n),
    "personality_score": np.random.randint(1, 10, n)
}

df = pd.DataFrame(data)

def assign_career(row):
    if row["programming_skill"] > 7 and row["interest_tech"] > 7:
        return "Software Engineer"
    elif row["communication_skill"] > 7 and row["interest_management"] > 7:
        return "Business Analyst"
    elif row["math_score"] > 85:
        return "Data Scientist"
    else:
        return "General Graduate Career"

df["career"] = df.apply(assign_career, axis=1)

df.to_csv("dataset.csv", index=False)

print("Dataset generated successfully with 600 students.")
