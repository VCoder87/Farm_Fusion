from flask import Flask, render_template, request
import joblib

app = Flask(__name__)

model = joblib.load('gradient_boost_model.pkl')
le_crop = joblib.load('le_crop.pkl')
le_region = joblib.load('le_region.pkl')
le_intercrop = joblib.load('le_intercrop.pkl')

@app.route('/', methods=['GET', 'POST'])
def index():
    crops = le_crop.classes_
    regions = le_region.classes_
    recommended_intercrop = None

    if request.method == 'POST':
        try:
            crop = request.form['crop']
            region = request.form['region']
            area_available = float(request.form['area_available'])
            temperature = float(request.form['temperature'])
            rainfall = float(request.form['rainfall'])
            ph_level = float(request.form['ph_level'])

            crop_enc = le_crop.transform([crop])[0]
            region_enc = le_region.transform([region])[0]

            features = [[crop_enc, region_enc, area_available, temperature, rainfall, ph_level]]
            pred_enc = model.predict(features)[0]
            recommended_intercrop = le_intercrop.inverse_transform([pred_enc])[0]

        except Exception as e:
            recommended_intercrop = f"Error: {str(e)}"

    return render_template('index.html', crops=crops, regions=regions, recommendation=recommended_intercrop)

if __name__ == '__main__':
    app.run(debug=True,port=5003)
