import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import GradientBoostingClassifier
import joblib

df = pd.read_excel('Intercropping.xlsx')

le_crop = LabelEncoder()
le_region = LabelEncoder()
le_intercrop = LabelEncoder()

df['crop_enc'] = le_crop.fit_transform(df['crop'])
df['region_enc'] = le_region.fit_transform(df['region'])
df['intercrop_enc'] = le_intercrop.fit_transform(df['intercrop'])

X = df[['crop_enc', 'region_enc', 'area_available', 'temperature', 'rainfall', 'ph_level']]
y = df['intercrop_enc']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = GradientBoostingClassifier(random_state=42)
model.fit(X_train, y_train)

joblib.dump(model, 'gradient_boost_model.pkl')
joblib.dump(le_crop, 'le_crop.pkl')
joblib.dump(le_region, 'le_region.pkl')
joblib.dump(le_intercrop, 'le_intercrop.pkl')

print("Training complete and model saved.")
