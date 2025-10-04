# CROP RECOMMENDATION SYSTEM - WEB APPLICATION VERSION
# Compatible with Python 3.12.9

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
import joblib
import warnings
import os
import json
from flask import Flask, render_template, request, jsonify
import threading
import webbrowser
from datetime import datetime

warnings.filterwarnings('ignore')

class CropRecommendationWebApp:
    def __init__(self):
        self.models = {}
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_names = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
        self.best_model = None
        self.best_accuracy = 0
        self.data = None
        self.model_results = {}
        self.app = Flask(__name__)
        self.setup_routes()
    
    def create_sample_dataset(self):
        """Create a sample dataset if CSV is not available"""
        print("📁 Creating sample dataset...")
        
        # Sample data based on typical crop requirements
        crops = ['rice', 'maize', 'chickpea', 'kidneybeans', 'pigeonpeas', 'mothbeans', 
                'mungbean', 'blackgram', 'lentil', 'pomegranate', 'banana', 'mango', 
                'grapes', 'watermelon', 'muskmelon', 'apple', 'orange', 'papaya', 
                'coconut', 'cotton', 'jute', 'coffee']
        
        np.random.seed(42)
        data = []
        
        # Generate synthetic data for each crop with realistic ranges
        crop_profiles = {
            'rice': {'N': (80, 120), 'P': (40, 60), 'K': (40, 60), 'temp': (20, 30), 'humidity': (80, 95), 'ph': (5.5, 7.0), 'rainfall': (200, 300)},
            'maize': {'N': (80, 120), 'P': (40, 60), 'K': (20, 40), 'temp': (18, 27), 'humidity': (55, 75), 'ph': (6.0, 7.5), 'rainfall': (50, 100)},
            'chickpea': {'N': (40, 70), 'P': (60, 85), 'K': (80, 120), 'temp': (15, 25), 'humidity': (10, 40), 'ph': (6.0, 7.5), 'rainfall': (30, 80)},
            'kidneybeans': {'N': (20, 40), 'P': (60, 85), 'K': (20, 40), 'temp': (15, 25), 'humidity': (15, 35), 'ph': (5.5, 7.0), 'rainfall': (30, 60)},
            'banana': {'N': (100, 120), 'P': (75, 100), 'K': (50, 80), 'temp': (25, 35), 'humidity': (75, 85), 'ph': (5.5, 7.0), 'rainfall': (100, 180)},
            'cotton': {'N': (120, 160), 'P': (40, 70), 'K': (70, 120), 'temp': (20, 30), 'humidity': (80, 90), 'ph': (5.8, 8.0), 'rainfall': (50, 100)}
        }
        
        for crop in crops:
            if crop in crop_profiles:
                profile = crop_profiles[crop]
            else:
                # Default profile for crops not specified
                profile = {'N': (40, 100), 'P': (30, 80), 'K': (30, 80), 'temp': (15, 35), 
                          'humidity': (20, 90), 'ph': (5.0, 8.0), 'rainfall': (50, 250)}
            
            # Generate 100 samples per crop
            for _ in range(100):
                sample = {
                    'N': np.random.uniform(*profile['N']),
                    'P': np.random.uniform(*profile['P']),
                    'K': np.random.uniform(*profile['K']),
                    'temperature': np.random.uniform(*profile['temp']),
                    'humidity': np.random.uniform(*profile['humidity']),
                    'ph': np.random.uniform(*profile['ph']),
                    'rainfall': np.random.uniform(*profile['rainfall']),
                    'label': crop
                }
                data.append(sample)
        
        self.data = pd.DataFrame(data)
        print(f"✅ Sample dataset created with {len(self.data)} records and {len(crops)} crops")
        return self.data
    
    def load_data(self, file_path='Crop_recommendation.csv'):
        """Load the crop recommendation dataset or create sample data"""
        try:
            if os.path.exists(file_path):
                self.data = pd.read_csv(file_path)
                print(f"✅ Dataset loaded from {file_path}")
            else:
                print(f"⚠️  Dataset file '{file_path}' not found. Creating sample dataset...")
                self.create_sample_dataset()
            
            print(f"📊 Dataset shape: {self.data.shape}")
            print(f"🌾 Crops available: {sorted(self.data['label'].unique())}")
            return self.data
            
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            print("📁 Creating sample dataset as fallback...")
            return self.create_sample_dataset()
    
    def preprocess_data(self):
        """Preprocess the data for training"""
        if self.data is None:
            print("Please load data first!")
            return
        
        print("\n⚙️  Preprocessing data...")
        
        # Separate features and target
        X = self.data.drop('label', axis=1)
        y = self.data['label']
        
        # Encode target variable
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        # Scale the features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Store preprocessed data
        self.X_train, self.X_test = X_train_scaled, X_test_scaled
        self.y_train, self.y_test = y_train, y_test
        self.X_train_orig, self.X_test_orig = X_train, X_test
        
        print("✅ Data preprocessing completed!")
        return True
    
    def train_models(self):
        """Train multiple machine learning models"""
        if not hasattr(self, 'X_train'):
            print("Please preprocess data first!")
            return
        
        models_config = {
            'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
            'Gradient Boosting': GradientBoostingClassifier(random_state=42),
            'SVM': SVC(random_state=42, probability=True),
            'KNN': KNeighborsClassifier(n_jobs=-1),
            'Decision Tree': DecisionTreeClassifier(random_state=42),
            'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000, n_jobs=-1)
        }
        
        print("\n🤖 Training models...")
        
        for name, model in models_config.items():
            print(f"Training {name}...")
            model.fit(self.X_train, self.y_train)
            y_pred = model.predict(self.X_test)
            accuracy = accuracy_score(self.y_test, y_pred)
            
            # Cross-validation
            cv_scores = cross_val_score(model, self.X_train, self.y_train, cv=5, n_jobs=-1)
            
            self.model_results[name] = {
                'model': model,
                'accuracy': accuracy,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std()
            }
            
            # Track best model
            if accuracy > self.best_accuracy:
                self.best_accuracy = accuracy
                self.best_model = model
                self.best_model_name = name
        
        print(f"✅ Best model: {self.best_model_name} with accuracy: {self.best_accuracy:.4f}")
        return self.model_results
    
    def predict_crop(self, N, P, K, temperature, humidity, ph, rainfall):
        """Predict suitable crop based on input parameters"""
        if self.best_model is None:
            return None, 0, []
        
        # Prepare input data
        input_data = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
        input_scaled = self.scaler.transform(input_data)
        
        # Make prediction
        prediction_encoded = self.best_model.predict(input_scaled)[0]
        prediction_proba = self.best_model.predict_proba(input_scaled)[0]
        predicted_crop = self.label_encoder.inverse_transform([prediction_encoded])[0]
        confidence = max(prediction_proba) * 100
        
        # Get top 5 predictions
        top_5_indices = np.argsort(prediction_proba)[-5:][::-1]
        top_5_crops = self.label_encoder.inverse_transform(top_5_indices)
        top_5_probabilities = prediction_proba[top_5_indices] * 100
        
        top_5_results = [
            {'crop': crop, 'probability': prob} 
            for crop, prob in zip(top_5_crops, top_5_probabilities)
        ]
        
        return predicted_crop, confidence, top_5_results
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return '''
           <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌾 Crop Recommendation System</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.7/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-LN+7fdVzj6u52u30Kp6M/trliBMCMKTyK833zpbD+pXdCLuTusPj697FH4R/5mcr" crossorigin="anonymous">
    <style>
        * {
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(45deg, #2ecc71, #27ae60);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .tab-content {
            padding: 30px;
        }
        
        .tab-content h2 {
            margin-top: 0;
            margin-bottom: 30px;
            color: #2c3e50;
            text-align: center;
        }
        
        .form-group {
            margin-bottom: 25px;
            width: 100%;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #2c3e50;
            font-size: 16px;
        }
        
        .form-group input {
            width: 100%;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s, box-shadow 0.3s;
            background-color: #fff;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #007bff;
            box-shadow: 0 0 10px rgba(0,123,255,0.3);
        }
        
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }
        
        .predict-btn {
            background: linear-gradient(45deg, #e74c3c, #c0392b);
            color: white;
            padding: 18px 40px;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 20px;
        }
        
        .predict-btn:hover {
            background: linear-gradient(45deg, #c0392b, #e74c3c);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(231,76,60,0.4);
        }
        
        .result-container {
            margin-top: 30px;
            padding: 25px;
            background: linear-gradient(135deg, #74b9ff, #0984e3);
            color: white;
            border-radius: 10px;
            display: none;
        }
        
        .result-main {
            text-align: center;
            margin-bottom: 25px;
        }
        
        .result-main h2 {
            font-size: 2em;
            margin: 10px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .confidence {
            font-size: 1.2em;
            font-weight: bold;
        }
        
        .top-crops {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 20px;
        }
        
        .top-crops h3 {
            margin-top: 0;
            text-align: center;
            margin-bottom: 15px;
        }
        
        .crop-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            margin: 8px 0;
            background: rgba(255,255,255,0.1);
            border-radius: 5px;
        }
        
        .loading {
            text-align: center;
            font-size: 18px;
            color: #666;
            display: none;
            margin: 20px 0;
        }
        
        .graph-container {
            margin: 20px 0;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .status-message {
            text-align: center;
            padding: 20px;
            font-size: 18px;
            color: #666;
        }
        
        /* Mobile responsiveness */
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .tab-content {
                padding: 20px;
            }
            
            .form-grid {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .form-group input {
                padding: 12px;
            }
            
            .predict-btn {
                padding: 15px 30px;
                font-size: 16px;
            }
        }
        
        @media (max-width: 480px) {
            .header {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 1.8em;
            }
            
            .tab-content {
                padding: 15px;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            .form-group input {
                padding: 10px;
                font-size: 14px;
            }
        }
    </style>
</head>
<body>
   
        <header class="d-flex flex-wrap align-items-center justify-content-center justify-content-md-between py-3 mb-4 border-bottom">
        <div class="col-md-3 mb-2 mb-md-0">
            <a href="/" class="d-inline-flex link-body-emphasis text-decoration-none">
                <svg class="bi" width="40" height="32" role="img" aria-label="Bootstrap"><use xlink:href="#bootstrap"></use></svg>
                <span class="fs-4">Farm Fusion</span>
            </a>
        </div>
        <ul class="nav col-12 col-md-auto mb-2 justify-content-center mb-md-0">
            <li><a href="new.html" class="nav-link px-2 text-success">Home</a></li>
            <li><a href="#" class="nav-link px-2 text-success">Features</a></li>
            <li><a href="#" class="nav-link px-2 text-success">FarmCom</a></li>
            <li><a href="#" class="nav-link px-2 text-success">FAQs</a></li>
            <li><a href="#" class="nav-link px-2 link-success">About</a></li>
        </ul>
        <div class="col-md-3 text-end">
            <button type="button" class="btn btn-outline-success me-2">Login</button>
            <button type="button" class="btn btn-success">Sign-up</button>
        </div>
    </header>
        <div class="tab-content">
            <h2>🌱 Enter Soil and Climate Parameters</h2>
            <form id="predictionForm">
                <div class="form-grid">
                    <div class="form-group">
                        <label for="N">🧪 Nitrogen (N) - ppm</label>
                        <input type="number" id="N" name="N" step="0.01" required 
                               placeholder="Enter nitrogen content (0-150)">
                    </div>
                    <div class="form-group">
                        <label for="P">🧪 Phosphorus (P) - ppm</label>
                        <input type="number" id="P" name="P" step="0.01" required 
                               placeholder="Enter phosphorus content (0-150)">
                    </div>
                    <div class="form-group">
                        <label for="K">🧪 Potassium (K) - ppm</label>
                        <input type="number" id="K" name="K" step="0.01" required 
                               placeholder="Enter potassium content (0-200)">
                    </div>
                    <div class="form-group">
                        <label for="temperature">🌡️ Temperature - °C</label>
                        <input type="number" id="temperature" name="temperature" step="0.01" required 
                               placeholder="Enter temperature (8-50)">
                    </div>
                    <div class="form-group">
                        <label for="humidity">💧 Humidity - %</label>
                        <input type="number" id="humidity" name="humidity" step="0.01" required 
                               placeholder="Enter humidity (10-100)">
                    </div>
                    <div class="form-group">
                        <label for="ph">⚗️ pH Level</label>
                        <input type="number" id="ph" name="ph" step="0.01" required 
                               placeholder="Enter pH level (3-10)">
                    </div>
                    <div class="form-group">
                        <label for="rainfall">🌧️ Rainfall - mm</label>
                        <input type="number" id="rainfall" name="rainfall" step="0.01" required 
                               placeholder="Enter rainfall (20-300)">
                    </div>
                </div>
                <button type="submit" class="predict-btn">🔮 Predict Suitable Crop</button>
            </form>
            
            <div class="loading" id="loading">
                ⏳ Analyzing soil and climate data...
            </div>
            
            <div id="result" class="result-container">
                <div class="result-main">
                    <h2 id="predicted-crop">🌾 Recommended Crop</h2>
                    <div class="confidence" id="confidence">🎯 Confidence: 0%</div>
                </div>
                <div class="top-crops">
                    <h3>🏅 Top 5 Recommendations</h3>
                    <div id="top-crops-list"></div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let isModelTrained = false;
        
        document.getElementById('predictionForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
            
            // Get form data
            const formData = new FormData(this);
            const data = {};
            for (let [key, value] of formData.entries()) {
                data[key] = parseFloat(value);
            }
            
            // Send prediction request
            fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('loading').style.display = 'none';
                
                if (data.status === 'success') {
                    // Update result display
                    document.getElementById('predicted-crop').textContent = '🌾 ' + data.predicted_crop.toUpperCase();
                    document.getElementById('confidence').textContent = '🎯 Confidence: ' + data.confidence.toFixed(1) + '%';
                    
                    // Update top 5 crops
                    const topCropsList = document.getElementById('top-crops-list');
                    topCropsList.innerHTML = '';
                    data.top_5.forEach((crop, index) => {
                        const cropItem = document.createElement('div');
                        cropItem.className = 'crop-item';
                        cropItem.innerHTML = `
                            <span>${index + 1}. ${crop.crop.toUpperCase()}</span>
                            <span>${crop.probability.toFixed(1)}%</span>
                        `;
                        topCropsList.appendChild(cropItem);
                    });
                    
                    document.getElementById('result').style.display = 'block';
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => {
                document.getElementById('loading').style.display = 'none';
                alert('Error making prediction');
            });
        });
        
        // Initialize the application
        fetch('/initialize')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    isModelTrained = true;
                    console.log('✅ Model training completed successfully');
                } else {
                    console.error('❌ Model training failed:', data.message);
                }
            });
    </script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.7/dist/js/bootstrap.bundle.min.js" integrity="sha384-ndDqU0Gzau9qJ1lfW4pNLlhNTkCfHzAVBReH9diLlhNTkCLuTusPj697FH4R/5mcr" crossorigin="anonymous"></script>
 <footer class="d-flex flex-wrap justify-content-between align-items-center py-3 my-4 border-top">
        <div class="col-md-4 d-flex align-items-center">
            <a href="/" class="mb-3 me-2 mb-md-0 text-body-secondary text-decoration-none lh-1" aria-label="Bootstrap">
                <svg class="bi" width="30" height="24" aria-hidden="true"><use xlink:href="#bootstrap"></use></svg>
            </a>
            <span class="mb-3 mb-md-0 text-body-secondary">© 2025 Farm Fusion, Inc</span>
        </div>
        <ul class="nav col-md-4 justify-content-end list-unstyled d-flex">
            <li class="ms-3"><a class="text-body-secondary" href="#" aria-label="Instagram"><svg class="bi" width="24" height="24" aria-hidden="true"><use xlink:href="#instagram"></use></svg></a></li>
            <li class="ms-3"><a class="text-body-secondary" href="#" aria-label="Facebook"><svg class="bi" width="24" height="24"><use xlink:href="#facebook"></use></svg></a></li>
        </ul>
    </footer>
</body>
</html>
            '''
        
        @self.app.route('/predict', methods=['POST'])
        def predict():
            try:
                data = request.json
                N = data['N']
                P = data['P']
                K = data['K']
                temperature = data['temperature']
                humidity = data['humidity']
                ph = data['ph']
                rainfall = data['rainfall']
                
                predicted_crop, confidence, top_5 = self.predict_crop(
                    N, P, K, temperature, humidity, ph, rainfall
                )
                
                if predicted_crop is None:
                    return jsonify({
                        'status': 'error',
                        'message': 'Model not trained yet. Please wait for initialization to complete.'
                    })
                
                return jsonify({
                    'status': 'success',
                    'predicted_crop': predicted_crop,
                    'confidence': confidence,
                    'top_5': top_5
                })
                
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                })
        
        @self.app.route('/initialize')
        def initialize():
            try:
                # This endpoint triggers the model training process
                if not hasattr(self, 'data') or self.data is None:
                    self.load_data()
                
                if not hasattr(self, 'X_train'):
                    self.preprocess_data()
                
                if not self.model_results:
                    self.train_models()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Model training completed successfully'
                })
                
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                })
    
    def save_model(self, filename='crop_recommendation_model.pkl'):
        """Save the trained model and preprocessing components"""
        if self.best_model is None:
            print("No model to save. Please train models first.")
            return
        
        model_data = {
            'model': self.best_model,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'feature_names': self.feature_names,
            'model_name': self.best_model_name,
            'accuracy': self.best_accuracy
        }
        
        joblib.dump(model_data, filename)
        print(f"✅ Model saved as {filename}")
    
    def load_model(self, filename='crop_recommendation_model.pkl'):
        """Load a pre-trained model"""
        try:
            model_data = joblib.load(filename)
            self.best_model = model_data['model']
            self.scaler = model_data['scaler']
            self.label_encoder = model_data['label_encoder']
            self.feature_names = model_data['feature_names']
            self.best_model_name = model_data['model_name']
            self.best_accuracy = model_data['accuracy']
            print(f"✅ Model loaded from {filename}")
            return True
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def run_web_app(self, host='127.0.0.1', port=5001, debug=False):
        """Run the Flask web application"""
        print(f"\n🚀 Starting Crop Recommendation Web Application...")
        print(f"🌐 Access the application at: http://{host}:{port}")
        print("📊 The application includes:")
        print("   • Crop prediction based on soil and climate parameters")
        print("\n⏳ Initializing models in the background...")
        
        # Initialize data and models in a separate thread
        def initialize_app():
            try:
                self.load_data()
                self.preprocess_data()
                self.train_models()
                print("✅ Model initialization completed!")
            except Exception as e:
                print(f"❌ Error during initialization: {e}")
        
        init_thread = threading.Thread(target=initialize_app, daemon=True)
        init_thread.start()
        
        # Open browser automatically
        if not debug:
            def open_browser():
                import time
                time.sleep(1.5)  # Wait for server to start
                webbrowser.open(f'http://{host}:{port}')
            
            browser_thread = threading.Thread(target=open_browser, daemon=True)
            browser_thread.start()
        
        # Run Flask app with error handling
        try:
            self.app.run(host=host, port=port, debug=debug, use_reloader=False)
        except KeyboardInterrupt:
            print("\n👋 Application stopped by user")
        except Exception as e:
            print(f"❌ Error running application: {e}")

def main():
    """Main function to run the Crop Recommendation System"""
    print("🌾" + "="*60 + "🌾")
    print("        CROP RECOMMENDATION SYSTEM - WEB APPLICATION")
    print("                   AI-Powered Agricultural Advisor")
    print("🌾" + "="*60 + "🌾")
    
    # Create the application instance
    app = CropRecommendationWebApp()
    
    try:
        # Option to load pre-trained model
        if os.path.exists('crop_recommendation_model.pkl'):
            print("\n📁 Found existing model file.")
            choice = input("Do you want to load the existing model? (y/n): ").lower().strip()
            if choice == 'y':
                if app.load_model():
                    print("✅ Pre-trained model loaded successfully!")
        
        # Run the web application
        print("\n🚀 Launching web application...")
        app.run_web_app(debug=False)
        
    except KeyboardInterrupt:
        print("\n👋 Application terminated by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        
        # Fallback to console mode
        print("\n🔄 Falling back to console mode...")
        console_mode(app)

def console_mode(app):
    """Console-based interaction mode"""
    print("\n" + "="*50)
    print("           CONSOLE MODE ACTIVATED")
    print("="*50)
    
    # Initialize if not already done
    if app.data is None:
        print("📊 Loading dataset...")
        app.load_data()
    
    if not hasattr(app, 'X_train'):
        print("⚙️ Preprocessing data...")
        app.preprocess_data()
    
    if not app.model_results:
        print("🤖 Training models...")
        app.train_models()
        print(f"✅ Best model: {app.best_model_name} with {app.best_accuracy:.4f} accuracy")
    
    print("\n🌱 Enter soil and climate parameters for crop prediction:")
    print("📝 Type 'quit' or 'exit' to stop")
    
    while True:
        try:
            print("\n" + "-"*50)
            
            # Check for exit command
            user_input = input("Continue with prediction? (Enter/quit): ").strip().lower()
            if user_input in ['quit', 'exit', 'q']:
                break
            
            # Get input parameters
            print("🧪 Enter Nutrient Values:")
            N = float(input("Nitrogen (N) ppm [0-150]: "))
            P = float(input("Phosphorus (P) ppm [0-150]: "))
            K = float(input("Potassium (K) ppm [0-200]: "))
            
            print("\n🌤️ Enter Climate Values:")
            temperature = float(input("Temperature °C [8-50]: "))
            humidity = float(input("Humidity % [10-100]: "))
            
            print("\n🧪 Enter Soil Properties:")
            ph = float(input("pH Level [3-10]: "))
            rainfall = float(input("Rainfall mm [20-300]: "))
            
            # Make prediction
            predicted_crop, confidence, top_5 = app.predict_crop(
                N, P, K, temperature, humidity, ph, rainfall
            )
            
            if predicted_crop:
                print(f"\n🌾 PREDICTION RESULTS:")
                print(f"🏆 Recommended Crop: {predicted_crop.upper()}")
                print(f"🎯 Confidence: {confidence:.1f}%")
                
                print(f"\n🏅 Top 5 Recommendations:")
                for i, result in enumerate(top_5, 1):
                    print(f"   {i}. {result['crop'].upper()} - {result['probability']:.1f}%")
            else:
                print("❌ Could not make prediction. Model not trained.")
                
        except ValueError:
            print("❌ Please enter valid numeric values!")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Save model option
    save_choice = input("\n💾 Do you want to save the trained model? (y/n): ").lower().strip()
    if save_choice == 'y':
        app.save_model()
        print("✅ Model saved successfully!")
    
    print("👋 Console mode ended. Thank you for using the Crop Recommendation System!")

if __name__ == "__main__":
    main()