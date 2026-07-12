import joblib
import pandas as pd
import numpy as np
import os
import json
from flask import Flask, render_template, request, jsonify
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, rdMolDescriptors, AllChem, DataStructs
import warnings

warnings.filterwarnings('ignore', category=UserWarning)
RDLogger.DisableLog('rdApp.*')

app = Flask(__name__)
MODEL_DIR = "models"
model_registry = {}

def calculate_descriptors(smiles):
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        descriptors = {
            'MW': Descriptors.MolWt(mol),
            'LogP': Descriptors.MolLogP(mol),
            'TPSA': rdMolDescriptors.CalcTPSA(mol),
            'HBD': rdMolDescriptors.CalcNumHBD(mol),
            'HBA': rdMolDescriptors.CalcNumHBA(mol),
            'RotBonds': rdMolDescriptors.CalcNumRotatableBonds(mol),
            'RingCount': rdMolDescriptors.CalcNumRings(mol),
            'AromaticRings': rdMolDescriptors.CalcNumAromaticRings(mol)
        }
        aromatic_atoms = sum(1 for atom in mol.GetAtoms() if atom.GetIsAromatic())
        total_atoms = mol.GetNumAtoms()
        descriptors['AromaticRatio'] = aromatic_atoms / total_atoms if total_atoms > 0 else 0
        return descriptors
    except Exception as e:
        print(f"Descriptor error: {e}")
        return None

def get_smart_suggestions(invalid_smiles, dataset_path="data.csv", n=4):
    try:
        dataset = pd.read_csv(dataset_path)
        if 'SMILES' not in dataset.columns:
            return []
        valid_smiles = dataset['SMILES'].dropna().unique().tolist()
        valid_smiles = [s for s in valid_smiles if len(s) <= 25]
        if not valid_smiles:
            return []
        invalid_mol = Chem.MolFromSmiles(invalid_smiles)
        if invalid_mol is None:
            return np.random.choice(valid_smiles, size=min(n, len(valid_smiles)), replace=False).tolist()
        return np.random.choice(valid_smiles, size=min(n, len(valid_smiles)), replace=False).tolist()
    except Exception as e:
        print(f" suggestion error: {e}")
        return []

def load_all_models():
    global model_registry
    metadata_path = os.path.join(MODEL_DIR, 'models_metadata.json')

    if not os.path.exists(metadata_path):
        print(f" '{metadata_path}' not found.")
        exit()
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    for name, info in metadata['models'].items():
        try:
            model_path = os.path.join(MODEL_DIR, f'model_{name}.pkl')
            scaler_path = os.path.join(MODEL_DIR, f'scaler_{name}.pkl')

            model = joblib.load(model_path)
            scaler = joblib.load(scaler_path)

            model_registry[name] = {
                'model': model,
                'scaler': scaler,
                'features': info['features'],
                'type': info['type'],
                'classes': info.get('classes')
            }
        except Exception as e:
            print(f" Error loading model {name}: {e}")

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/results')
def results():
    return render_template('results.html')
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        smiles = data.get('smiles', '').strip()
        molecule_name = data.get('molecule_name', '').strip()

        if not smiles:
            return jsonify({'error': 'SMILES string is required'}), 400

        descriptors = calculate_descriptors(smiles)
        if descriptors is None:
            suggestions_smiles = get_smart_suggestions(smiles)
            suggestions = []

            for s in suggestions_smiles:
                desc = calculate_descriptors(s)
                if not desc:
                    continue
                sample_results = {}
                for name, info in model_registry.items():
                    model = info['model']
                    scaler = info['scaler']
                    feature_list = info['features']
                    model_type = info['type']
                    try:
                        X = pd.DataFrame([desc])[feature_list]
                        X_scaled = scaler.transform(X)
                        if model_type == 'regression':
                            pred = float(model.predict(X_scaled)[0])
                            sample_results[name] = {"prediction": round(pred, 3)}
                        else:
                            probs = model.predict_proba(X_scaled)[0]
                            pred_idx = int(np.argmax(probs))
                            pred_label = info['classes'][pred_idx]
                            sample_results[name] = {"prediction": pred_label}
                    except Exception:
                        sample_results[name] = {"prediction": "N/A"}
                suggestions.append({"smiles": s, "results": sample_results})

            return jsonify({
                "error": "Invalid SMILES string. Please try one of these valid molecules:",
                "suggestions": suggestions
            }), 200

        all_results = {}
        for name, info in model_registry.items():
            model = info['model']
            scaler = info['scaler']
            feature_list = info['features']
            model_type = info['type']

            try:
                X = pd.DataFrame([descriptors])[feature_list]
                X_scaled = scaler.transform(X)
            except Exception as e:
                all_results[name] = {'error': f'Feature error: {e}'}
                continue

            if model_type == 'regression':
                pred = float(model.predict(X_scaled)[0])
                pred_display = round(pred, 3)
            else:
                probs = model.predict_proba(X_scaled)[0]
                pred_idx = int(np.argmax(probs))
                pred_label = info['classes'][pred_idx]
                pred_conf = probs[pred_idx]
                pred_display = f"{pred_label} ({pred_conf:.2f})"

            result_entry = {'prediction': pred_display}
            if model_type == 'classification':
                probs = model.predict_proba(X_scaled)[0]
                result_entry['probabilities'] = {
                    cls: float(prob) for cls, prob in zip(info['classes'], probs)
                }
            all_results[name] = result_entry

        return jsonify({
            'smiles': smiles,
            'molecule_name': molecule_name,
            'descriptors': descriptors,
            'results': all_results
        })
    except Exception as e:
        print(f" Prediction error: {e}")
        return jsonify({'error': f'Internal Server Error: {str(e)}'}), 500

if __name__ == '__main__':
    load_all_models()
    app.run(debug=True, host='0.0.0.0', port=5000)
