import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pickle

def train_model():
    data = pd.read_csv("dataset.csv")

    X = data.drop("Career", axis=1)
    y = data["Career"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
5
    model = RandomForestClassifier()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    pickle.dump(model, open("model.pkl", "wb"))

    return round(accuracy * 100, 2)