"""
Model training module for crop yield prediction.
Handles model selection, training, evaluation, and saving.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from .data_preprocessing import DataPreprocessor
import os
import warnings
warnings.filterwarnings('ignore')


class ModelTrainer:
    def __init__(self):
        self.preprocessor = DataPreprocessor()
        self.model = None
        self.feature_names = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        
    def load_data(self, file_path):
        """Load and preprocess data."""
        try:
            result = self.preprocessor.preprocess_data(file_path)
            if result:
                self.X_train, self.X_test, self.y_train, self.y_test, self.feature_names = result
                print("Data loaded and preprocessed successfully!")
                return True
            else:
                print("Failed to load and preprocess data!")
                return False
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def train_random_forest(self, n_estimators=100, max_depth=None, random_state=42):
        """Train Random Forest model."""
        print("Training Random Forest model...")
        
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1
        )
        
        self.model.fit(self.X_train, self.y_train)
        print("Random Forest model trained successfully!")
        return self.model
    
    def train_linear_regression(self):
        """Train Linear Regression model."""
        print("Training Linear Regression model...")
        
        self.model = LinearRegression()
        self.model.fit(self.X_train, self.y_train)
        print("Linear Regression model trained successfully!")
        return self.model
    
    def train_svr(self, kernel='rbf', C=1.0, gamma='scale'):
        """Train Support Vector Regression model."""
        print("Training SVR model...")
        
        self.model = SVR(kernel=kernel, C=C, gamma=gamma)
        self.model.fit(self.X_train, self.y_train)
        print("SVR model trained successfully!")
        return self.model
    
    def train_model(self, model_type='random_forest', **kwargs):
        """Train model based on specified type."""
        if self.X_train is None:
            print("No data loaded. Please load data first.")
            return None
            
        if model_type == 'random_forest':
            return self.train_random_forest(**kwargs)
        elif model_type == 'linear_regression':
            return self.train_linear_regression(**kwargs)
        elif model_type == 'svr':
            return self.train_svr(**kwargs)
        else:
            print(f"Unknown model type: {model_type}")
            return None
    
    def evaluate_model(self):
        """Evaluate the trained model."""
        if self.model is None:
            print("No model trained. Please train a model first.")
            return None
            
        # Make predictions
        y_train_pred = self.model.predict(self.X_train)
        y_test_pred = self.model.predict(self.X_test)
        
        # Calculate metrics
        train_r2 = r2_score(self.y_train, y_train_pred)
        test_r2 = r2_score(self.y_test, y_test_pred)
        
        train_mae = mean_absolute_error(self.y_train, y_train_pred)
        test_mae = mean_absolute_error(self.y_test, y_test_pred)
        
        train_rmse = np.sqrt(mean_squared_error(self.y_train, y_train_pred))
        test_rmse = np.sqrt(mean_squared_error(self.y_test, y_test_pred))
        
        # Print results
        print("\n=== Model Evaluation Results ===")
        print(f"Training R² Score: {train_r2:.4f}")
        print(f"Testing R² Score: {test_r2:.4f}")
        print(f"Training MAE: {train_mae:.4f}")
        print(f"Testing MAE: {test_mae:.4f}")
        print(f"Training RMSE: {train_rmse:.4f}")
        print(f"Testing RMSE: {test_rmse:.4f}")
        
        # Feature importance (if available)
        if hasattr(self.model, 'feature_importances_'):
            self.plot_feature_importance()
        
        # Plot predictions vs actual
        self.plot_predictions(y_test_pred)
        
        return {
            'train_r2': train_r2,
            'test_r2': test_r2,
            'train_mae': train_mae,
            'test_mae': test_mae,
            'train_rmse': train_rmse,
            'test_rmse': test_rmse
        }
    
    def plot_feature_importance(self):
        """Plot feature importance for tree-based models."""
        if not hasattr(self.model, 'feature_importances_'):
            print("Model doesn't have feature importance.")
            return
            
        importance_df = pd.DataFrame({
            'Feature': self.feature_names,
            'Importance': self.model.feature_importances_
        }).sort_values('Importance', ascending=False)
        
        plt.figure(figsize=(10, 6))
        sns.barplot(data=importance_df, x='Importance', y='Feature')
        plt.title('Feature Importance')
        plt.xlabel('Importance Score')
        plt.tight_layout()
        plt.show()
        
        print("\n=== Feature Importance ===")
        print(importance_df)
    
    def plot_predictions(self, y_pred):
        """Plot actual vs predicted values."""
        plt.figure(figsize=(12, 5))
        
        # Scatter plot
        plt.subplot(1, 2, 1)
        plt.scatter(self.y_test, y_pred, alpha=0.6)
        plt.plot([self.y_test.min(), self.y_test.max()], 
                [self.y_test.min(), self.y_test.max()], 'r--', lw=2)
        plt.xlabel('Actual Yield')
        plt.ylabel('Predicted Yield')
        plt.title('Actual vs Predicted Yield')
        
        # Residual plot
        plt.subplot(1, 2, 2)
        residuals = self.y_test - y_pred
        plt.scatter(y_pred, residuals, alpha=0.6)
        plt.axhline(y=0, color='r', linestyle='--')
        plt.xlabel('Predicted Yield')
        plt.ylabel('Residuals')
        plt.title('Residual Plot')
        
        plt.tight_layout()
        plt.show()
    
    def save_model(self, file_path):
        """Save the trained model and preprocessor."""
        if self.model is None:
            print("No model to save. Please train a model first.")
            return False
            
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save model and preprocessor together
            model_data = {
                'model': self.model,
                'preprocessor': self.preprocessor,
                'feature_names': self.feature_names
            }
            
            joblib.dump(model_data, file_path)
            print(f"Model saved successfully to {file_path}")
            return True
            
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load_model(self, file_path):
        """Load a saved model."""
        try:
            model_data = joblib.load(file_path)
            
            self.model = model_data['model']
            self.preprocessor = model_data['preprocessor']
            self.feature_names = model_data['feature_names']
            
            print(f"Model loaded successfully from {file_path}")
            return True
            
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def cross_validate_model(self, cv_folds=5):
        """Perform cross-validation."""
        from sklearn.model_selection import cross_val_score
        
        if self.X_train is None or self.model is None:
            print("Data or model not available for cross-validation.")
            return None
            
        # Combine train and test data for cross-validation
        X_combined = pd.concat([self.X_train, self.X_test])
        y_combined = pd.concat([self.y_train, self.y_test])
        
        # Perform cross-validation
        cv_scores = cross_val_score(self.model, X_combined, y_combined, 
                                   cv=cv_folds, scoring='r2')
        
        print(f"\n=== Cross-Validation Results ({cv_folds}-fold) ===")
        print(f"CV R² Scores: {cv_scores}")
        print(f"Mean CV R² Score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        
        return cv_scores
    
    def hyperparameter_tuning(self, model_type='random_forest'):
        """Perform hyperparameter tuning using GridSearchCV."""
        from sklearn.model_selection import GridSearchCV
        
        if self.X_train is None:
            print("No data loaded for hyperparameter tuning.")
            return None
        
        print("Performing hyperparameter tuning...")
        
        if model_type == 'random_forest':
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [None, 10, 20, 30],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
            base_model = RandomForestRegressor(random_state=42)
            
        elif model_type == 'svr':
            param_grid = {
                'C': [0.1, 1, 10, 100],
                'gamma': ['scale', 'auto', 0.001, 0.01, 0.1, 1],
                'kernel': ['rbf', 'linear', 'poly']
            }
            base_model = SVR()
            
        else:
            print(f"Hyperparameter tuning not implemented for {model_type}")
            return None
        
        # Perform grid search
        grid_search = GridSearchCV(
            base_model, param_grid, cv=3, scoring='r2', n_jobs=-1, verbose=1
        )
        
        grid_search.fit(self.X_train, self.y_train)
        
        # Update model with best parameters
        self.model = grid_search.best_estimator_
        
        print(f"Best parameters: {grid_search.best_params_}")
        print(f"Best cross-validation score: {grid_search.best_score_:.4f}")
        
        return grid_search.best_params_


if __name__ == "__main__":
    # Test the trainer
    trainer = ModelTrainer()
    
    # Load data and train model
    if trainer.load_data('data/crop_data.csv'):
        # Train Random Forest model
        trainer.train_model(model_type='random_forest', n_estimators=100)
        
        # Evaluate model
        results = trainer.evaluate_model()
        
        # Cross-validation
        trainer.cross_validate_model()
        
        # Save model
        trainer.save_model('models/saved_models/yield_model.pkl')
    else:
        print("Failed to load data!")