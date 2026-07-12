document.addEventListener('DOMContentLoaded', function() {
    const resultsData = sessionStorage.getItem('predictionResults');
    
    if (!resultsData) {
        window.location.href = '/';
        return;
    }
    
    const data = JSON.parse(resultsData);
    displayAllResults(data);
});

function displayAllResults(data) {
    const moleculeTitle = document.getElementById('molecule-title');
    const smilesDisplay = document.getElementById('smiles-display');
    
    if (data.molecule_name) {
        moleculeTitle.textContent = `${data.molecule_name} Analysis`;
    }
    smilesDisplay.textContent = data.smiles;
    
    const properties = ['Drug_likeness', 'Solubility', 'Permeability', 'Stability', 'Toxicity'];
    
    properties.forEach(property => {
        const result = data.results[property];
        displayPropertyResult(property, result);
    });
    
    displaySummary(data.results);
}

function displayPropertyResult(property, result) {
    const propertyKey = property.toLowerCase().replace('_', '-');

    const badge = document.getElementById(`${propertyKey}-badge`);
    const predictionSpan = document.getElementById(`${propertyKey}-prediction`);
    
    if (!result || result.error) {
        predictionSpan.textContent = result?.error || 'No prediction available';
        badge.className = 'prediction-badge error';
        const explanationDiv = document.getElementById(`${propertyKey}-explanation`);
        explanationDiv.innerHTML = ''; 
        const confidenceDiv = document.getElementById(`${propertyKey}-confidence`);
        confidenceDiv.innerHTML = '';
        return;
    }
    
    if (result.prediction === undefined || result.prediction === null) {
        predictionSpan.textContent = 'N/A';
        badge.className = 'prediction-badge error';
        const explanationDiv = document.getElementById(`${propertyKey}-explanation`);
        explanationDiv.innerHTML = ''; 
        const confidenceDiv = document.getElementById(`${propertyKey}-confidence`);
        confidenceDiv.innerHTML = '';
        return;
    }
    
    predictionSpan.textContent = formatPrediction(result.prediction, property);
    badge.className = `prediction-badge ${getPredictionClass(result.prediction, property)}`;
    
    const explanationDiv = document.getElementById(`${propertyKey}-explanation`);
    if (result.explanation) {
        explanationDiv.innerHTML = result.explanation.split('\n').map(line => 
            `<div class="explanation-item">${line}</div>`
        ).join('');
    } else {
        explanationDiv.innerHTML = '';
    }
    
    const confidenceDiv = document.getElementById(`${propertyKey}-confidence`);
    if (result.probabilities) {
        confidenceDiv.innerHTML = `
            <div class="confidence-scores">
                <h4>Confidence Scores:</h4>
                ${Object.entries(result.probabilities).map(([key, value]) => 
                    `<div class="confidence-item">
                        <span class="confidence-label">${key}:</span>
                        <span class="confidence-value">${(typeof value === 'number' ? value * 100 : parseFloat(value) * 100).toFixed(1)}%</span>
                    </div>`
                ).join('')}
            </div>
        `;
    } else {
        confidenceDiv.innerHTML = `<div class="confidence-scores"><h4>Regression Model</h4><p>Continuous value prediction</p></div>`;
    }
}

function displaySummary(results) {
    const summaryContent = document.getElementById('summary-content');

    const clean = (val) => {
        if (!val) return null;
        if (typeof val === 'number') return val;
        return val.replace(/\(.*?\)/g, '').trim().toLowerCase(); 
    };

    const getPrediction = (prop) => clean(results[prop]?.prediction);

    const drugLike = ['drug-like', 'yes', 'true'].includes(getPrediction('Drug_likeness'));
    const solubilityVal = results.Solubility?.prediction;
    const highSolubility = typeof solubilityVal === 'number' ? solubilityVal > 1000 : parseFloat(solubilityVal) > 1000;

    const highPermeability = ['high', 'yes', 'true'].includes(getPrediction('Permeability'));
    const highStability = ['stable', 'yes', 'true'].includes(getPrediction('Stability'));
    const lowToxicity = ['non-toxic', 'low', 'safe', 'yes'].includes(getPrediction('Toxicity'));

    const positiveCount = [drugLike, highSolubility, highPermeability, highStability, lowToxicity]
        .filter(Boolean).length;

    let summaryText = '';
    let overallClass = '';

    if (positiveCount >= 4) {
        summaryText = 'Excellent drug candidate with favorable properties across all metrics.';
        overallClass = 'excellent';
    } else if (positiveCount >= 3) {
        summaryText = 'Good drug candidate with mostly favorable properties.';
        overallClass = 'good';
    } else if (positiveCount >= 2) {
        summaryText = 'Moderate drug candidate with mixed properties.';
        overallClass = 'moderate';
    } else {
        summaryText = 'Poor drug candidate with unfavorable properties.';
        overallClass = 'poor';
    }

    summaryContent.innerHTML = `
        <div class="summary-text ${overallClass}">
            <h3>Overall Assessment: ${positiveCount}/5 Properties Favorable</h3>
            <p>${summaryText}</p>
        </div>
        <div class="summary-details">
            <div class="summary-item ${drugLike ? 'favorable' : 'unfavorable'}">
                <i class="fas fa-pills"></i>
                <span>Drug-Likeness: ${results.Drug_likeness?.prediction || 'N/A'}</span>
            </div>
            <div class="summary-item ${highSolubility ? 'favorable' : 'unfavorable'}">
                <i class="fas fa-tint"></i>
                <span>Solubility: ${results.Solubility?.prediction || 'N/A'}</span>
            </div>
            <div class="summary-item ${highPermeability ? 'favorable' : 'unfavorable'}">
                <i class="fas fa-exchange-alt"></i>
                <span>Permeability: ${results.Permeability?.prediction || 'N/A'}</span>
            </div>
            <div class="summary-item ${highStability ? 'favorable' : 'unfavorable'}">
                <i class="fas fa-shield-alt"></i>
                <span>Stability: ${results.Stability?.prediction || 'N/A'}</span>
            </div>
            <div class="summary-item ${lowToxicity ? 'favorable' : 'unfavorable'}">
                <i class="fas fa-exclamation-triangle"></i>
                <span>Toxicity: ${results.Toxicity?.prediction || 'N/A'}</span>
            </div>
        </div>
    `;
}

function formatPrediction(prediction, property) {
    if (property === 'Solubility') {
        if (typeof prediction === 'number') {
            return `${prediction.toFixed(0)} mg/L`;
        }
        return `${prediction} mg/L`;
    }
    return prediction;
}

function getPredictionClass(prediction, property) {
    const val = (typeof prediction === 'string') ? prediction.trim().toLowerCase() : prediction;

    if (property === 'Drug_likeness') {
        return val === 'drug-like' ? 'favorable' : 'unfavorable';
    }
    if (property === 'Permeability') {
        return val === 'high' ? 'favorable' : 'unfavorable';
    }
    if (property === 'Stability') {
        return val === 'stable' ? 'favorable' : 'unfavorable';
    }
    if (property === 'Toxicity') {
        return val === 'non-toxic' || val === 'low' ? 'favorable' : 'unfavorable';
    }
    if (property === 'Solubility') {
        if (typeof val === 'number') {
            return val > 10000 ? 'favorable' : 'unfavorable';
        }
        return 'unfavorable';
    }
    return '';
}

function getDescriptorLabel(key) {
    const labels = {
        'MW': 'Molecular Weight',
        'LogP': 'LogP',
        'TPSA': 'TPSA',
        'HBD': 'H-Bond Donors',
        'HBA': 'H-Bond Acceptors',
        'RotBonds': 'Rotatable Bonds',
        'RingCount': 'Rings',
        'AromaticRings': 'Aromatic Rings',
        'AromaticRatio': 'Aromaticity'
    };
    return labels[key] || key;
}

function formatDescriptorValue(key, value) {
    if (key === 'MW') {
        return `${value.toFixed(1)} g/mol`;
    }
    if (key === 'LogP') {
        return value.toFixed(2);
    }
    if (key === 'TPSA') {
        return `${value.toFixed(1)} Å²`;
    }
    if (key === 'AromaticRatio') {
        return `${(value * 100).toFixed(1)}%`;
    }
    return value.toFixed(1);
}
