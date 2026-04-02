const examples = [
    "Software activation fee of ₹1,999 will be charged after the 14-day free trial. This fee is non-refundable and is separate from the monthly subscription of ₹499. The activation fee is mentioned in clause 8.3 of our terms of service.",
    "To cancel your Inventory Manager Pro subscription, please send a physical letter to our registered office at least 30 days before your renewal date. Cancellations via email or phone are not accepted. Your bank account will remain linked until the cancellation is processed.",
    "Monthly rent payment of ₹15,000 to Sharma Properties for shop at Block 4, Laxmi Nagar Market. Payment due on 1st of every month. No additional charges.",
    "Ek company ne call karke bola ki hamara inventory software free hai pehle 7 din. Par baad mein ₹2,999 automatically katega. Aur band karna ho toh sirf Monday ko 10-11 baje call karo. Kya yeh theek hai?"
];

function loadExample(index) {
    document.getElementById('inputText').value = examples[index];
}

async function analyze() {
    const text = document.getElementById('inputText').value.trim();
    if (!text) return;

    const btn = document.getElementById('analyzeBtn');
    const loading = document.getElementById('loading');
    const resultCard = document.getElementById('resultCard');

    btn.disabled = true;
    btn.textContent = 'Analyzing...';
    loading.style.display = 'block';
    resultCard.style.display = 'none';

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });

        const data = await response.json();

        if (data.error) {
            alert('Error: ' + data.error);
            return;
        }

        renderResult(data.result);

    } catch (err) {
        alert('Something went wrong. Make sure app.py is running and your .env key is set.');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Analyze';
        loading.style.display = 'none';
    }
}

function renderResult(r) {
    const card = document.getElementById('resultCard');

    // Verdict config — handle both English and translated verdicts
    const verdictClass = (v) => {
        if (v.includes('DARK PATTERN') || v.includes('खतरा') || v.includes('ਖ਼ਤਰਾ')) return 'verdict-danger';
        if (v.includes('SUSPICIOUS') || v.includes('संदिग्ध') || v.includes('ਸ਼ੱਕੀ')) return 'verdict-warn';
        if (v.includes('CLEAN') || v.includes('सुरक्षित') || v.includes('ਸੁਰੱਖਿਅਤ')) return 'verdict-safe';
        return 'verdict-info';
    };

    const verdictIcon = (v) => {
        if (v.includes('DARK PATTERN') || v.includes('खतरा') || v.includes('ਖ਼ਤਰਾ')) return '🚨';
        if (v.includes('SUSPICIOUS') || v.includes('संदिग्ध') || v.includes('ਸ਼ੱਕੀ')) return '⚠️';
        if (v.includes('CLEAN') || v.includes('सुरक्षित') || v.includes('ਸੁਰੱਖਿਅਤ')) return '✅';
        return '💬';
    };

    const banner = document.getElementById('verdictBanner');
    banner.className = 'verdict-banner ' + verdictClass(r.verdict);
    document.getElementById('verdictIcon').textContent = verdictIcon(r.verdict);
    document.getElementById('verdictText').textContent = r.verdict;
    document.getElementById('patternType').textContent = r.pattern_type || '';

    // Friendly message
    document.getElementById('friendlyMsg').textContent = r.friendly_message;

    // What they might miss
    const missBlock = document.getElementById('missBlock');
    if (r.what_they_might_miss) {
        missBlock.style.display = 'block';
        document.getElementById('missText').textContent = r.what_they_might_miss;
    } else {
        missBlock.style.display = 'none';
    }

    // Why dangerous
    const whyBlock = document.getElementById('whyBlock');
    if (r.explain_why_dangerous) {
        whyBlock.style.display = 'block';
        document.getElementById('whyText').textContent = r.explain_why_dangerous;
    } else {
        whyBlock.style.display = 'none';
    }

    // Recommendation
    document.getElementById('recommendation').textContent = r.recommendation;

    // Metrics — hide for general questions
    const metricsRow = document.getElementById('metricsRow');
    if (r.input_type === 'GENERAL_QUESTION') {
        metricsRow.style.display = 'none';
    } else {
        metricsRow.style.display = 'grid';
        const rv = document.getElementById('riskLevel');
        rv.textContent = r.risk_level;
        rv.className = 'value risk-' + r.risk_level;
        document.getElementById('patternVal').textContent = r.pattern_type || '—';
        document.getElementById('confidenceVal').textContent = r.confidence + '%';
        setTimeout(() => {
            document.getElementById('confidenceFill').style.width = r.confidence + '%';
        }, 100);
    }

    card.style.display = 'block';
    card.scrollIntoView({ behavior: 'smooth' });
}

// Allow Enter key (Ctrl+Enter) to submit
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('inputText').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            analyze();
        }
    });
});