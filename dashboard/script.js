const API_URL = "http://127.0.0.1:8000/predict";

// Risk thresholds — must match api/main.py get_risk_level() exactly:
// probability >= 0.66 → High, >= 0.33 → Medium, < 0.33 → Low
function getRiskLevel(probability) {
  if (probability >= 0.66) return "High";
  if (probability >= 0.33) return "Medium";
  return "Low";
}

// ── DOM refs ──────────────────────────────────────────────────────
const form            = document.getElementById("predict-form");
const submitBtn       = document.getElementById("submit-btn");
const btnText         = document.getElementById("btn-text");
const btnSpinner      = document.getElementById("btn-spinner");
const formError       = document.getElementById("form-error");
const resultPlaceholder = document.getElementById("result-placeholder");
const resultContent   = document.getElementById("result-content");
const probValue         = document.getElementById("prob-value");
const riskBadge         = document.getElementById("risk-badge");
const predictionVerdict = document.getElementById("prediction-verdict");
const segmentNameText   = document.getElementById("segment-name-text");
const recommendationText = document.getElementById("recommendation-text");
const supportingDataText = document.getElementById("supporting-data-text");

let doughnutChart = null;

// ── Churn Playbook Rules (Derived from SQL & Statistical Findings) ────
const CHURN_PLAYBOOK = [
  {
    id: 1,
    name: "Critical Risk — High-Value New Customer",
    risk_level: "Critical",
    match: (p) => p.Contract === "Month-to-month" && p.tenure < 12 && p.MonthlyCharges > 70.0,
    action: "Priority retention outreach within 48 hours; offer contract upgrade discount or loyalty credit; assign dedicated account representative.",
    supporting_data: "47.68% 1st-year churn rate; 814 target accounts identified in SQL representing $323,148/month in revenue at stake."
  },
  {
    id: 2,
    name: "Critical Risk — Unsupported Fiber Customer",
    risk_level: "Critical",
    match: (p) => p.InternetService === "Fiber optic" && p.OnlineSecurity === "No" && p.TechSupport === "No",
    action: "Proactively offer free 90-day trial of Tech Support & Online Security bundle; initiate onboarding check-in call.",
    supporting_data: "55.01% churn rate for this exact service combination vs 17.05% for all other customer profiles."
  },
  {
    id: 3,
    name: "High Risk — Manual Payment, Month-to-Month",
    risk_level: "High",
    match: (p) => p.PaymentMethod === "Electronic check" && p.Contract === "Month-to-month",
    action: "Encourage migration to automated recurring payment (Credit Card / Bank Transfer) via a $5-$10 bill credit incentive.",
    supporting_data: "45.29% churn rate for Electronic check users vs 15.25% for Auto Credit Card and 16.73% for Auto Bank Transfer."
  },
  {
    id: 4,
    name: "Moderate Risk — Early Tenure, Standard Plan",
    risk_level: "Moderate",
    match: (p) => p.tenure >= 13 && p.tenure <= 24 && p.Contract !== "Two year",
    action: "Offer annual contract renewal incentive before customer reaches the 2-year mark; monitor usage and satisfaction score.",
    supporting_data: "28.71% churn rate in 13-24 month cohort vs 20.39% at 25-48 months (statistical correlation r = -0.354 confirms strong protective effect of tenure)."
  },
  {
    id: 5,
    name: "Low Risk — Long-Term Contract Holder",
    risk_level: "Low",
    match: (p) => p.Contract === "Two year" && p.tenure > 48,
    action: "No urgent retention action required; target for loyalty perks, referral incentives, and premium service upsells.",
    supporting_data: "2.85% churn rate for Two-year contracts and 6.61% churn rate for customers with 61-72 months tenure."
  },
  {
    id: 6,
    name: "Low Risk — Fully Protected Customer",
    risk_level: "Low",
    match: (p) => p.OnlineSecurity === "Yes" && p.TechSupport === "Yes" && p.Contract !== "Month-to-month",
    action: "Maintain service quality; eligible for case study/testimonial requests and early access to new features.",
    supporting_data: "OnlineSecurity (Cramér's V = 0.347) and TechSupport (V = 0.343) statistically rank as top-4 drivers preventing churn."
  }
];

// ── Evaluate Playbook Segment in Hierarchical Order ───────────────
function evaluatePlaybookSegment(payload, risk, probability) {
  for (const segment of CHURN_PLAYBOOK) {
    if (segment.match(payload)) {
      return {
        segment_name: segment.name,
        recommended_action: segment.action,
        supporting_data: `Based on: ${segment.supporting_data}`
      };
    }
  }

  const fallbackAction = risk === "High"
    ? "Initiate proactive customer retention review; evaluate contract upgrade and loyalty offers."
    : risk === "Medium"
    ? "Monitor customer engagement across the next billing cycle and schedule a satisfaction check-in."
    : "No immediate action needed — this customer shows low churn risk.";

  return {
    segment_name: `${risk} Risk Profile (Standard)`,
    recommended_action: fallbackAction,
    supporting_data: `Based on: General ${risk.toLowerCase()} risk category threshold (model churn probability: ${(probability * 100).toFixed(1)}%).`
  };
}

// ── Form submit ───────────────────────────────────────────────────
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearError();
  setLoading(true);

  const payload = buildPayload();
  let lastPayload = payload;

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(detail.detail || `Server error: ${response.status}`);
    }

    const data = await response.json();
    renderResult(data, lastPayload);
  } catch (err) {
    if (err instanceof TypeError && err.message.includes("fetch")) {
      showError("Cannot reach the API. Make sure the FastAPI server is running on http://127.0.0.1:8000");
    } else {
      showError(err.message || "An unexpected error occurred.");
    }
  } finally {
    setLoading(false);
  }
});

// ── Build payload from form ───────────────────────────────────────
function buildPayload() {
  const fd = new FormData(form);
  const payload = {};

  for (const [key, value] of fd.entries()) {
    if (key === "SeniorCitizen") {
      payload[key] = parseInt(value, 10);
    } else if (key === "tenure") {
      payload[key] = parseInt(value, 10);
    } else if (key === "MonthlyCharges") {
      payload[key] = parseFloat(value);
    } else if (key === "TotalCharges") {
      // Optional — omit if blank so the API estimates it
      const trimmed = value.trim();
      if (trimmed !== "") payload[key] = parseFloat(trimmed);
    } else {
      payload[key] = value;
    }
  }

  return payload;
}

// ── Risk badge icons (match api/main.py thresholds exactly) ──────────
const RISK_ICONS = { Low: "✓", Medium: "▲", High: "▲" };

// ── Count-up animation for probability display ────────────────────
function animateCountUp(element, targetPct, duration) {
  const start = performance.now();
  const startVal = parseFloat(element.dataset.current || "0");
  function step(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    const current = startVal + (targetPct - startVal) * eased;
    element.textContent = current.toFixed(1) + "%";
    if (progress < 1) requestAnimationFrame(step);
    else element.dataset.current = targetPct;
  }
  requestAnimationFrame(step);
}

// ── Render result ─────────────────────────────────────────────────
function renderResult(data, payload) {
  const pct = (data.churn_probability * 100).toFixed(1) + "%";
  const risk = data.risk_level;
  const retentionPct = parseFloat((100 - data.churn_probability * 100).toFixed(1));
  const churnPct = parseFloat((data.churn_probability * 100).toFixed(1));

  // Count-up animation for probability
  animateCountUp(probValue, churnPct, 350);

  // Risk badge with icon
  riskBadge.textContent = RISK_ICONS[risk] + "  " + risk + " Risk";
  riskBadge.className = "risk-badge " + risk.toLowerCase();

  predictionVerdict.textContent =
    data.churn_prediction === "Yes"
      ? `⚠️ This customer is likely to churn (${pct} probability).`
      : `✅ This customer is likely to stay (${pct} churn probability).`;

  // Evaluate matching Churn Playbook segment and retention action
  const playbook = evaluatePlaybookSegment(payload, risk, data.churn_probability);
  segmentNameText.textContent    = playbook.segment_name;
  recommendationText.textContent = playbook.recommended_action;
  supportingDataText.textContent = playbook.supporting_data;

  renderDoughnut(churnPct, retentionPct);

  resultPlaceholder.classList.add("hidden");
  resultContent.classList.remove("hidden");
  resultContent.classList.remove("pulse-in");
  void resultContent.offsetWidth; // force reflow so animation restarts
  resultContent.classList.add("pulse-in");
}

// ── Doughnut chart ────────────────────────────────────────────────
function renderDoughnut(churnPct, retentionPct) {
  const ctx = document.getElementById("doughnut-chart").getContext("2d");

  if (doughnutChart) doughnutChart.destroy();

  doughnutChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Churn", "Retention"],
      datasets: [{
        data: [churnPct, retentionPct],
        backgroundColor: ["#dc2626", "#16a34a"],
        borderWidth: 0,
        hoverOffset: 4,
      }],
    },
    options: {
      cutout: "70%",
      plugins: {
        legend: { position: "bottom", labels: { font: { size: 12 } } },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.label}: ${ctx.parsed.toFixed(1)}%`,
          },
        },
      },
    },
  });
}

// ── Loading state ─────────────────────────────────────────────────
function setLoading(loading) {
  submitBtn.disabled = loading;
  btnText.textContent = loading ? "Predicting…" : "Predict Churn";
  btnSpinner.classList.toggle("hidden", !loading);
}

// ── Error helpers ─────────────────────────────────────────────────
function showError(msg) {
  formError.textContent = msg;
  formError.classList.remove("hidden");
}

function clearError() {
  formError.textContent = "";
  formError.classList.add("hidden");
}

// ── Static EDA Charts ─────────────────────────────────────────────
// Values are approximate figures derived from the EDA notebook analysis
// of the Telco Customer Churn training dataset.

function initEDACharts() {
  // Chart 1: Churn rate by contract type
  new Chart(document.getElementById("chart-contract").getContext("2d"), {
    type: "bar",
    data: {
      labels: ["Month-to-month", "One year", "Two year"],
      datasets: [{
        label: "Churn Rate (%)",
        data: [42.7, 11.3, 2.8],
        backgroundColor: ["#dc2626", "#d97706", "#16a34a"],
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (ctx) => ` ${ctx.parsed.y}%` } },
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 55,
          ticks: { callback: (v) => v + "%" },
          grid: { color: "#f0f2f5" },
        },
        x: { grid: { display: false } },
      },
    },
  });

  // Chart 2: Churn rate by tenure group
  new Chart(document.getElementById("chart-tenure").getContext("2d"), {
    type: "bar",
    data: {
      labels: ["0–12 mo", "13–24 mo", "25–48 mo", "49–60 mo", "61–72 mo"],
      datasets: [{
        label: "Churn Rate (%)",
        data: [47.4, 35.2, 22.1, 14.8, 6.6],
        backgroundColor: "#4f46e5",
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (ctx) => ` ${ctx.parsed.y}%` } },
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 60,
          ticks: { callback: (v) => v + "%" },
          grid: { color: "#f0f2f5" },
        },
        x: { grid: { display: false } },
      },
    },
  });

  // Chart 3: Churn rate by internet service type
  new Chart(document.getElementById("chart-internet").getContext("2d"), {
    type: "bar",
    data: {
      labels: ["Fiber optic", "DSL", "No service"],
      datasets: [{
        label: "Churn Rate (%)",
        data: [41.9, 19.0, 7.4],
        backgroundColor: ["#dc2626", "#d97706", "#16a34a"],
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (ctx) => ` ${ctx.parsed.y}%` } },
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 55,
          ticks: { callback: (v) => v + "%" },
          grid: { color: "#f0f2f5" },
        },
        x: { grid: { display: false } },
      },
    },
  });
}

// Init EDA charts on page load
initEDACharts();
