// script.js - ONCHAIN AI Dashboard Frontend
// Connects to FastAPI backend at http://localhost:8000

// ────────────────────────────────────────────────
// Configuration
// ────────────────────────────────────────────────

const API_BASE = "http://localhost:8000";   // change to production URL later

// ────────────────────────────────────────────────
// DOM Elements
// ────────────────────────────────────────────────

const navItems         = document.querySelectorAll('.nav-item');
const tabContents      = document.querySelectorAll('.tab-content');
const dynamicContent   = document.getElementById('dynamic-tab-content');
const whaleCountEl     = document.getElementById('whale-count');
const pumpCountEl      = document.getElementById('pump-count');
const scamCountEl      = document.getElementById('scam-count');
const trendingCountEl  = document.getElementById('trending-count');
const syncTimeEl       = document.getElementById('sync-time');
const refreshBtn       = document.getElementById('refresh-all');
const askAiBtn         = document.getElementById('ask-ai');
const newInsightBtn    = document.getElementById('new-insight');

// ────────────────────────────────────────────────
// API Helper
// ────────────────────────────────────────────────

async function apiFetch(endpoint) {
    try {
        const response = await fetch(API_BASE + endpoint, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API call failed (${endpoint}):`, error);
        return null;
    }
}

// ────────────────────────────────────────────────
// Dashboard - load summary stats
// ────────────────────────────────────────────────

async function loadDashboardSummary() {
    const data = await apiFetch('/dashboard-summary');
    if (!data) return;

    if (whaleCountEl)    whaleCountEl.textContent    = data.whales_count    ?? '?';
    if (trendingCountEl) trendingCountEl.textContent = data.trending_count ?? '?';

    // You can also display the AI analysis somewhere if you want
    // Example: document.getElementById('dashboard-insight').textContent = data.analysis || '';

    syncTimeEl.textContent = 'just now';
}

// ────────────────────────────────────────────────
// Whale Tracker
// ────────────────────────────────────────────────

async function loadWhaleTracker() {
    const data = await apiFetch('/whales');
    if (!data) {
        dynamicContent.innerHTML = '<p style="color:#ef4444;">Failed to load whale data</p>';
        return;
    }

    let html = `
        <h2 style="margin-bottom: 1.5rem;">Whale Tracker</h2>
        <div style="margin-bottom: 1.5rem; padding: 1rem; background: rgba(0,245,255,0.08); border-radius: 12px;">
            <strong>Gemini 2.5 Insight:</strong><br>
            ${data.analysis || 'No insight available'}
        </div>
        <table>
            <thead>
                <tr>
                    <th>Wallet</th>
                    <th>Amount (ETH)</th>
                    <th>Time</th>
                    <th>Transaction</th>
                </tr>
            </thead>
            <tbody>
    `;

    if (data.data && data.data.length > 0) {
        data.data.forEach(item => {
            html += `
                <tr>
                    <td style="font-family: monospace;">${item.wallet}</td>
                    <td style="color: #22c55e; font-weight: 600;">${item.amount_eth}</td>
                    <td>${item.time}</td>
                    <td style="font-family: monospace; color: #00f5ff;">${item.tx}</td>
                </tr>
            `;
        });
    } else {
        html += '<tr><td colspan="4" style="text-align:center; padding:2rem;">No whale transactions detected</td></tr>';
    }

    html += '</tbody></table>';

    dynamicContent.innerHTML = html;

    // Optional: update global whale count card
    if (whaleCountEl) whaleCountEl.textContent = data.metrics?.count ?? '0';
}

// ────────────────────────────────────────────────
// Pump Signals
// ────────────────────────────────────────────────

async function loadPumpSignals() {
    const data = await apiFetch('/pump-signals');
    if (!data) {
        dynamicContent.innerHTML = '<p style="color:#ef4444;">Failed to load pump signals</p>';
        return;
    }

    let html = `
        <h2 style="margin-bottom: 1.5rem; color: #f97316;">Pump Detection AI</h2>
        <div style="margin-bottom: 1.5rem; padding: 1rem; background: rgba(249,115,22,0.1); border-radius: 12px; border: 1px solid #f97316/30;">
            <strong>AI Analysis:</strong><br>
            ${data.analysis || 'No analysis available'}
        </div>
    `;

    if (data.data && data.data.length > 0) {
        data.data.forEach(signal => {
            html += `
                <div style="background: rgba(30,40,60,0.6); border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem; border-left: 4px solid #f97316;">
                    <div style="font-size: 1.4rem; font-weight: 600; color: #f97316;">${signal.token} (${signal.symbol})</div>
                    <div style="margin: 0.5rem 0; font-size: 1.3rem;">
                        Spike: <strong>${signal.spike_percent}%</strong> • Confidence: <strong>${signal.confidence}%</strong>
                    </div>
                    <div style="color: #94a3b8;">${signal.reason}</div>
                </div>
            `;
        });
    } else {
        html += '<p style="text-align:center; padding: 3rem 0;">No active pump signals detected right now</p>';
    }

    dynamicContent.innerHTML = html;

    if (pumpCountEl) pumpCountEl.textContent = data.metrics?.active_signals ?? '0';
}

// ────────────────────────────────────────────────
// Scam / Rug Alerts
// ────────────────────────────────────────────────

async function loadScamAlerts() {
    const data = await apiFetch('/scam-alerts');
    if (!data) {
        dynamicContent.innerHTML = '<p style="color:#ef4444;">Failed to load scam alerts</p>';
        return;
    }

    let html = `
        <h2 style="margin-bottom: 1.5rem; color: #ef4444;">Scam / Rug Detector</h2>
        <div style="margin-bottom: 1.5rem; padding: 1rem; background: rgba(239,68,68,0.12); border-radius: 12px; border: 1px solid #ef4444/30;">
            <strong>AI Warning Summary:</strong><br>
            ${data.analysis || 'No analysis available'}
        </div>
    `;

    if (data.data && data.data.length > 0) {
        data.data.forEach(alert => {
            const color = alert.risk === 'CRITICAL' ? '#ef4444' : alert.risk === 'HIGH' ? '#f97316' : '#eab308';
            html += `
                <div style="background: rgba(30,40,60,0.6); border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem; border-left: 4px solid ${color};">
                    <div style="font-size: 1.3rem; font-weight: 600; color: ${color};">${alert.token} – ${alert.risk}</div>
                    <div style="margin-top: 0.6rem; color: #94a3b8;">${alert.reason}</div>
                </div>
            `;
        });
    } else {
        html += '<p style="text-align:center; padding: 3rem 0; color: #22c55e;">No active scam or rug alerts at the moment</p>';
    }

    dynamicContent.innerHTML = html;

    if (scamCountEl) scamCountEl.textContent = data.metrics?.total ?? '0';
}

// ────────────────────────────────────────────────
// Trending Tokens
// ────────────────────────────────────────────────

async function loadTrending() {
    const data = await apiFetch('/trending');
    if (!data) {
        dynamicContent.innerHTML = '<p style="color:#ef4444;">Failed to load trending tokens</p>';
        return;
    }

    let html = `
        <h2 style="margin-bottom: 1.5rem;">Trending Tokens</h2>
        <div style="margin-bottom: 1.5rem; padding: 1rem; background: rgba(168,85,247,0.08); border-radius: 12px;">
            <strong>Gemini 2.5 Insight:</strong><br>
            ${data.analysis || 'No insight available'}
        </div>
        <table>
            <thead>
                <tr>
                    <th>Token</th>
                    <th>Symbol</th>
                    <th>Price (USD)</th>
                    <th>Liquidity (M)</th>
                    <th>24h Volume (M)</th>
                    <th>24h Change</th>
                </tr>
            </thead>
            <tbody>
    `;

    if (data.data && data.data.length > 0) {
        data.data.forEach(t => {
            const changeColor = t.change_24h >= 0 ? '#22c55e' : '#ef4444';
            html += `
                <tr>
                    <td>${t.token}</td>
                    <td>${t.symbol}</td>
                    <td>$${t.price_usd.toFixed(6)}</td>
                    <td>$${t.liq_usd}M</td>
                    <td>$${t.vol_24h}M</td>
                    <td style="color: ${changeColor};">${t.change_24h >= 0 ? '+' : ''}${t.change_24h}%</td>
                </tr>
            `;
        });
    } else {
        html += '<tr><td colspan="6" style="text-align:center; padding:2rem;">No trending tokens right now</td></tr>';
    }

    html += '</tbody></table>';

    dynamicContent.innerHTML = html;

    if (trendingCountEl) trendingCountEl.textContent = data.metrics?.count ?? '0';
}

// ────────────────────────────────────────────────
// Tab Switching Logic
// ────────────────────────────────────────────────

function switchTab(index) {
    // Update active nav item
    navItems.forEach((item, i) => {
        item.classList.toggle('active', i === index);
    });

    // Show/hide content areas
    tabContents.forEach((tab, i) => {
        tab.classList.toggle('active', i === index);
    });

    dynamicContent.style.display = (index === 0) ? 'none' : 'block';

    // Load data for the selected tab
    if (index === 0) {
        loadDashboardSummary();
    } else if (index === 1) {
        dynamicContent.innerHTML = '<p>Loading whale tracker...</p>';
        loadWhaleTracker();
    } else if (index === 2) {
        dynamicContent.innerHTML = '<p>Loading pump signals...</p>';
        loadPumpSignals();
    } else if (index === 4) {
        dynamicContent.innerHTML = '<p>Loading scam alerts...</p>';
        loadScamAlerts();
    } else if (index === 5) {
        dynamicContent.innerHTML = '<p>Loading trending tokens...</p>';
        loadTrending();
    } else {
        dynamicContent.innerHTML = '<div style="text-align:center; padding: 5rem 0; font-size: 1.4rem;">Coming soon...</div>';
    }
}

// ────────────────────────────────────────────────
// Event Listeners
// ────────────────────────────────────────────────

navItems.forEach(item => {
    item.addEventListener('click', e => {
        e.preventDefault();
        const index = parseInt(item.getAttribute('data-tab'));
        switchTab(index);
    });
});

if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
        loadDashboardSummary();
        // You can also reload the current tab's data here if desired
        alert('Data refreshed!');
    });
}

if (askAiBtn) {
    askAiBtn.addEventListener('click', () => {
        alert('AI Agent query not implemented in this demo version.\nYou can extend this with a text input + /ask endpoint.');
    });
}

if (newInsightBtn) {
    newInsightBtn.addEventListener('click', () => {
        alert('New insight generation not implemented yet.\nWould require a new endpoint or re-calling existing ones.');
    });
}

// ────────────────────────────────────────────────
// Initialize
// ────────────────────────────────────────────────

window.addEventListener('load', () => {
    // Start on dashboard
    switchTab(0);
    loadDashboardSummary();

    // Optional: auto-refresh every 60 seconds
    // setInterval(loadDashboardSummary, 60000);
});

console.log("ONCHAIN AI Dashboard frontend initialized");