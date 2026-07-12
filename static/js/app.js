const exampleMolecules = {
    'Aspirin': 'CC(=O)OC1=CC=CC=C1C(=O)O',
    'Caffeine': 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C',
    'Ibuprofen': 'CC(C)CC1=CC=C(C=C1)C(C)C(=O)O',
    'Paracetamol': 'CC(=O)Nc1ccc(O)cc1',
    'Ethanol': 'CCO'
};

const form = document.getElementById('prediction-form');
const smilesInput = document.getElementById('smiles-input');
const moleculeNameInput = document.getElementById('molecule-name');
const loadingDiv = document.getElementById('loading');
const errorDiv = document.getElementById('error');
const exampleTags = document.querySelectorAll('.example-tag');
const suggestionsDiv = document.getElementById('suggestions');
const suggestionsList = document.getElementById('suggestions-list');

document.addEventListener('DOMContentLoaded', function() {
    smilesInput.value = 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C';
    
    form.addEventListener('submit', handleFormSubmit);
    
    exampleTags.forEach(tag => {
        tag.addEventListener('click', function() {
            const smiles = this.dataset.smiles;
            const name = this.dataset.name;
            
            smilesInput.value = smiles;
            moleculeNameInput.value = name;
            
            hideResults();
            hideError();
            hideSuggestions();
        });
    });
    
    smilesInput.addEventListener('input', function() {
        hideError();
        hideSuggestions();
    });
});

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const smiles = smilesInput.value.trim();
    const moleculeName = moleculeNameInput.value.trim();
    
    if (!smiles) {
        showError('Please enter a SMILES string');
        return;
    }
    
    showLoading();
    hideError();
    
    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                smiles: smiles,
                molecule_name: moleculeName
            })
        });
        
        const data = await response.json();
        
        if (data && data.error && Array.isArray(data.suggestions) && data.suggestions.length > 0) {
            showSuggestions(data.suggestions);
            hideLoading();
            return;
        }
        
        if (!response.ok) {
            throw new Error(data.error || 'Prediction failed');
        }
        
        sessionStorage.setItem('predictionResults', JSON.stringify(data));
        window.location.href = '/results';
        
    } catch (error) {
        showError(error.message);
        hideLoading();
    }
}

function showLoading() {
    loadingDiv.classList.remove('hidden');
}

function hideLoading() {
    loadingDiv.classList.add('hidden');
}

function showError(message) {
    document.getElementById('error-message').textContent = message;
    errorDiv.classList.remove('hidden');
}

function hideError() {
    errorDiv.classList.add('hidden');
}

function showSuggestions(suggestions) {
    suggestionsList.innerHTML = suggestions.map((s, idx) => {
        return `
            <div class="suggestion-card" data-smiles="${s.smiles}">
                <div class="suggestion-header">
                    <code>${s.smiles}</code>
                    <button class="use-suggestion-btn" data-smiles="${s.smiles}">Use</button>
                </div>
                <div class="suggestion-results">
                    ${renderSuggestionResults(s.results)}
                </div>
            </div>
        `;
    }).join('');
    suggestionsDiv.classList.remove('hidden');
    suggestionsList.querySelectorAll('.use-suggestion-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const s = btn.getAttribute('data-smiles');
            smilesInput.value = s;
            form.dispatchEvent(new Event('submit'));
        });
    });
}

function hideSuggestions() {
    suggestionsDiv.classList.add('hidden');
    suggestionsList.innerHTML = '';
}

function renderSuggestionResults(results) {
    const order = ['Drug_likeness', 'Solubility', 'Permeability', 'Stability', 'Toxicity'];
    return `
        <div class="suggestion-grid">
            ${order.map(key => {
                const r = results[key];
                if (!r) return '';
                return `
                    <div class="suggestion-item">
                        <div class="suggestion-label">${key.replace('_',' ')}</div>
                        <div class="suggestion-value">${formatSuggestionValue(key, r.prediction)}</div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

function formatSuggestionValue(property, value) {
    if (property === 'Solubility' && typeof value === 'number') {
        return `${value.toFixed(0)} mg/L`;
    }
    return value;
}
