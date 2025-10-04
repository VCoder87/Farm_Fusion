"""
Utility functions for crop yield prediction project.
Contains helper functions for data visualization, model comparison, and analysis.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import os
import warnings
warnings.filterwarnings('ignore')


def create_project_structure():
    """Create the required project directory structure."""
    directories = [
        'data',
        'models',
        'models/saved_models',
        'src',
        'notebooks'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Create __init__.py file
    init_file = 'src/__init__.py'
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('# Crop Yield Prediction Package\n')
        print(f"Created file: {init_file}")
    
    print("Project structure created successfully!")


def plot_data_distribution(data, columns=None, figsize=(15, 10)):
    """
    Plot distribution of numerical columns in the dataset.
    
    Parameters:
    -----------
    data : pandas.DataFrame
        The dataset
    columns : list, optional
        List of columns to plot. If None, plots all numerical columns
    figsize : tuple
        Figure size for the plots
    """
    
    if columns is None:
        # Select numerical columns
        columns = data.select_dtypes(include=[np.number]).columns.tolist()
    
    n_cols = 3
    n_rows = (len(columns) + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    axes = axes.flatten() if n_rows > 1 else [axes]
    
    for idx, col in enumerate(columns):
        if idx < len(axes):
            axes[idx].hist(data[col].dropna(), bins=30, alpha=0.7)
            axes[idx].set_title(f'Distribution of {col}')
            axes[idx].set_xlabel(col)
            axes[idx].set_ylabel('Frequency')
    
    # Hide empty subplots
    for idx in range(len(columns), len(axes)):
        axes[idx].set_visible(False)
    
    plt.tight_layout()
    plt.show()


def plot_correlation_matrix(data, figsize=(12, 10)):
    """
    Plot correlation matrix heatmap for numerical columns.
    
    Parameters:
    -----------
    data : pandas.DataFrame
        The dataset
    figsize : tuple
        Figure size for the plot
    """
    
    # Select only numerical columns
    numerical_data = data.select_dtypes(include=[np.number])
    
    # Calculate correlation matrix
    correlation_matrix = numerical_data.corr()
    
    # Create heatmap
    plt.figure(figsize=figsize)
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                square=True, linewidths=0.5)
    plt.title('Correlation Matrix of Numerical Features')
    plt.tight_layout()
    plt.show()
    
    return correlation_matrix


def compare_models(model_results):
    """
    Compare multiple model results and create visualization.
    
    Parameters:
    -----------
    model_results : dict
        Dictionary where keys are model names and values are result dictionaries
        from model evaluation
    """
    
    # Extract metrics
    models = list(model_results.keys())
    metrics = ['test_r2', 'test_mae', 'test_rmse']
    
    # Create comparison DataFrame
    comparison_data = []
    for model_name, results in model_results.items():
        comparison_data.append({
            'Model': model_name,
            'R² Score': results.get('test_r2', 0),
            'MAE': results.get('test_mae', 0),
            'RMSE': results.get('test_rmse', 0)
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # Plot comparison
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # R² Score (higher is better)
    axes[0].bar(comparison_df['Model'], comparison_df['R² Score'])
    axes[0].set_title('R² Score Comparison')
    axes[0].set_ylabel('R² Score')
    axes[0].tick_params(axis='x', rotation=45)
    
    # MAE (lower is better)
    axes[1].bar(comparison_df['Model'], comparison_df['MAE'])
    axes[1].set_title('Mean Absolute Error Comparison')
    axes[1].set_ylabel('MAE')
    axes[1].tick_params(axis='x', rotation=45)
    
    # RMSE (lower is better)
    axes[2].bar(comparison_df['Model'], comparison_df['RMSE'])
    axes[2].set_title('Root Mean Square Error Comparison')
    axes[2].set_ylabel('RMSE')
    axes[2].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.show()
    
    print("Model Comparison Results:")
    print(comparison_df.to_string(index=False))
    
    return comparison_df


def analyze_crop_yield_by_state(data, top_n=10):
    """
    Analyze crop yield patterns by state.
    
    Parameters:
    -----------
    data : pandas.DataFrame
        The dataset
    top_n : int
        Number of top states to display
    """
    
    # Calculate average yield by state
    state_yield = data.groupby('State')['Yield'].agg(['mean', 'std', 'count']).reset_index()
    state_yield = state_yield.sort_values('mean', ascending=False).head(top_n)
    
    # Plot
    plt.figure(figsize=(12, 6))
    plt.bar(range(len(state_yield)), state_yield['mean'], 
            yerr=state_yield['std'], capsize=5, alpha=0.7)
    plt.xlabel('State')
    plt.ylabel('Average Yield')
    plt.title(f'Top {top_n} States by Average Crop Yield')
    plt.xticks(range(len(state_yield)), state_yield['State'], rotation=45)
    plt.tight_layout()
    plt.show()
    
    print(f"Top {top_n} States by Average Yield:")
    print(state_yield.to_string(index=False))
    
    return state_yield


def analyze_crop_yield_by_crop(data, top_n=10):
    """
    Analyze crop yield patterns by crop type.
    
    Parameters:
    -----------
    data : pandas.DataFrame
        The dataset
    top_n : int
        Number of top crops to display
    """
    
    # Calculate average yield by crop
    crop_yield = data.groupby('Crop')['Yield'].agg(['mean', 'std', 'count']).reset_index()
    crop_yield = crop_yield.sort_values('mean', ascending=False).head(top_n)
    
    # Plot
    plt.figure(figsize=(12, 6))
    plt.bar(range(len(crop_yield)), crop_yield['mean'], 
            yerr=crop_yield['std'], capsize=5, alpha=0.7)
    plt.xlabel('Crop')
    plt.ylabel('Average Yield')
    plt.title(f'Top {top_n} Crops by Average Yield')
    plt.xticks(range(len(crop_yield)), crop_yield['Crop'], rotation=45)
    plt.tight_layout()
    plt.show()
    
    print(f"Top {top_n} Crops by Average Yield:")
    print(crop_yield.to_string(index=False))
    
    return crop_yield


def calculate_yield_efficiency(data):
    """
    Calculate yield efficiency (Yield per unit of input).
    
    Parameters:
    -----------
    data : pandas.DataFrame
        The dataset
        
    Returns:
    --------
    pandas.DataFrame
        Dataset with efficiency metrics added
    """
    
    result_data = data.copy()
    
    # Yield per unit area
    result_data['Yield_per_Area'] = result_data['Yield'] / result_data['Area']
    
    # Yield per unit fertilizer
    result_data['Yield_per_Fertilizer'] = result_data['Yield'] / (result_data['Fertilizer'] + 1)
    
    # Yield per unit pesticide
    result_data['Yield_per_Pesticide'] = result_data['Yield'] / (result_data['Pesticide'] + 1)
    
    # Yield per unit rainfall
    result_data['Yield_per_Rainfall'] = result_data['Yield'] / (result_data['Annual_Rainfall'] + 1)
    
    return result_data


def generate_prediction_report(actual, predicted, model_name="Model"):
    """
    Generate a comprehensive prediction report.
    
    Parameters:
    -----------
    actual : array-like
        Actual values
    predicted : array-like
        Predicted values
    model_name : str
        Name of the model
        
    Returns:
    --------
    dict
        Report dictionary with various metrics
    """
    
    # Calculate metrics
    r2 = r2_score(actual, predicted)
    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    mape = np.mean(np.abs((actual - predicted) / actual)) * 100
    
    # Calculate additional metrics
    residuals = actual - predicted
    mean_residual = np.mean(residuals)
    std_residual = np.std(residuals)
    
    report = {
        'model_name': model_name,
        'r2_score': r2,
        'mae': mae,
        'rmse': rmse,
        'mape': mape,
        'mean_residual': mean_residual,
        'std_residual': std_residual,
        'min_actual': np.min(actual),
        'max_actual': np.max(actual),
        'min_predicted': np.min(predicted),
        'max_predicted': np.max(predicted)
    }
    
    print(f"\n=== {model_name} Prediction Report ===")
    print(f"R² Score: {r2:.4f}")
    print(f"Mean Absolute Error: {mae:.4f}")
    print(f"Root Mean Square Error: {rmse:.4f}")
    print(f"Mean Absolute Percentage Error: {mape:.2f}%")
    print(f"Mean Residual: {mean_residual:.4f}")
    print(f"Std Residual: {std_residual:.4f}")
    
    return report


def save_results_to_csv(results, filename):
    """
    Save prediction results to CSV file.
    
    Parameters:
    -----------
    results : pandas.DataFrame
        Results DataFrame
    filename : str
        Output filename
    """
    
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(filename)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        results.to_csv(filename, index=False)
        print(f"Results saved to {filename}")
        
    except Exception as e:
        print(f"Error saving results: {e}")


def load_multiple_models(model_directory):
    """
    Load multiple models from a directory.
    
    Parameters:
    -----------
    model_directory : str
        Path to directory containing model files
        
    Returns:
    --------
    dict
        Dictionary of loaded models
    """
    
    models = {}
    
    if not os.path.exists(model_directory):
        print(f"Directory not found: {model_directory}")
        return models
    
    for filename in os.listdir(model_directory):
        if filename.endswith('.pkl'):
            model_path = os.path.join(model_directory, filename)
            try:
                model_data = joblib.load(model_path)
                model_name = filename.replace('.pkl', '')
                models[model_name] = model_data
                print(f"Loaded model: {model_name}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    return models


def validate_input_data(crop, state, area, production, annual_rainfall, fertilizer, pesticide):
    """
    Validate input data for prediction.
    
    Parameters:
    -----------
    All prediction input parameters
    
    Returns:
    --------
    bool
        True if all inputs are valid, False otherwise
    """
    
    errors = []
    
    # Check if required string inputs are provided
    if not crop or not isinstance(crop, str):
        errors.append("Crop must be a non-empty string")
    
    if not state or not isinstance(state, str):
        errors.append("State must be a non-empty string")
    
    # Check numerical inputs
    numerical_inputs = {
        'area': area,
        'production': production,
        'annual_rainfall': annual_rainfall,
        'fertilizer': fertilizer,
        'pesticide': pesticide
    }
    
    for name, value in numerical_inputs.items():
        try:
            float_value = float(value)
            if float_value < 0:
                errors.append(f"{name} must be non-negative")
        except (ValueError, TypeError):
            errors.append(f"{name} must be a valid number")
    
    # Print errors if any
    if errors:
        print("Input validation errors:")
        for error in errors:
            print(f"- {error}")
        return False
    
    return True


if __name__ == "__main__":
    # Test utility functions
    print("Testing utility functions...")
    
    # Create project structure
    create_project_structure()
    
    print("Utility functions are ready to use!")