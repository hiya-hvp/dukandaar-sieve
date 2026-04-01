from flask import Flask, request, jsonify, render_template_string
from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are दुकानdaar's SIEVE — a trusted financial guardian (like a smart older brother) for small Indian shopkeepers (kirana walas, street vendors, small merchants).

DEFAULT LANGUAGE: Always respond in English unless the user writes to you in Hindi or Hinglish. If they write in Hindi, reply in Hindi. If Hinglish, reply in Hinglish. If English or anything else, reply in English. Be warm, simple, like a trusted friend — not a corporate tool.

FIRST: Understand what the person is actually asking. There are 3 types of inputs:

TYPE 1 — GENERAL QUESTION (not about a payment at all)
Examples: "how does this work", "what is this tool", "is this free"
→ These are NOT payment queries. Reply helpfully in their language, explain what SIEVE does and how it helps them. DO NOT run dark pattern analysis.

TYPE 2 — PAYMENT/SUBSCRIPTION TEXT (actual terms, agreement, or description)
→ Analyze deeply for dark patterns. Your JOB here is to find what a shopkeeper would MISS — buried clauses, confusing terms, tricky fine print. If it says "free trial auto-converts" in plain simple language — that's still a trap because the SHOPKEEPER may not realize it.

TYPE 3 — SITUATION DESCRIPTION (shopkeeper describing something that happened or asking if something is suspicious)
Examples: "a company called me and asked me to take a subscription", "₹2000 was deducted without notice", "I got this email, what should I do"
→ Treat like a concerned friend. Help them understand the risk. Give practical next steps.

For TYPE 2 and TYPE 3, detect these dark patterns (go DEEP, not surface-level):
1. HIDDEN FEES — fees NOT mentioned upfront, buried in fine print or clauses
2. SUBSCRIPTION TRAP — hard to cancel, requires physical letter / specific hours only
3. DRIP PRICING — price looks low but keeps adding up at checkout or over time
4. BASKET SNEAKING — extra charges added without clear consent
5. FORCED CONTINUITY — free trial silently converts to paid
6. ROACH MOTEL — easy to join, nearly impossible to exit
7. VISHING / SCAM CALL — unsolicited calls pressuring merchants to pay or share details
8. FAKE URGENCY — "offer ends today", pressure tactics to force quick payment decisions
9. DELINK BARRIER — making it very hard to remove linked bank account

IMPORTANT RULES:
- Do NOT flag something as dangerous just because it mentions money or payments — many are legitimate
- A straightforward rent payment, salary payment, utility bill = CLEAN
- Be honest about confidence. If you're not sure, say so.
- For TYPE 2: Your value is in explaining WHY something is dangerous in terms the shopkeeper understands — not just repeating what's written
- Always give a PRACTICAL next step — what should they do RIGHT NOW?

Respond ONLY in this exact JSON format:
{
  "input_type": "GENERAL_QUESTION" or "PAYMENT_ANALYSIS" or "SITUATION_HELP",
  "verdict": "DARK PATTERN DETECTED" or "PAYMENT CLEAN" or "SUSPICIOUS — VERIFY" or "NOT A PAYMENT QUERY",
  "risk_level": "HIGH" or "MEDIUM" or "LOW" or "NONE" or "NA",
  "pattern_type": "name of the dark pattern, or null",
  "friendly_message": "1-2 sentences in THEIR language — warm, like a trusted friend telling them what's going on",
  "what_they_might_miss": "For PAYMENT_ANALYSIS only — the specific thing buried/hidden that a busy shopkeeper would overlook. null for others.",
  "recommendation": "Practical next step in their language — concrete, actionable, simple",
  "confidence": a number 0-100,
  "explain_why_dangerous": "For dark patterns only — explain in simple words WHY this hurts them specifically as a small merchant. null if clean."
}"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>दुकानdaar — SIEVE Engine</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background: #0D1B2A;
            color: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px 20px;
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
        }

        .header h1 {
            font-size: 3rem;
            color: #F4A261;
            font-weight: 800;
            letter-spacing: -1px;
        }

        .header .subtitle {
            font-size: 1rem;
            color: #A0B4C8;
            margin-top: 8px;
        }

        .badge {
            display: inline-block;
            background: #E76F51;
            color: white;
            font-size: 0.7rem;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 20px;
            margin-top: 10px;
            letter-spacing: 1px;
        }

        .card {
            background: #1A2A3A;
            border: 1px solid #2A3A4A;
            border-radius: 16px;
            padding: 32px;
            width: 100%;
            max-width: 720px;
            margin-bottom: 24px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }

        .card h2 {
            font-size: 1rem;
            color: #F4A261;
            font-weight: 700;
            margin-bottom: 16px;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        textarea {
            width: 100%;
            background: #0D1B2A;
            border: 1px solid #2A3A4A;
            border-radius: 10px;
            color: #ffffff;
            font-size: 0.95rem;
            padding: 16px;
            resize: vertical;
            min-height: 120px;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s;
        }

        textarea:focus { border-color: #F4A261; }
        textarea::placeholder { color: #4A6A8A; }

        .examples {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 12px;
            align-items: center;
        }

        .examples-label {
            font-size: 0.8rem;
            color: #4A6A8A;
        }

        .example-btn {
            background: #0D1B2A;
            border: 1px solid #2A3A4A;
            color: #A0B4C8;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.2s;
            font-family: inherit;
        }

        .example-btn:hover {
            border-color: #F4A261;
            color: #F4A261;
        }

        .analyze-btn {
            width: 100%;
            background: linear-gradient(135deg, #F4A261, #E76F51);
            color: white;
            border: none;
            padding: 16px;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            margin-top: 16px;
            transition: opacity 0.2s;
            letter-spacing: 0.5px;
            font-family: inherit;
        }

        .analyze-btn:hover { opacity: 0.9; }
        .analyze-btn:disabled { opacity: 0.5; cursor: not-allowed; }

        .result-card {
            display: none;
            background: #1A2A3A;
            border-radius: 16px;
            padding: 32px;
            width: 100%;
            max-width: 720px;
            margin-bottom: 24px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }

        .verdict-banner {
            border-radius: 10px;
            padding: 20px 24px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .verdict-danger { background: rgba(230,57,70,0.15); border: 1px solid #E63946; }
        .verdict-safe   { background: rgba(46,196,182,0.15); border: 1px solid #2EC4B6; }
        .verdict-warn   { background: rgba(255,209,102,0.12); border: 1px solid #FFD166; }
        .verdict-info   { background: rgba(100,160,255,0.12); border: 1px solid #64a0ff; }

        .verdict-icon { font-size: 2.5rem; }

        .verdict-text h3 { font-size: 1.2rem; font-weight: 800; }
        .verdict-danger .verdict-text h3 { color: #E63946; }
        .verdict-safe   .verdict-text h3 { color: #2EC4B6; }
        .verdict-warn   .verdict-text h3 { color: #FFD166; }
        .verdict-info   .verdict-text h3 { color: #64a0ff; }

        .verdict-text p { font-size: 0.85rem; color: #A0B4C8; margin-top: 4px; }

        .friendly-msg {
            background: #0D1B2A;
            border-radius: 10px;
            padding: 16px 20px;
            margin-bottom: 16px;
            font-size: 1rem;
            line-height: 1.65;
            color: #e8edf5;
            font-weight: 500;
        }

        .detail-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 16px;
            margin-bottom: 16px;
        }

        .detail-box {
            background: #0D1B2A;
            border-radius: 10px;
            padding: 16px;
        }

        .detail-box .label {
            font-size: 0.7rem;
            color: #A0B4C8;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-bottom: 6px;
        }

        .detail-box .value {
            font-size: 1rem;
            font-weight: 700;
            color: #F4A261;
        }

        .risk-HIGH   { color: #E63946 !important; }
        .risk-MEDIUM { color: #E76F51 !important; }
        .risk-LOW    { color: #FFD166 !important; }
        .risk-NONE, .risk-NA { color: #2EC4B6 !important; }

        .block-label {
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-bottom: 8px;
            color: #A0B4C8;
        }

        .block-text {
            font-size: 0.95rem;
            color: #ffffff;
            line-height: 1.6;
        }

        .miss-block {
            background: rgba(230,57,70,0.07);
            border: 1px solid rgba(230,57,70,0.2);
            border-radius: 10px;
            padding: 16px 20px;
            margin-bottom: 16px;
        }
        .miss-block .block-label { color: #e66; }
        .miss-block .block-text  { color: #ffcccc; }

        .explanation-box {
            background: #0D1B2A;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 16px;
        }

        .recommendation-box {
            background: rgba(244,162,97,0.1);
            border: 1px solid rgba(244,162,97,0.3);
            border-radius: 10px;
            padding: 16px 20px;
            display: flex;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 16px;
        }

        .recommendation-box .icon { font-size: 1.2rem; margin-top: 2px; flex-shrink: 0; }
        .recommendation-box p { font-size: 0.9rem; color: #F4A261; line-height: 1.5; }

        .confidence-bar-wrap { margin-top: 6px; }
        .confidence-bar { height: 6px; background: #1A2A3A; border-radius: 3px; overflow: hidden; }
        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, #F4A261, #E76F51);
            border-radius: 3px;
            transition: width 0.8s ease;
        }

        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #A0B4C8;
            font-size: 0.9rem;
        }

        .footer {
            text-align: center;
            color: #4A6A8A;
            font-size: 0.8rem;
            margin-top: 20px;
        }
        .footer span { color: #F4A261; }
    </style>
</head>
<body>

    <div class="header">
        <h1>दुकानdaar</h1>
        <p class="subtitle">Autonomous Financial Guardian for India's SMB Merchants</p>
        <span class="badge">🧾 SIEVE ENGINE — DARK PATTERN DETECTOR</span>
    </div>

    <div class="card">
        <h2>🔍 Analyze a Payment or Subscription</h2>
        <textarea id="inputText" placeholder="Paste a subscription description, payment terms, or transaction detail here...

Example: 'Free trial for 7 days. After trial ends, ₹2,999/month will be automatically charged. To cancel, call our helpline between 10am-12pm Monday to Wednesday only.'"></textarea>

        <div class="examples">
            <span class="examples-label">Try:</span>
            <button class="example-btn" onclick="loadExample(0)">Hidden Activation Fee</button>
            <button class="example-btn" onclick="loadExample(1)">Subscription Trap</button>
            <button class="example-btn" onclick="loadExample(2)">Legitimate Payment</button>
            <button class="example-btn" onclick="loadExample(3)">Drip Pricing</button>
        </div>

        <button class="analyze-btn" onclick="analyze()" id="analyzeBtn">
            Analyze for Dark Patterns
        </button>
    </div>

    <div class="loading" id="loading">
        Analyzing with SIEVE Engine...
    </div>

    <div class="result-card" id="resultCard">
        <div class="verdict-banner" id="verdictBanner">
            <div class="verdict-icon" id="verdictIcon"></div>
            <div class="verdict-text">
                <h3 id="verdictText"></h3>
                <p id="patternType"></p>
            </div>
        </div>

        <div class="friendly-msg" id="friendlyMsg"></div>

        <div id="missBlock" class="miss-block" style="display:none">
            <div class="block-label">⚠️ What you might have missed</div>
            <div class="block-text" id="missText"></div>
        </div>

        <div id="whyBlock" class="explanation-box" style="display:none">
            <div class="block-label">💸 How this could hurt you</div>
            <div class="block-text" id="whyText"></div>
        </div>

        <div class="recommendation-box">
            <div class="icon">💡</div>
            <p id="recommendation"></p>
        </div>

        <div class="detail-grid">
            <div class="detail-box">
                <div class="label">Risk Level</div>
                <div class="value" id="riskLevel"></div>
            </div>
            <div class="detail-box">
                <div class="label">Pattern</div>
                <div class="value" id="patternVal" style="font-size:0.8rem; margin-top:2px;"></div>
            </div>
            <div class="detail-box">
                <div class="label">Confidence</div>
                <div class="value" id="confidenceVal"></div>
                <div class="confidence-bar-wrap">
                    <div class="confidence-bar">
                        <div class="confidence-fill" id="confidenceFill" style="width:0%"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="footer">
        Built for <span>Protex Hackathon 2026</span> · Powered by <span>Groq LLaMA 3.3</span> · Track 2 & 3
    </div>

    <script>
        const examples = [
            "Software activation fee of ₹1,999 will be charged after the 14-day free trial. This fee is non-refundable and is separate from the monthly subscription of ₹499. The activation fee is mentioned in clause 8.3 of our terms of service.",
            "To cancel your Inventory Manager Pro subscription, please send a physical letter to our registered office at least 30 days before your renewal date. Cancellations via email or phone are not accepted. Your bank account will remain linked until the cancellation is processed.",
            "Monthly rent payment of ₹15,000 to Sharma Properties for shop at Block 4, Laxmi Nagar Market. Payment due on 1st of every month. No additional charges.",
            "Start your billing software free! ₹0 for the first month. Standard plan ₹199/month. Note: GST filing module ₹149/month extra. Priority support ₹99/month. Data backup ₹79/month."
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
                if (data.error) { alert('Error: ' + data.error); return; }
                renderResult(data.result);

            } catch (err) {
                alert('Something went wrong. Check your API key in .env');
            } finally {
                btn.disabled = false;
                btn.textContent = 'Analyze for Dark Patterns';
                loading.style.display = 'none';
            }
        }

        function renderResult(r) {
            const card = document.getElementById('resultCard');

            const config = {
                'DARK PATTERN DETECTED': { cls: 'verdict-danger', icon: '🚨' },
                'SUSPICIOUS \u2014 VERIFY': { cls: 'verdict-warn', icon: '⚠️' },
                'PAYMENT CLEAN':            { cls: 'verdict-safe', icon: '✅' },
                'NOT A PAYMENT QUERY':      { cls: 'verdict-info', icon: '💬' }
            };

            const cfg = config[r.verdict] || { cls: 'verdict-info', icon: '💬' };
            const banner = document.getElementById('verdictBanner');
            banner.className = 'verdict-banner ' + cfg.cls;

            document.getElementById('verdictIcon').textContent = cfg.icon;
            document.getElementById('verdictText').textContent = r.verdict;
            document.getElementById('patternType').textContent = r.pattern_type ? 'Pattern: ' + r.pattern_type : 'No deceptive patterns found';

            document.getElementById('friendlyMsg').textContent = r.friendly_message;

            const missBlock = document.getElementById('missBlock');
            if (r.what_they_might_miss) {
                missBlock.style.display = 'block';
                document.getElementById('missText').textContent = r.what_they_might_miss;
            } else { missBlock.style.display = 'none'; }

            const whyBlock = document.getElementById('whyBlock');
            if (r.explain_why_dangerous) {
                whyBlock.style.display = 'block';
                document.getElementById('whyText').textContent = r.explain_why_dangerous;
            } else { whyBlock.style.display = 'none'; }

            document.getElementById('recommendation').textContent = r.recommendation;

            const rv = document.getElementById('riskLevel');
            rv.textContent = r.risk_level;
            rv.className = 'value risk-' + r.risk_level;

            document.getElementById('patternVal').textContent = r.pattern_type || '—';
            document.getElementById('confidenceVal').textContent = r.confidence + '%';

            setTimeout(() => {
                document.getElementById('confidenceFill').style.width = r.confidence + '%';
            }, 100);

            card.style.display = 'block';
            card.scrollIntoView({ behavior: 'smooth' });
        }
    </script>
</body>
</html>"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "Please provide some text to analyze."})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this:\n\n{text}"}
            ],
            temperature=0.15,
            max_tokens=700
        )

        raw = response.choices[0].message.content.strip()

        if "```" in raw:
            parts = raw.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                try:
                    result = json.loads(part)
                    return jsonify({"result": result})
                except:
                    continue

        result = json.loads(raw)
        return jsonify({"result": result})

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    print("\n✅ दुकानdaar SIEVE Engine is running!")
    print("👉 Open http://localhost:5000\n")
    app.run(debug=True, port=5000)