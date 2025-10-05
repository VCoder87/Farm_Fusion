<!-- Banner Section -->
<p align="center">
  <img src="banner.png" alt="Farm Fusion Banner" width="100%" />
</p>

<h1 align="center">🌾 Farm Fusion – Your Smart Agricultural Assistant 🌱</h1>

<p align="center">
  <b>An AI-powered platform empowering farmers with intelligent crop insights, yield prediction, intercropping guidance, and more.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.7%2B-blue?logo=python" />
  <img src="https://img.shields.io/badge/Django-Backend-green?logo=django" />
  <img src="https://img.shields.io/badge/Machine%20Learning-Random%20Forest-orange?logo=scikitlearn" />
  <img src="https://img.shields.io/badge/Frontend-HTML%2C%20CSS%2C%20Bootstrap-blueviolet?logo=html5" />
  <img src="https://img.shields.io/badge/License-Open%20Source-yellow" />
</p>

---

## 🌍 Overview

**Farm Fusion** is an all-in-one **AI-driven agricultural web application** that assists farmers in making data-backed decisions for better productivity and sustainable farming.

It integrates multiple modules into a single platform — blending **Machine Learning**, **Web Development**, and **AI Chat Systems** to enhance modern agriculture.

---

## 🚀 Modules Overview

### 🌱 1. Crop Recommendation  
Recommends the most suitable crops based on soil and weather conditions.  
**Dataset Source:** [Kaggle](https://www.kaggle.com/)

### 🌾 2. Crop Yield Prediction  
Predicts expected crop yield using the **Random Forest algorithm** for accurate and reliable results.  
**Dataset Source:** [Kaggle](https://www.kaggle.com/)

### 🌿 3. Intercropping Recommendation  
Suggests optimal crop combinations for sustainable farming.  
**Dataset:** *AI-generated synthetic data* (for academic and demonstration purposes)

### 💬 4. FarmChat (Chatbot)  
An interactive chatbot that assists farmers with queries and agricultural advice in real-time.

### 👨‍🌾 5. FarmCom (Farmer Community)  
A community-driven forum for farmers to share knowledge, experiences, and discussions.

---

## ⚙️ Tech Stack

| Layer | Technologies Used |
|:--|:--|
| **Frontend** | HTML, CSS, Bootstrap |
| **Backend** | Django / Flask |
| **Machine Learning** | Random Forest, Scikit-learn, Pandas, NumPy |
| **APIs** | Google Maps, OpenWeatherMap, WeatherStack |
| **Database** | SQLite / MySQL |

---

## 🧠 Datasets

| Module | Source | Description |
|:--|:--|:--|
| Crop Recommendation | Kaggle | Crop–soil–climate dataset |
| Crop Yield Prediction | Kaggle | Crop yield data by soil and weather |
| Intercropping Recommendation | Synthetic | AI-generated dataset for testing |

---

## 💻 How to Run Each Module

> ⚠️ **Before running any module**, ensure you have Python 3.7+ (and Node.js for FarmChat) installed.

### 1️⃣ Crop Recommendation
```bash
pip install -r requirements.txt
python main.py
