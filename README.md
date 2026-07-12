<h1 align="center">
  Drug Properties Predictor
</h1>

<p align="center">
  <strong>A professional web application for predicting multiple drug properties simultaneously using machine learning.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Flask-2.3+-green.svg" alt="Flask">
  <img src="https://img.shields.io/badge/RDKit-2023.3+-orange.svg" alt="RDKit">
  <img src="https://img.shields.io/badge/scikit--learn-1.3+-blue.svg" alt="Scikit-Learn">
</p>

## 🚀 Overview

The **Drug Properties Predictor** is a modern, responsive web application that leverages machine learning models trained on molecular descriptors to predict five critical drug properties simultaneously. Just input a SMILES string, and the application provides a comprehensive analysis of the molecule's potential as a drug candidate.

## ✨ Features

- **Complete Property Analysis**: Predicts all 5 critical properties:
  - 💊 **Drug-Likeness** (Lipinski's Rule compliance)
  - 💧 **Solubility prediction**
  - 🧪 **Membrane Permeability**
  - 🛡️ **Chemical Stability**
  - ⚠️ **Toxicity assessment**
- **Detailed Results Dashboard**: Clean, dedicated results page showing predictions, confidence scores, and detailed explanations.
- **Molecular Descriptors**: Automatically calculates and displays key molecular properties (MW, LogP, TPSA, HBD, HBA, etc.).
- **Smart Suggestions**: Suggests valid example molecules if an invalid SMILES string is provided.
- **Example Molecules**: Pre-loaded examples (Aspirin, Caffeine, Ibuprofen) for quick testing.
- **Modern Interface**: Clean aesthetics, responsive design, and intuitive user experience.

## 📁 Repository Structure

```text
.
├── app.py                 # Main Flask application entry point
├── data.py                # Data processing and generation scripts
├── train.ipynb            # Jupyter notebook for training the ML models
├── models/                # Directory containing trained ML models and scalers
├── static/                # Static assets (CSS, JavaScript, Images)
├── templates/             # HTML templates for the web interface
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8 or higher
- Git

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/drug-properties-predictor.git
cd drug-properties-predictor
```

### 2. Create a virtual environment (Recommended)

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

*Note: If you encounter issues installing `rdkit`, you can also use conda: `conda install -c conda-forge rdkit`*

## 💻 Usage

1. Start the Flask application:
   ```bash
   python app.py
   ```
2. Open your web browser and navigate to `http://localhost:5000`
3. Enter a SMILES string in the input field or click on one of the example molecules.
4. Click **"Predict All Drug Properties"** to view the comprehensive analysis.

## 🧠 Model Training

If you want to retrain the models or explore the dataset:
1. Open the `train.ipynb` Jupyter notebook.
2. The notebook covers data preprocessing, feature engineering (using RDKit descriptors), model training (scikit-learn), and evaluation.
3. Updated models will be saved in the `models/` directory.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
Feel free to check the [issues page](https://github.com/yourusername/drug-properties-predictor/issues).

## 📝 License

This project is open source and available under the [MIT License](LICENSE).