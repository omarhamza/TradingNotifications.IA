import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from xgboost import XGBClassifier
from config import features

def train_model_from_csv(csv_file):
    df = pd.read_csv(csv_file, parse_dates=['timestamp'])
    df.set_index('timestamp', inplace=True)
    df['future_return'] = df['close'].shift(-3) / df['close'] - 1
    df['target'] = (df['future_return'] > 0.01).astype(int)
    df.dropna(subset=features + ['target'], inplace=True)

    X = df[features]
    y = df['target']

    X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=False, test_size=0.2)

    model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print("📊 Rapport de performance :")
    print(classification_report(y_test, y_pred))

    return model, df