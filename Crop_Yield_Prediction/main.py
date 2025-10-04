"""
Flask API backend for crop yield prediction model.
This script provides REST API endpoints for the yield prediction frontend.
"""

import os
import sys
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from src.model_prediction import YieldPredictor
from src.utils import create_project_structure
import warnings
warnings.filterwarnings('ignore')

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Global variables
predictor = None
MODEL_FILE = 'models/saved_models/yield_model.pkl'

def initialize_model():
    """Initialize the prediction model on startup."""
    global predictor
    
    print("Initializing Crop Yield Prediction API...")
    
    # Create project structure if it doesn't exist
    create_project_structure()
    
    # Check if model file exists
    if not os.path.exists(MODEL_FILE):
        print(f"ERROR: Model file not found at {MODEL_FILE}")
        print("Please train your model first using the training script.")
        return False
    
    # Load the model
    predictor = YieldPredictor()
    if predictor.load_model(MODEL_FILE):
        print(f"Model loaded successfully from {MODEL_FILE}")
        return True
    else:
        print("Failed to load model!")
        return False

@app.route('/')
def index():
    """Serve the frontend HTML page."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crop Yield Prediction</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.7/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-LN+7fdVzj6u52u30Kp6M/trliBMCMKTyK833zpbD+pXdCLuTusPj697FH4R/5mcr" crossorigin="anonymous">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
            text-align: center;
            padding: 30px;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }

        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .form-container {
            padding: 40px;
        }

        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
        }

        .form-group label {
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
            font-size: 0.95em;
        }

        .form-group input,
        .form-group select {
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: all 0.3s ease;
            background: white;
        }

        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            border-color: #4CAF50;
            box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
            transform: translateY(-2px);
        }

        .form-group input:hover,
        .form-group select:hover {
            border-color: #4CAF50;
        }

        .predict-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 20px;
        }

        .predict-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(76, 175, 80, 0.3);
        }

        .predict-btn:active {
            transform: translateY(-1px);
        }

        .predict-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        .result-container {
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border-radius: 15px;
            padding: 25px;
            margin-top: 20px;
            text-align: center;
            border: 2px solid #dee2e6;
            display: none;
        }

        .result-container.show {
            display: block;
            animation: slideIn 0.5s ease;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .result-title {
            font-size: 1.4em;
            font-weight: 600;
            color: #333;
            margin-bottom: 15px;
        }

        .result-value {
            font-size: 2.5em;
            font-weight: 700;
            color: #4CAF50;
            margin-bottom: 10px;
        }

        .result-unit {
            font-size: 1.1em;
            color: #666;
        }

        .error-message {
            background: #ff6b6b;
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            display: none;
        }

        .loading {
            text-align: center;
            color: #666;
            font-style: italic;
        }

        .optional-note {
            font-size: 0.85em;
            color: #888;
            font-style: italic;
        }

        @media (max-width: 768px) {
            .container {
                margin: 10px;
            }
            
            .form-container {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .form-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
  <header class="d-flex flex-wrap align-items-center justify-content-center justify-content-md-between py-3 mb-4 border-bottom">
        <div class="col-md-3 mb-2 mb-md-0">
            <a href="/" class="d-inline-flex link-body-emphasis text-decoration-none">
                <svg class="bi" width="40" height="32" role="img" aria-label="Bootstrap">
                    <use xlink:href="#bootstrap"></use>
                </svg>
                <span class="fs-4">Farm Fusion</span>
            </a>
        </div>
        
        <ul class="nav col-12 col-md-auto mb-2 justify-content-center mb-md-0">
            <li><a href="#" class="nav-link px-2 link-success">Home</a></li>
            <li><a href="#" class="nav-link px-2 text-success">Features</a></li>
            <li><a href="#" class="nav-link px-2 text-success">FarmCom</a></li>
            <li><a href="#" class="nav-link px-2 text-success">FAQs</a></li>
            <li><a href="about.html" class="nav-link px-2 text-success">About</a></li>
        </ul>
        
        <div class="col-md-3 text-end">
            <button type="button" class="btn btn-outline-success me-2">Login</button>
            <button type="button" class="btn btn-success">Sign-up</button>
        </div>
    </header>
        <div class="form-container">
            <form id="predictionForm">
                <div class="form-grid">
                    <div class="form-group">
                        <label for="crop">Crop Type</label>
                        <input type="text" id="crop" name="crop" required placeholder="e.g., Rice, Wheat, Corn">
                    </div>
                    
                    <div class="form-group">
                        <label for="state">State</label>
                        <input type="text" id="state" name="state" required placeholder="e.g., Punjab, Karnataka">
                    </div>
                    
                    <div class="form-group">
                        <label for="area">Area (hectares)</label>
                        <input type="number" id="area" name="area" step="0.01" required placeholder="e.g., 100.5">
                    </div>
                    
                    <div class="form-group">
                        <label for="production">Production (tonnes)</label>
                        <input type="number" id="production" name="production" step="0.01" required placeholder="e.g., 250.75">
                    </div>
                    
                    <div class="form-group">
                        <label for="rainfall">Annual Rainfall (mm)</label>
                        <input type="number" id="rainfall" name="rainfall" step="0.01" required placeholder="e.g., 1200.5">
                    </div>
                    
                    <div class="form-group">
                        <label for="fertilizer">Fertilizer (kg/hectare)</label>
                        <input type="number" id="fertilizer" name="fertilizer" step="0.01" required placeholder="e.g., 120.5">
                    </div>
                    
                    <div class="form-group">
                        <label for="pesticide">Pesticide (kg/hectare)</label>
                        <input type="number" id="pesticide" name="pesticide" step="0.01" required placeholder="e.g., 5.2">
                    </div>
                    
                    <div class="form-group">
                        <label for="season">Season <span class="optional-note">(optional)</span></label>
                        <select id="season" name="season">
                            <option value="">Select season</option>
                            <option value="Kharif">Kharif (Monsoon)</option>
                            <option value="Rabi">Rabi (Winter)</option>
                            <option value="Zaid">Zaid (Summer)</option>
                            <option value="Whole Year">Whole Year</option>
                        </select>
                    </div>
                </div>
                
                <button type="submit" class="predict-btn" id="predictBtn">
                    🔮 Predict Yield
                </button>
            </form>
            
            <div id="result" class="result-container">
                <div class="result-title">Predicted Crop Yield</div>
                <div class="result-value" id="yieldValue">-</div>
                <div class="result-unit">tonnes per hectare</div>
            </div>
            
            <div id="error" class="error-message"></div>
        </div>
    </div>

    <script>
        const API_BASE_URL = window.location.origin; // Use same origin for API calls
        
        document.getElementById('predictionForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = {};
            
            // Collect form data
            for (let [key, value] of formData.entries()) {
                if (value.trim() !== '') {
                    data[key] = value;
                }
            }
            
            // Show loading state
            const predictBtn = document.getElementById('predictBtn');
            const originalText = predictBtn.textContent;
            predictBtn.textContent = '🔄 Predicting...';
            predictBtn.disabled = true;
            
            // Hide previous results/errors
            document.getElementById('result').classList.remove('show');
            document.getElementById('error').style.display = 'none';
            
            try {
                const response = await fetch(`${API_BASE_URL}/predict`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                
                // Display result
                document.getElementById('yieldValue').textContent = result.predicted_yield.toFixed(4);
                document.getElementById('result').classList.add('show');
                
            } catch (error) {
                console.error('Error:', error);
                const errorDiv = document.getElementById('error');
                errorDiv.textContent = `Error: ${error.message}`;
                errorDiv.style.display = 'block';
            } finally {
                // Reset button
                predictBtn.textContent = originalText;
                predictBtn.disabled = false;
            }
        });
        
        // Add input animations
        document.querySelectorAll('input, select').forEach(input => {
            input.addEventListener('focus', function() {
                this.parentElement.style.transform = 'scale(1.02)';
            });
            
            input.addEventListener('blur', function() {
                this.parentElement.style.transform = 'scale(1)';
            });
        });
    </script>
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
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.7/dist/js/bootstrap.bundle.min.js" integrity="sha384-ndDqU0Gzau9qJ1lfW4pNLlhNTkCfHzAVBReH9diLlhNTkCLuTusPj697FH4R/5mcr" crossorigin="anonymous"></script>

</body>
</html>
    """
    return render_template_string(html_content)

@app.route('/predict', methods=['POST'])
def predict_yield():
    """API endpoint for yield prediction."""
    try:
        # Check if model is loaded
        if predictor is None:
            return jsonify({
                'error': 'Model not loaded. Please check server configuration.',
                'status': 'error'
            }), 500
        
        # Get data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided',
                'status': 'error'
            }), 400
        
        # Extract parameters with validation
        try:
            crop = data.get('crop', '').strip()
            state = data.get('state', '').strip()
            area = float(data.get('area', 0))
            production = float(data.get('production', 0))
            rainfall = float(data.get('rainfall', 0))
            fertilizer = float(data.get('fertilizer', 0))
            pesticide = float(data.get('pesticide', 0))
            season = data.get('season', '').strip() or None
            
            # Basic validation
            if not crop or not state:
                return jsonify({
                    'error': 'Crop and State are required fields',
                    'status': 'error'
                }), 400
            
            if area <= 0:
                return jsonify({
                    'error': 'Area must be greater than 0',
                    'status': 'error'
                }), 400
            
            if any(val < 0 for val in [production, rainfall, fertilizer, pesticide]):
                return jsonify({
                    'error': 'Production, rainfall, fertilizer, and pesticide values cannot be negative',
                    'status': 'error'
                }), 400
        
        except (ValueError, TypeError) as e:
            return jsonify({
                'error': f'Invalid input values: {str(e)}',
                'status': 'error'
            }), 400
        
        # Make prediction
        predicted_yield = predictor.predict(
            crop, state, area, production, rainfall, fertilizer, pesticide, season
        )
        
        if predicted_yield is None:
            return jsonify({
                'error': 'Prediction failed. Please check your input values.',
                'status': 'error'
            }), 400
        
        # Calculate additional metrics
        productivity = predicted_yield / area if area > 0 else 0
        
        # Get confidence interval if available
        confidence_result = predictor.predict_with_confidence(
            crop, state, area, production, rainfall, fertilizer, pesticide, season
        )
        
        response_data = {
            'predicted_yield': float(predicted_yield),
            'productivity': float(productivity),
            'status': 'success',
            'inputs': {
                'crop': crop,
                'state': state,
                'area': area,
                'production': production,
                'rainfall': rainfall,
                'fertilizer': fertilizer,
                'pesticide': pesticide,
                'season': season
            }
        }
        
        # Add confidence interval if available
        if confidence_result and confidence_result.get('lower_bound') is not None:
            response_data['confidence_interval'] = {
                'lower_bound': float(confidence_result['lower_bound']),
                'upper_bound': float(confidence_result['upper_bound'])
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    model_status = 'loaded' if predictor is not None else 'not_loaded'
    return jsonify({
        'status': 'healthy',
        'model_status': model_status,
        'model_file': MODEL_FILE
    })

@app.route('/model-info', methods=['GET'])
def model_info():
    """Get information about the loaded model."""
    if predictor is None:
        return jsonify({
            'error': 'Model not loaded',
            'status': 'error'
        }), 400
    
    try:
        model_type = type(predictor.model).__name__
        info = {
            'model_type': model_type,
            'model_file': MODEL_FILE,
            'status': 'loaded'
        }
        
        # Add feature importance if available
        if hasattr(predictor.model, 'feature_importances_'):
            info['has_feature_importance'] = True
            info['feature_importances'] = predictor.model.feature_importances_.tolist()
        else:
            info['has_feature_importance'] = False
        
        return jsonify(info)
        
    except Exception as e:
        return jsonify({
            'error': f'Error getting model info: {str(e)}',
            'status': 'error'
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Endpoint not found',
        'status': 'error'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'error': 'Internal server error',
        'status': 'error'
    }), 500

def main():
    """Main function to start the Flask API server."""
    print("=" * 60)
    print("CROP YIELD PREDICTION API SERVER")
    print("=" * 60)
    
    # Initialize the model
    if not initialize_model():
        print("Failed to initialize model. Exiting...")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("SERVER STARTUP INFORMATION")
    print("=" * 60)
    print(f"Model file: {MODEL_FILE}")
    print(f"Model type: {type(predictor.model).__name__}")
    print("\nAPI Endpoints:")
    print("- GET  /           : Frontend interface")
    print("- POST /predict    : Yield prediction")
    print("- GET  /health     : Health check")
    print("- GET  /model-info : Model information")
    print("=" * 60)
    
    # Start the Flask development server
    print("\nStarting Flask server...")
    print("Access the application at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        app.run(debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        print("Server shutdown complete.")

if __name__ == "__main__":
    main()