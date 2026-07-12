import pubchempy as pcp
import pandas as pd
import numpy as np
import time
import json
from tqdm import tqdm
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
import warnings
warnings.filterwarnings('ignore')

SIZE = 500
LIMIT = 1000

def looks_organic(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return False
    atoms = {a.GetSymbol() for a in mol.GetAtoms()}
    metals = {'Na', 'K', 'Ca', 'Mg', 'Fe', 'Zn', 'Cu', 'Ag', 'Au'}
    return ('C' in atoms) and not (atoms & metals)

def predict_stability(row):
    mol = Chem.MolFromSmiles(row['SMILES'])
    if mol is None:
        return 'Unknown'
    
    patterns = [
        Chem.MolFromSmarts('[NX3](=O)=O'), # Nitro
        Chem.MolFromSmarts('OO'),          # Peroxide
        Chem.MolFromSmarts('C1OC1')         # Epoxide
    ]
    for p in patterns:
        if mol.HasSubstructMatch(p):
            return 'Unstable'
    
    if row['RotBonds'] > 8:
        return 'Unstable'
    if not (0 < row['LogP'] < 4): 
        return 'Unstable'
    
    return 'Stable'

def predict_toxicity(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return 'Unknown'
    
    toxic_patterns = [
        ('Nitro', '[NX3](=O)=O'),
        ('Halogenated', '[F,Cl,Br,I]'),
        ('Aromatic amine', 'cN'),
        ('Peroxide', 'OO'),
        ('Heavy metal', '[Hg,As,Pb,Cd]')
    ]
    
    for _, pattern in toxic_patterns:
        if mol.HasSubstructMatch(Chem.MolFromSmarts(pattern)):
            return 'Toxic'
    return 'Non-toxic'

def lipinski_rule_check(row):
    issues = 0
    if row['MW'] > 400: issues += 1  
    if row['LogP'] > 4: issues += 1   
    if row['HBD'] > 4: issues += 1    
    if row['HBA'] > 8: issues += 1    
    
    return 'Drug-like' if issues == 0 else 'Non-drug-like'

def fetch_pubchem_data(limit=1000):
    records = []
    used = set()
    cid_start = 1000
    for attempt in tqdm(range(LIMIT)):
        if len(records) >= limit:
            break
        cid = cid_start + attempt
        if cid in used:
            continue
        used.add(cid)
        try:
            compound = pcp.Compound.from_cid(cid)
            smiles = getattr(compound, 'isomeric_smiles', None) or getattr(compound, 'canonical_smiles', None)
            if not smiles or not looks_organic(smiles):
                continue
            name = getattr(compound, 'iupac_name', None) or f"Molecule_{cid}"
            records.append({'CID': cid, 'SMILES': smiles, 'Name': name})
            time.sleep(0.2)
        except Exception:
            continue
    return pd.DataFrame(records)

def compute_molecular_features(df):
    info = []
    for _, row in tqdm(df.iterrows(), total=len(df)):
        mol = Chem.MolFromSmiles(row['SMILES'])
        if mol is None:
            continue
        vals = {
            'CID': row['CID'],
            'Name': row['Name'],
            'SMILES': row['SMILES'],
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
        vals['AromaticRatio'] = aromatic_atoms / total_atoms if total_atoms > 0 else 0
        info.append(vals)
    return pd.DataFrame(info)

def refine_data(df):
    df['CanonicalSMILES'] = df['SMILES'].apply(lambda s: Chem.MolToSmiles(Chem.MolFromSmiles(s)))
    df = df.drop_duplicates(subset=['CanonicalSMILES'])
    df = df[
        (df['MW'] <= 800) & 
        (df['LogP'].between(-5, 7)) & 
        (df['TPSA'] <= 200)
    ]
    for c in ['MW', 'LogP', 'TPSA', 'HBD', 'HBA']:
        mean, std = df[c].mean(), df[c].std()
        df = df[df[c].between(mean - 3 * std, mean + 3 * std)]
    return df.dropna()

def assign_property_labels(df):
    df['LogS'] = 0.16 - 0.63 * df['LogP'] - 0.0062 * df['MW'] + 0.066 * df['RotBonds']
    df['Solubility_mol_L'] = 10 ** df['LogS']
    df['Solubility_mg_L'] = df['Solubility_mol_L'] * df['MW'] * 1000
    
    df['Permeability'] = df.apply(
        lambda row: 'High' if (row['TPSA'] < 120 and row['LogP'] < 5 and row['MW'] < 500) else 'Low', 
        axis=1
    )

    df['Stability'] = df.apply(predict_stability, axis=1) 
    df['DrugType'] = df.apply(lipinski_rule_check, axis=1)
    df['Toxicity'] = df['SMILES'].apply(predict_toxicity)

    return df

def save_results(df):
    df.to_csv('data.csv', index=False)
    meta = {
        'total_samples': len(df),
        'columns': list(df.columns),
        'source': 'PubChem (via PubChemPy)',
        'steps': ['RDKit', 'Lipinski Rule (Stricter)', 'Toxicity Detection', 'Basic Filtering'],
        'generated_on': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    json.dump(meta, open("dataset_info.json", "w"), indent=4)

def main():
    raw = fetch_pubchem_data(SIZE)
    if raw.empty:
        print("No data fetched from PubChem.")
        return
    desc = compute_molecular_features(raw)
    if desc.empty:
        print("Could not compute features.")
        return
    cleaned = refine_data(desc)
    final = assign_property_labels(cleaned)

    final = final[final['Stability'] != 'Unknown']
    
    print(final['Stability'].value_counts(normalize=True))
    print(final['DrugType'].value_counts(normalize=True))
    print(final['Permeability'].value_counts(normalize=True))
    
    save_results(final)
    print(f"\nSuccessfully saved {len(final)} to data.csv")

if __name__ == "__main__":
    main()