"""
Model prediction module for crop yield prediction.
Handles loading trained models and making predictions.
"""

import pandas as pd
import numpy as np
import joblib
import os
from .data_preprocessing import DataPreprocessor
import warnings
warnings.filterwarnings('ignore')


class YieldPredictor:
    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.feature_names = None
        self.is_loaded = False
        
    def load_model(self, model_path):
        """Load a trained model from file."""
        try:
            if not os.path.exists(model_path):
                print(f"Model file not found: {model_path}")
                return False
                
            model_data = joblib.load(model_path)
            
            self.model = model_data['model']
            self.preprocessor = model_data['preprocessor']
            self.feature_names = model_data['feature_names']
            self.is_loaded = True
            
            print(f"Model loaded successfully from {model_path}")
            print(f"Model type: {type(self.model).__name__}")
            print(f"Features: {self.feature_names}")
            return True
            
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def predict(self, crop, state, area, production, annual_rainfall, 
                fertilizer, pesticide, season=None):
        """
        Make a yield prediction for given inputs.
        
        Parameters:
        -----------
        crop : str
            Crop type (e.g., 'Maize', 'Rice', 'Wheat')
        state : str
            State name (e.g., 'Assam', 'Bihar')
        area : float
            Area in hectares
        production : float
            Production in tons
        annual_rainfall : float
            Annual rainfall in mm
        fertilizer : float
            Fertilizer usage in kg
        pesticide : float
            Pesticide usage in kg
        season : str, optional
            Season (e.g., 'Kharif', 'Rabi', 'Whole Year')
            
        Returns:
        --------
        float
            Predicted yield
        """
        
        if not self.is_loaded:
            print("No model loaded. Please load a model first.")
            return None
            
        try:
            # Encode categorical variables
            crop_encoded, state_encoded, season_encoded = self.preprocessor.encode_single_prediction(
                crop, state, season
            )
            
            # Prepare feature vector
            features = [crop_encoded, state_encoded, area, production, 
                       annual_rainfall, fertilizer, pesticide]
            
            # Add season if it was used in training
            if 'Season_Encoded' in self.feature_names:
                features.append(season_encoded)
            
            # Convert to numpy array and reshape
            features_array = np.array(features).reshape(1, -1)
            
            # Create DataFrame with proper column names
            feature_df = pd.DataFrame(features_array, columns=self.feature_names)
            
            # Make prediction
            prediction = self.model.predict(feature_df)[0]
            
            print(f"\n=== Prediction Details ===")
            print(f"Crop: {crop} (encoded: {crop_encoded})")
            print(f"State: {state} (encoded: {state_encoded})")
            print(f"Area: {area} hectares")
            print(f"Production: {production} tons")
            print(f"Annual Rainfall: {annual_rainfall} mm")
            print(f"Fertilizer: {fertilizer} kg")
            print(f"Pesticide: {pesticide} kg")
            if season:
                print(f"Season: {season} (encoded: {season_encoded})")
            print(f"Predicted Yield: {prediction:.4f}")
            
            return prediction
            
        except Exception as e:
            print(f"Error making prediction: {e}")
            return None
    
    def predict_batch(self, data_file):
        """
        Make predictions for a batch of data from CSV file.
        
        Parameters:
        -----------
        data_file : str
            Path to CSV file containing prediction data
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame with original data and predictions
        """
        
        if not self.is_loaded:
            print("No model loaded. Please load a model first.")
            return None
            
        try:
            # Load data
            data = pd.read_csv(data_file)
            print(f"Loaded {len(data)} records for batch prediction")
            
            # Encode categorical variables
            encoded_data = self.preprocessor.encode_categorical_features(data)
            
            # Prepare features
            X, _, _ = self.preprocessor.prepare_features(encoded_data)
            
            # Make predictions
            predictions = self.model.predict(X)
            
            # Add predictions to original data
            result_data = data.copy()
            result_data['Predicted_Yield'] = predictions
            
            print("Batch predictions completed successfully!")
            return result_data
            
        except Exception as e:
            print(f"Error in batch prediction: {e}")
            return None
    
    def get_model_info(self):
        """Get information about the loaded model."""
        if not self.is_loaded:
            print("No model loaded.")
            return None
            
        info = {
            'model_type': type(self.model).__name__,
            'features': self.feature_names,
            'n_features': len(self.feature_names)
        }
        
        # Additional info for specific model types
        if hasattr(self.model, 'n_estimators'):
            info['n_estimators'] = self.model.n_estimators
        if hasattr(self.model, 'max_depth'):
            info['max_depth'] = self.model.max_depth
        if hasattr(self.model, 'feature_importances_'):
            importance_dict = dict(zip(self.feature_names, self.model.feature_importances_))
            info['feature_importance'] = importance_dict
            
        return info
    
    def predict_with_confidence(self, crop, state, area, production, annual_rainfall,
                               fertilizer, pesticide, season=None, n_predictions=100):
        """
        Make prediction with confidence interval (for ensemble models).
        
        Parameters:
        -----------
        Same as predict() method
        n_predictions : int
            Number of predictions to make for confidence estimation
            
        Returns:
        --------
        dict
            Dictionary containing prediction, lower bound, upper bound
        """
        
        if not self.is_loaded:
            print("No model loaded. Please load a model first.")
            return None
            
        # Check if model supports prediction intervals
        if not hasattr(self.model, 'estimators_'):
            print("Confidence intervals only available for ensemble models.")
            prediction = self.predict(crop, state, area, production, annual_rainfall,
                                    fertilizer, pesticide, season)
            return {'prediction': prediction, 'lower_bound': None, 'upper_bound': None}
        
        try:
            # Encode categorical variables
            crop_encoded, state_encoded, season_encoded = self.preprocessor.encode_single_prediction(
                crop, state, season
            )
            
            # Prepare feature vector
            features = [crop_encoded, state_encoded, area, production,
                       annual_rainfall, fertilizer, pesticide]
            
            if 'Season_Encoded' in self.feature_names:
                features.append(season_encoded)
            
            features_array = np.array(features).reshape(1, -1)
            feature_df = pd.DataFrame(features_array, columns=self.feature_names)
            
            # Get predictions from all estimators
            predictions = []
            for estimator in self.model.estimators_:
                pred = estimator.predict(feature_df)[0]
                predictions.append(pred)
            
            predictions = np.array(predictions)
            
            # Calculate statistics
            mean_pred = np.mean(predictions)
            std_pred = np.std(predictions)
            lower_bound = np.percentile(predictions, 2.5)
            upper_bound = np.percentile(predictions, 97.5)
            
            print(f"\n=== Prediction with Confidence ===")
            print(f"Mean Prediction: {mean_pred:.4f}")
            print(f"Standard Deviation: {std_pred:.4f}")
            print(f"95% Confidence Interval: [{lower_bound:.4f}, {upper_bound:.4f}]")
            
            return {
                'prediction': mean_pred,
                'std': std_pred,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'all_predictions': predictions
            }
            
        except Exception as e:
            print(f"Error making prediction with confidence: {e}")
            return None


def interactive_prediction():
    """Interactive prediction function for command line usage."""
    predictor = YieldPredictor()
    
    # Load model
    model_path = input("Enter model file path (or press Enter for default): ").strip()
    if not model_path:
        model_path = 'models/saved_models/yield_model.pkl'
    
    if not predictor.load_model(model_path):
        print("Failed to load model. Exiting.")
        return
    
    print("\n=== Interactive Yield Prediction ===")
    print("Enter the following details:")
    
    try:
        crop = input("Crop type (e.g., Maize, Rice, Wheat): ").strip()
        state = input("State (e.g., Assam, Bihar): ").strip()
        area = float(input("Area (hectares): "))
        production = float(input("Production (tons): "))
        annual_rainfall = float(input("Annual Rainfall (mm): "))
        fertilizer = float(input("Fertilizer usage (kg): "))
        pesticide = float(input("Pesticide usage (kg): "))
        
        season = input("Season (optional, e.g., Kharif, Rabi): ").strip()
        if not season:
            season = None
        
        # Make prediction
        prediction = predictor.predict(
            crop, state, area, production, annual_rainfall,
            fertilizer, pesticide, season
        )
        
        if prediction is not None:
            print(f"\n*** FINAL PREDICTION: {prediction:.4f} ***")
        else:
            print("Prediction failed!")
            
    except ValueError as e:
        print(f"Invalid input: {e}")
    except KeyboardInterrupt:
        print("\nPrediction cancelled.")


if __name__ == "__main__":
    # Run interactive prediction
    interactive_prediction()