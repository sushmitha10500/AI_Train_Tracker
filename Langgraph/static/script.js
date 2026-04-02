// ============================================
// INDIAN RAILWAY ROUTE PLANNER - FRONTEND LOGIC
// ============================================

const API_BASE_URL = 'http://89.116.20.129:5005';
//const API_BASE_URL = 'http://localhost:5000';
const API_ENDPOINT = '/api/smart_query';

// DOM Elements
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const loadingSection = document.getElementById('loadingSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');
const journeyInfo = document.getElementById('journeyInfo');
const aiRecommendation = document.getElementById('aiRecommendation');
const trainsContainer = document.getElementById('trainsContainer');
const errorTitle = document.getElementById('errorTitle');
const errorMessage = document.getElementById('errorMessage');
const retryBtn = document.getElementById('retryBtn');
const quickBtns = document.querySelectorAll('.quick-btn');
const loadingText = document.getElementById('loadingText');

// Loading steps
const loadingSteps = [
    { id: 'step1', text: 'Understanding your query...' },
    { id: 'step2', text: 'Finding railway stations...' },
    { id: 'step3', text: 'Searching available routes...' },
    { id: 'step4', text: 'Optimizing recommendations...' }
];

let currentLoadingStep = 0;
let loadingInterval = null;

// ============================================
// EVENT LISTENERS
// ============================================

searchBtn.addEventListener('click', handleSearch);
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSearch();
});

retryBtn.addEventListener('click', () => {
    errorSection.style.display = 'none';
    searchInput.focus();
});

quickBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        searchInput.value = btn.dataset.query;
        handleSearch();
    });
});

// ============================================
// MAIN SEARCH HANDLER
// ============================================

async function handleSearch() {
    const query = searchInput.value.trim();

    if (!query) {
        showError('Please enter a search query', 'Tell us where you want to go!');
        return;
    }

    // Hide previous results and errors
    hideAllSections();

    // Show loading
    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}${API_ENDPOINT}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query })
        });

        const data = await response.json();

        // Stop loading animation
        stopLoading();

        if (data.success) {
            displayResults(data);
        } else {
            showError(
                data.message || 'No routes found',
                data.suggestion || 'Please try different stations or check your input.'
            );
        }
    } catch (error) {
        stopLoading();
        console.error('API Error:', error);
        showError(
            'Connection Error',
            'Unable to connect to the server. Please make sure the backend is running on port 5000.'
        );
    }
}

// ============================================
// LOADING MANAGEMENT
// ============================================

function showLoading() {
    loadingSection.style.display = 'block';
    currentLoadingStep = 0;

    // Animate loading steps
    loadingInterval = setInterval(() => {
        // Remove active class from all steps
        document.querySelectorAll('.step').forEach(step => {
            step.classList.remove('active');
        });

        // Add active class to current step
        const currentStep = loadingSteps[currentLoadingStep];
        const stepElement = document.getElementById(currentStep.id);
        if (stepElement) {
            stepElement.classList.add('active');
            loadingText.textContent = currentStep.text;
        }

        currentLoadingStep = (currentLoadingStep + 1) % loadingSteps.length;
    }, 1000);
}

function stopLoading() {
    clearInterval(loadingInterval);
    loadingSection.style.display = 'none';
}

// ============================================
// RESULTS DISPLAY
// ============================================

function displayResults(data) {
    resultsSection.style.display = 'block';

    // Display journey info
    displayJourneyInfo(data.journey);

    // Display AI recommendation
    if (data.aiRecommendation) {
        displayAIRecommendation(data.aiRecommendation);
    }

    // Display available trains
    displayTrains(data.availableTrains);
}

function displayJourneyInfo(journey) {
    journeyInfo.innerHTML = `
        <div class="journey-route">
            <div class="journey-station">${journey.from.split('(')[0].trim()}</div>
            <div class="journey-arrow">→</div>
            <div class="journey-station">${journey.to.split('(')[0].trim()}</div>
        </div>
        <div class="journey-stats">
            <div class="stat">
                <div class="stat-value">${journey.totalOptions}</div>
                <div class="stat-label">Routes Found</div>
            </div>
            <div class="stat">
                <div class="stat-value">${journey.searchDate}</div>
                <div class="stat-label">Search Date</div>
            </div>
        </div>
    `;
}

function displayAIRecommendation(recommendation) {
    const highlightsHTML = recommendation.highlights
        ? recommendation.highlights.map(h => `<div class="highlight">${h}</div>`).join('')
        : '';

    aiRecommendation.innerHTML = `
        <div class="ai-badge">
            <span>🤖</span>
            <span>AI Recommendation</span>
        </div>
        <div class="ai-reason">${recommendation.reason}</div>
        ${recommendation.totalJourneyTime ? `<div style="color: var(--text-secondary); margin-top: 0.5rem;">Total Journey: ${recommendation.totalJourneyTime}</div>` : ''}
        ${highlightsHTML ? `<div class="ai-highlights">${highlightsHTML}</div>` : ''}
    `;
    aiRecommendation.style.display = 'block';
}

function displayTrains(trains) {
    trainsContainer.innerHTML = '';

    trains.forEach((train, index) => {
        const trainCard = createTrainCard(train, index);
        trainsContainer.appendChild(trainCard);
    });
}

function createTrainCard(train, index) {
    const card = document.createElement('div');
    card.className = `train-card ${train.isRecommended ? 'recommended' : ''}`;

    let contentHTML = `
        <div class="train-header">
            <div class="train-type">${train.type}</div>
            ${train.isRecommended ? '<div class="recommended-badge">⭐ Recommended</div>' : ''}
        </div>
    `;

    // Direct train
    if (train.trainNumber) {
        contentHTML += `
            <div class="train-details">
                <div class="detail-group">
                    <div class="detail-label">Train Number</div>
                    <div class="detail-value">${train.trainNumber}</div>
                </div>
                <div class="detail-group">
                    <div class="detail-label">Train Name</div>
                    <div class="detail-value">${train.trainName}</div>
                </div>
                <div class="detail-group">
                    <div class="detail-label">Departure</div>
                    <div class="detail-value">${train.departure.time}</div>
                </div>
                <div class="detail-group">
                    <div class="detail-label">Arrival</div>
                    <div class="detail-value">${train.arrival.time}</div>
                </div>
                <div class="detail-group">
                    <div class="detail-label">Journey Time</div>
                    <div class="detail-value">${train.totalJourneyTime}</div>
                </div>
                <div class="detail-group">
                    <div class="detail-label">Distance</div>
                    <div class="detail-value">${train.totalDistance}</div>
                </div>
            </div>
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(79, 172, 254, 0.1); border-radius: 8px; color: var(--accent-blue);">
                ✓ ${train.connections}
            </div>
        `;
    }
    // Connecting trains
    else if (train.trains) {
        contentHTML += `
            <div class="train-details">
                <div class="detail-group">
                    <div class="detail-label">Total Journey Time</div>
                    <div class="detail-value">${train.totalJourneyTime}</div>
                </div>
                <div class="detail-group">
                    <div class="detail-label">Total Distance</div>
                    <div class="detail-value">${train.totalDistance}</div>
                </div>
                <div class="detail-group">
                    <div class="detail-label">Connections</div>
                    <div class="detail-value">${train.connections}</div>
                </div>
            </div>
            
            <div class="train-segments">
                <h4 style="margin-bottom: 1rem; color: var(--accent-blue);">Route Details</h4>
                ${train.trains.map((segment, idx) => createSegmentHTML(segment, idx)).join('')}
                ${train.waitingTimes ? train.waitingTimes.map(waiting => createWaitingTimeHTML(waiting)).join('') : ''}
            </div>
        `;
    }

    if (train.alternative_note) {
        contentHTML += `
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(255, 165, 0, 0.1); border-radius: 8px; border-left: 3px solid #ff9a56;">
                ℹ️ ${train.alternative_note}
            </div>
        `;
    }

    card.innerHTML = contentHTML;
    return card;
}

function createSegmentHTML(segment, index) {
    return `
        <div class="segment">
            <div class="segment-header">
                <div>
                    <span class="train-number">${segment.trainNumber}</span>
                    <span class="train-name">${segment.trainName}</span>
                </div>
                <div style="color: var(--text-secondary); font-size: 0.875rem;">
                    ${segment.duration} | ${segment.distance}
                </div>
            </div>
            <div class="segment-route">
                <div class="station-time">
                    <span class="station-code">${segment.from}</span>
                    <span class="time">${segment.departure}</span>
                </div>
                <div class="route-arrow"></div>
                <div class="station-time" style="text-align: right;">
                    <span class="station-code">${segment.to}</span>
                    <span class="time">${segment.arrival}</span>
                </div>
            </div>
        </div>
    `;
}

function createWaitingTimeHTML(waiting) {
    const statusClass = waiting.status.includes('COMFORTABLE') ? 'comfortable' :
        waiting.status.includes('TIGHT') ? 'tight' : '';

    return `
        <div class="waiting-time ${statusClass}">
            <div class="waiting-station">⏱️ Waiting at ${waiting.atStation}</div>
            <div class="waiting-duration">
                <strong>${waiting.waitingTime}</strong> - ${waiting.status}
            </div>
            <div style="font-size: 0.875rem; color: var(--text-secondary); margin-top: 0.25rem;">
                ${waiting.advice}
            </div>
        </div>
    `;
}

// ============================================
// ERROR HANDLING
// ============================================

function showError(title, message) {
    errorSection.style.display = 'block';
    errorTitle.textContent = title;
    errorMessage.textContent = message;
}

function hideAllSections() {
    loadingSection.style.display = 'none';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
    aiRecommendation.style.display = 'none';
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

// Auto-focus search input on page load
window.addEventListener('load', () => {
    searchInput.focus();
});

// Add enter key support for better UX
document.addEventListener('keydown', (e) => {
    // Focus search input when user starts typing (if not already focused)
    if (e.key.length === 1 &&
        document.activeElement !== searchInput &&
        !e.ctrlKey &&
        !e.altKey &&
        !e.metaKey) {
        searchInput.focus();
    }
});

console.log('🚆 Indian Railway Route Planner - Frontend Loaded');
console.log('API Endpoint:', `${API_BASE_URL}${API_ENDPOINT}`);
