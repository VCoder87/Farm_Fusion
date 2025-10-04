"""
Data preprocessing module for crop yield prediction.
Handles data cleaning, feature engineering, and encoding.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')


class DataPreprocessor:
    def __init__(self):
        self.crop_encoder = LabelEncoder()
        self.state_encoder = LabelEncoder()
        self.season_encoder = LabelEncoder()
        self.is_fitted = False
        
    def load_data(self, file_path):
        """Load data from CSV file."""
        try:
            self.data = pd.read_csv(file_path)
            print(f"Data loaded successfully. Shape: {self.data.shape}")
            return self.data
        except Exception as e:
            print(f"Error loading data: {e}")
            return None
    
    def explore_data(self):
        """Basic data exploration."""
        if hasattr(self, 'data'):
            print("\n=== Data Info ===")
            print(self.data.info())
            print("\n=== First 5 rows ===")
            print(self.data.head())
            print("\n=== Statistical Summary ===")
            print(self.data.describe())
            print("\n=== Missing Values ===")
            print(self.data.isnull().sum())
            print("\n=== Unique Values ===")
            print(f"Unique Crops: {self.data['Crop'].nunique()}")
            print(f"Unique States: {self.data['State'].nunique()}")
            print(f"Unique Seasons: {self.data['Season'].nunique()}")
        else:
            print("No data loaded. Please load data first.")
    
    def clean_data(self):
        """Clean the dataset."""
        if not hasattr(self, 'data'):
            print("No data loaded. Please load data first.")
            return None
            
        # Make a copy of the data
        cleaned_data = self.data.copy()
        
        # Remove rows with missing values in critical columns
        critical_columns = ['Crop', 'State', 'Area', 'Production', 'Yield']
        cleaned_data = cleaned_data.dropna(subset=critical_columns)
        
        # Fill missing values for optional columns
        if 'Annual_Rainfall' in cleaned_data.columns:
            cleaned_data['Annual_Rainfall'].fillna(cleaned_data['Annual_Rainfall'].median(), inplace=True)
        if 'Fertilizer' in cleaned_data.columns:
            cleaned_data['Fertilizer'].fillna(cleaned_data['Fertilizer'].median(), inplace=True)
        if 'Pesticide' in cleaned_data.columns:
            cleaned_data['Pesticide'].fillna(cleaned_data['Pesticide'].median(), inplace=True)
        if 'Season' in cleaned_data.columns:
            cleaned_data['Season'].fillna('Unknown', inplace=True)
            
        # Remove outliers using IQR method for numerical columns
        numerical_cols = ['Area', 'Production', 'Annual_Rainfall', 'Fertilizer', 'Pesticide', 'Yield']
        
        for col in numerical_cols:
            if col in cleaned_data.columns:
                Q1 = cleaned_data[col].quantile(0.25)
                Q3 = cleaned_data[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # Remove outliers
                cleaned_data = cleaned_data[
                    (cleaned_data[col] >= lower_bound) & 
                    (cleaned_data[col] <= upper_bound)
                ]
        
        print(f"Data cleaned. Original shape: {self.data.shape}, Cleaned shape: {cleaned_data.shape}")
        self.cleaned_data = cleaned_data
        return cleaned_data
    
    def encode_categorical_features(self, data):
        """Encode categorical features."""
        encoded_data = data.copy()
        
        if not self.is_fitted:
            # Fit encoders on training data
            encoded_data['Crop_Encoded'] = self.crop_encoder.fit_transform(encoded_data['Crop'])
            encoded_data['State_Encoded'] = self.state_encoder.fit_transform(encoded_data['State'])
            
            if 'Season' in encoded_data.columns:
                encoded_data['Season_Encoded'] = self.season_encoder.fit_transform(encoded_data['Season'])
            
            self.is_fitted = True
        else:
            # Transform using fitted encoders
            # Handle new categories by assigning them to a default value
            try:
                encoded_data['Crop_Encoded'] = self.crop_encoder.transform(encoded_data['Crop'])
            except ValueError:
                # Handle unseen categories
                encoded_data['Crop_Encoded'] = 0
                
            try:
                encoded_data['State_Encoded'] = self.state_encoder.transform(encoded_data['State'])
            except ValueError:
                encoded_data['State_Encoded'] = 0
                
            if 'Season' in encoded_data.columns:
                try:
                    encoded_data['Season_Encoded'] = self.season_encoder.transform(encoded_data['Season'])
                except ValueError:
                    encoded_data['Season_Encoded'] = 0
        
        return encoded_data
    
    def prepare_features(self, data):
        """Prepare feature matrix and target vector."""
        # Select features for prediction
        feature_columns = [
            'Crop_Encoded', 'State_Encoded', 'Area', 'Production', 
            'Annual_Rainfall', 'Fertilizer', 'Pesticide'
        ]
        
        # Add Season if available
        if 'Season_Encoded' in data.columns:
            feature_columns.append('Season_Encoded')
        
        # Ensure all feature columns exist
        available_features = [col for col in feature_columns if col in data.columns]
        
        X = data[available_features]
        y = data['Yield']
        
        return X, y, available_features
    
    def preprocess_data(self, file_path, test_size=0.2, random_state=42):
        """Complete preprocessing pipeline."""
        # Load data
        if self.load_data(file_path) is None:
            return None
            
        # Explore data
        self.explore_data()
        
        # Clean data
        cleaned_data = self.clean_data()
        if cleaned_data is None:
            return None
            
        # Encode categorical features
        encoded_data = self.encode_categorical_features(cleaned_data)
        
        # Prepare features
        X, y, feature_names = self.prepare_features(encoded_data)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        print(f"Training set shape: {X_train.shape}")
        print(f"Test set shape: {X_test.shape}")
        print(f"Feature columns: {feature_names}")
        
        return X_train, X_test, y_train, y_test, feature_names
    
    def encode_single_prediction(self, crop, state, season=None):
        """Encode categorical values for single prediction."""
        try:
            crop_encoded = self.crop_encoder.transform([crop])[0]
        except ValueError:
            print(f"Warning: Unknown crop '{crop}'. Using default encoding.")
            crop_encoded = 0
            
        try:
            state_encoded = self.state_encoder.transform([state])[0]
        except ValueError:
            print(f"Warning: Unknown state '{state}'. Using default encoding.")
            state_encoded = 0
            
        season_encoded = 0
        if season and hasattr(self, 'season_encoder'):
            try:
                season_encoded = self.season_encoder.transform([season])[0]
            except ValueError:
                print(f"Warning: Unknown season '{season}'. Using default encoding.")
                season_encoded = 0
                
        return crop_encoded, state_encoded, season_encoded


if __name__ == "__main__":
    # Test the preprocessor
    preprocessor = DataPreprocessor()
    
    # Example usage
    try:
        result = preprocessor.preprocess_data('data/crop_data.csv')
        if result:
            X_train, X_test, y_train, y_test, feature_names = result
            print("Preprocessing completed successfully!")
        else:
            print("Preprocessing failed!")
    except Exception as e:
        print(f"Error during preprocessing: {e}")