// AI Sales Operations Assistant - Dashboard Application Logic

let execChart = null;
let histChart = null;
let projectChart = null;
let duesChart = null;
let forecastChart = null;
let allExecutives = [];

// Formatting helpers
const formatBDT = (num) => {
  if (num === null || num === undefined) return 'N/A';
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(num) + ' BDT';
};

const formatPct = (num) => {
  if (num === null || num === undefined) return '0%';
  return num.toFixed(1) + '%';
};

const escapeHtml = (str) => {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
};

// Initialization on DOM load
document.addEventListener('DOMContentLoaded', () => {
  initDashboard();

  // Bind filter events
  document.getElementById('roleFilter').addEventListener('change', (e) => {
    loadKPIs(e.target.value);
    filterExecutiveTable();
  });

  const searchInput = document.getElementById('execSearch');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      filterExecutiveTable();
    });
  }

  // Bind lead form submission
  document.getElementById('leadForm').addEventListener('submit', handleLeadSubmission);
});

async function initDashboard() {
  await Promise.all([
    loadKPIs(),
    loadRankingsAndCharts(),
    loadForecast(),
    loadQualityReport(),
    loadLeadsTable(),
  ]);
}

// 1. Load KPIs
async function loadKPIs(role = '') {
  try {
    const url = role && role !== 'All' ? `/api/kpis?role=${encodeURIComponent(role)}` : '/api/kpis';
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    document.getElementById('kpiTarget').textContent = formatBDT(data.total_target);
    document.getElementById('kpiAchieved').textContent = formatBDT(data.total_achieved);
    document.getElementById('kpiAchievePct').textContent = formatPct(data.overall_achievement_pct);
    document.getElementById('kpiCollection').textContent = formatBDT(data.total_collection);

    document.getElementById('kpiExec100').textContent = data.executives_at_or_above_100_pct;
    document.getElementById('kpiExecZero').textContent = data.executives_at_zero;
    document.getElementById('kpiMeanMedian').textContent = `${formatPct(data.mean_achievement_pct)} / ${formatPct(data.median_achievement_pct)}`;
    document.getElementById('kpiConcentration').textContent = formatPct(data.top_10_concentration_pct);
  } catch (err) {
    console.error('Failed to load KPIs:', err);
  }
}

// 2. Load Rankings & Charts
async function loadRankingsAndCharts() {
  try {
    const [rankingsRes, statsRes, qualityRes] = await Promise.allSettled([
      fetch('/api/rankings?top_n=64'),
      fetch('/api/stats'),
      fetch('/api/quality')
    ]);

    if (rankingsRes.status === 'fulfilled' && rankingsRes.value.ok) {
      const rankingsData = await rankingsRes.value.json();
      allExecutives = rankingsData.top_by_amount || [];
      renderExecutiveTable(allExecutives);
      renderTargetVsAchievedChart(allExecutives.slice(0, 10));
      renderAchievementHistogram(allExecutives);
    } else {
      console.warn('Rankings request failed, falling back to top_n=50');
      try {
        const fallbackRes = await fetch('/api/rankings?top_n=50');
        if (fallbackRes.ok) {
          const fallbackData = await fallbackRes.json();
          allExecutives = fallbackData.top_by_amount || [];
          renderExecutiveTable(allExecutives);
          renderTargetVsAchievedChart(allExecutives.slice(0, 10));
          renderAchievementHistogram(allExecutives);
        }
      } catch (e) {
        console.error('Rankings fallback error:', e);
      }
    }

    // Fetch project breakdown
    try {
      const sqlProjRes = await fetch('/api/sql/total_sales_by_project');
      if (sqlProjRes.ok) {
        const projData = await sqlProjRes.json();
        renderProjectChart(projData.data || []);
      }
    } catch (err) {
      console.error('Error loading project chart:', err);
    }

    // Always render dues status chart
    try {
      renderDuesStatusChart();
    } catch (err) {
      console.error('Error rendering dues status chart:', err);
    }
  } catch (err) {
    console.error('Error in loadRankingsAndCharts:', err);
  }
}

// Chart 1: Top 10 Executive Target vs Achieved
function renderTargetVsAchievedChart(execs) {
  const ctx = document.getElementById('targetAchievedChart').getContext('2d');
  if (execChart) execChart.destroy();

  const labels = execs.map(e => e.executive_name);
  const targets = execs.map(e => e.target || 0);
  const achieved = execs.map(e => e.achieved || 0);

  execChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Management Target',
          data: targets,
          backgroundColor: 'rgba(148, 163, 184, 0.4)',
          borderColor: 'rgba(148, 163, 184, 0.8)',
          borderWidth: 1,
          borderRadius: 4
        },
        {
          label: 'Achieved Sales',
          data: achieved,
          backgroundColor: 'rgba(2, 132, 199, 0.8)',
          borderColor: '#0284c7',
          borderWidth: 1,
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#94a3b8' } },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${formatBDT(ctx.raw)}`
          }
        }
      },
      scales: {
        x: { ticks: { color: '#94a3b8', font: { size: 11 } }, grid: { display: false } },
        y: { ticks: { color: '#94a3b8', callback: (v) => v / 1000 + 'k' }, grid: { color: 'rgba(255, 255, 255, 0.05)' } }
      }
    }
  });
}

// Chart 2: Achievement Band Histogram
function renderAchievementHistogram(execs) {
  const ctx = document.getElementById('histogramChart').getContext('2d');
  if (histChart) histChart.destroy();

  const bands = { '0% (Zero)': 0, '1% - 25%': 0, '26% - 50%': 0, '51% - 75%': 0, '76% - 99%': 0, '>= 100%': 0 };

  execs.forEach(e => {
    const p = e.achievement_pct || 0;
    if (p === 0) bands['0% (Zero)']++;
    else if (p <= 25) bands['1% - 25%']++;
    else if (p <= 50) bands['26% - 50%']++;
    else if (p <= 75) bands['51% - 75%']++;
    else if (p < 100) bands['76% - 99%']++;
    else bands['>= 100%']++;
  });

  histChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: Object.keys(bands),
      datasets: [{
        label: 'Executives Count',
        data: Object.values(bands),
        backgroundColor: [
          '#ef4444',
          '#f97316',
          '#f59e0b',
          '#38bdf8',
          '#60a5fa',
          '#10b981'
        ],
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.raw} Executives`
          }
        }
      },
      scales: {
        x: { ticks: { color: '#94a3b8' }, grid: { display: false } },
        y: { ticks: { color: '#94a3b8', stepSize: 5 }, grid: { color: 'rgba(255, 255, 255, 0.05)' } }
      }
    }
  });
}

// Chart 3: Project Wise Collection
function renderProjectChart(projects) {
  const ctx = document.getElementById('projectChart').getContext('2d');
  if (projectChart) projectChart.destroy();

  const labels = projects.map(p => p.project_name);
  const collections = projects.map(p => p.total_collected_sep || 0);

  projectChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: collections,
        backgroundColor: ['#0284c7', '#38bdf8', '#10b981', '#f59e0b', '#a855f7'],
        borderWidth: 2,
        borderColor: '#111827'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right', labels: { color: '#94a3b8' } },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.label}: ${formatBDT(ctx.raw)}`
          }
        }
      }
    }
  });
}

// Chart 4: Dues by Status
function renderDuesStatusChart() {
  const ctx = document.getElementById('duesStatusChart').getContext('2d');
  if (duesChart) duesChart.destroy();

  // Status breakdown numbers from Sep-26 Status Table
  const statusLabels = ['Full Paid', 'EMI', 'Token', 'Hold', 'Cancel'];
  const duesValues = [0, 177518624, 140315300, 35191378, 80692000];

  duesChart = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: statusLabels,
      datasets: [{
        data: duesValues,
        backgroundColor: ['#10b981', '#0284c7', '#f59e0b', '#64748b', '#ef4444'],
        borderWidth: 2,
        borderColor: '#111827'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right', labels: { color: '#94a3b8' } },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.label}: ${formatBDT(ctx.raw)}`
          }
        }
      }
    }
  });
}

// 3. Load Forecast
async function loadForecast() {
  try {
    const res = await fetch('/api/forecast');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    document.getElementById('forecastModelName').textContent = data.best_model;
    const bestEval = data.model_evaluations.find(m => m.model_name === data.best_model);
    if (bestEval) {
      document.getElementById('forecastMAE').textContent = formatBDT(bestEval.mae);
      document.getElementById('forecastRMSE').textContent = formatBDT(bestEval.rmse);
    }

    renderForecastChart(data.historical_series, data.forecast_next_3_months);
  } catch (err) {
    console.error('Error loading forecast:', err);
  }
}

function renderForecastChart(history, forecast) {
  const ctx = document.getElementById('forecastChart').getContext('2d');
  if (forecastChart) forecastChart.destroy();

  const allMonths = [...history.map(h => h.month), ...forecast.map(f => f.month)];
  const actualData = history.map(h => h.amount);
  
  // Fill forecast array aligning with allMonths
  const forecastData = new Array(history.length - 1).fill(null);
  forecastData.push(history[history.length - 1].amount); // connect point
  forecast.forEach(f => forecastData.push(f.forecast_amount));

  const lowerBound = new Array(history.length).fill(null);
  forecast.forEach(f => lowerBound.push(f.lower_bound_95));

  const upperBound = new Array(history.length).fill(null);
  forecast.forEach(f => upperBound.push(f.upper_bound_95));

  forecastChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: allMonths,
      datasets: [
        {
          label: 'Historical Monthly Collection',
          data: actualData,
          borderColor: '#38bdf8',
          backgroundColor: '#38bdf8',
          tension: 0.2,
          pointRadius: 5
        },
        {
          label: 'Forecast Next 3 Months',
          data: forecastData,
          borderColor: '#f59e0b',
          borderDash: [6, 6],
          backgroundColor: '#f59e0b',
          tension: 0.2,
          pointRadius: 5
        },
        {
          label: 'Upper 95% Bound',
          data: upperBound,
          borderColor: 'transparent',
          backgroundColor: 'rgba(245, 158, 11, 0.12)',
          fill: '+1',
          pointRadius: 0
        },
        {
          label: 'Lower 95% Bound',
          data: lowerBound,
          borderColor: 'transparent',
          backgroundColor: 'transparent',
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#94a3b8' } },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${formatBDT(ctx.raw)}`
          }
        }
      },
      scales: {
        x: { ticks: { color: '#94a3b8' }, grid: { display: false } },
        y: { ticks: { color: '#94a3b8', callback: (v) => v / 1000000 + 'M' }, grid: { color: 'rgba(255, 255, 255, 0.05)' } }
      }
    }
  });
}

// 4. Executive Table & Search
function renderExecutiveTable(execs) {
  const tbody = document.getElementById('execTableBody');
  tbody.innerHTML = '';

  if (!execs || execs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 20px;">No executive records found.</td></tr>';
    return;
  }

  execs.forEach(e => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${e.rank}</td>
      <td style="font-weight: 600;">${e.executive_name}</td>
      <td><span class="chip" style="font-size:0.75rem;">${e.role}</span></td>
      <td>${formatBDT(e.target)}</td>
      <td>${formatBDT(e.achieved)}</td>
      <td><span style="font-weight:700; color: ${e.achievement_pct >= 100 ? '#10b981' : e.achievement_pct === 0 ? '#ef4444' : '#f59e0b'};">${formatPct(e.achievement_pct)}</span></td>
      <td>${formatBDT(e.total_collection)}</td>
    `;
    tbody.appendChild(tr);
  });
}

function filterExecutiveTable() {
  const role = document.getElementById('roleFilter').value;
  const searchInput = document.getElementById('execSearch');
  const search = searchInput ? searchInput.value.toLowerCase().trim() : '';

  let filtered = allExecutives;
  if (role && role !== 'All') {
    filtered = filtered.filter(e => e.role.toLowerCase() === role.toLowerCase());
  }
  if (search) {
    filtered = filtered.filter(e => e.executive_name.toLowerCase().includes(search));
  }
  renderExecutiveTable(filtered);
}

// 5. Data Quality Report
async function loadQualityReport() {
  try {
    const res = await fetch('/api/quality');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const statusBadge = document.getElementById('qualityStatusBadge');
    statusBadge.textContent = data.overall_status;
    statusBadge.className = data.overall_status === 'PASS' ? 'chip chip-status' : 'chip chip-anon';

    document.getElementById('qualityPolicyText').textContent = data.missing_value_policy;

    const crossTbody = document.getElementById('crossCheckTableBody');
    crossTbody.innerHTML = '';
    data.sheet_cross_checks.forEach(c => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${c.metric}</td>
        <td>${formatBDT(c.computed_sum)}</td>
        <td>${formatBDT(c.sheet_total_row)}</td>
        <td><span style="color: ${c.matches ? '#10b981' : '#f59e0b'}; font-weight:700;">${c.matches ? 'MATCH' : c.discrepancy.toLocaleString() + ' BDT GAP'}</span></td>
        <td style="font-size:0.775rem; color: #94a3b8;">${c.notes || '-'}</td>
      `;
      crossTbody.appendChild(tr);
    });
  } catch (err) {
    console.error('Failed to load quality report:', err);
  }
}

// 6. Lead Lab & AI Qualification Form
async function handleLeadSubmission(e) {
  e.preventDefault();

  const formAlert = document.getElementById('formAlert');
  formAlert.style.display = 'none';
  formAlert.className = 'alert';

  const name = document.getElementById('leadName').value.trim();
  const email = document.getElementById('leadEmail').value.trim();
  const phone = document.getElementById('leadPhone').value.trim();
  const budget = parseFloat(document.getElementById('leadBudget').value);
  const interest = document.getElementById('leadInterest').value.trim();
  const message = document.getElementById('leadMessage').value.trim();

  // Client-side validation
  if (!name || !email || !phone || isNaN(budget) || !interest) {
    showFormError('Please fill in all required fields.');
    return;
  }
  if (budget <= 0) {
    showFormError('Budget must be greater than zero.');
    return;
  }
  const cleanPhone = phone.replace(/\D/g, '');
  if (cleanPhone.length < 10) {
    showFormError('Phone number must have at least 10 digits.');
    return;
  }

  const submitBtn = document.getElementById('submitLeadBtn');
  const originalBtnText = submitBtn.innerHTML;
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner"></span> Qualifying with AI...';

  try {
    const res = await fetch('/api/leads', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, phone, budget, interest, message })
    });

    const data = await res.json();

    if (res.status === 409) {
      showFormError(`Duplicate Lead: ${data.detail}`);
      return;
    }
    if (res.status === 422) {
      const errDetail = data.detail ? (Array.isArray(data.detail) ? data.detail.map(d => d.msg).join(', ') : data.detail) : 'Validation failed';
      showFormError(`Validation error: ${errDetail}`);
      return;
    }
    if (!res.ok) {
      showFormError(`Error: ${data.detail || 'Lead processing failed'}`);
      return;
    }

    // Success - display AI Qualification Card
    renderOutcomeCard(data);
    document.getElementById('leadForm').reset();
    loadLeadsTable();
  } catch (err) {
    showFormError(`Network error: ${err.message}`);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalBtnText;
  }
}

function showFormError(msg) {
  const formAlert = document.getElementById('formAlert');
  formAlert.textContent = msg;
  formAlert.className = 'alert alert-danger';
  formAlert.style.display = 'block';
}

function renderOutcomeCard(lead) {
  const container = document.getElementById('outcomeContainer');
  const category = lead.category || 'Review';
  const badgeClass = category === 'Hot' ? 'badge-hot' : category === 'Warm' ? 'badge-warm' : 'badge-cold';

  container.innerHTML = `
    <span class="badge-pill ${badgeClass}">${lead.qualification_status}: ${category}</span>
    <div class="score-display" style="color: ${category === 'Hot' ? '#ef4444' : category === 'Warm' ? '#f59e0b' : '#38bdf8'};">
      ${lead.score !== null ? lead.score : '--'}<span style="font-size: 1.25rem; font-weight:600; color: #94a3b8;">/100</span>
    </div>
    <div style="font-size: 0.95rem; font-weight:700; color:#fff;">${lead.name}</div>
    <div style="font-size: 0.8rem; color:#94a3b8;">Budget: ${formatBDT(lead.budget)} | ${lead.interest}</div>
    <div class="ai-reason-box">
      <strong>AI Rationale:</strong><br>
      ${lead.reason || lead.ai_error || 'No explanation provided.'}
    </div>
  `;
}

// 7. Load Leads Table
async function loadLeadsTable() {
  try {
    const res = await fetch('/api/leads');
    if (!res.ok) return;
    const leads = await res.json();

    const tbody = document.getElementById('leadsTableBody');
    tbody.innerHTML = '';

    if (!leads || leads.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 20px;">No leads submitted yet. Use the form above to qualify a lead.</td></tr>';
      return;
    }

    leads.forEach(l => {
      const tr = document.createElement('tr');
      const badgeClass = l.category === 'Hot' ? 'badge-hot' : l.category === 'Warm' ? 'badge-warm' : 'badge-cold';
      tr.innerHTML = `
        <td>${l.id}</td>
        <td>${l.name}</td>
        <td>${formatBDT(l.budget)}</td>
        <td>${l.interest}</td>
        <td><span class="badge-pill ${badgeClass}" style="font-size: 0.75rem; padding: 3px 8px;">${l.category || l.qualification_status}</span></td>
        <td>${l.score !== null ? l.score : '-'}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('Failed to load leads table:', err);
  }
}

// 7. Grounded RAG Co-Pilot Interaction
function askCopilot(query) {
  const input = document.getElementById('copilotInput');
  if (input) {
    input.value = query;
    sendCopilotQuery();
  }
}

async function sendCopilotQuery() {
  const input = document.getElementById('copilotInput');
  const btn = document.getElementById('copilotBtn');
  const feed = document.getElementById('copilotFeed');
  if (!input || !feed) return;

  const query = input.value.trim();
  if (!query) return;

  input.value = '';
  if (btn) btn.disabled = true;

  // Append user message
  const userDiv = document.createElement('div');
  userDiv.style.cssText = 'font-size: 0.85rem; color: #111827; line-height: 1.5; padding: 8px 12px; background: #fef2f2; border-left: 3px solid #800000; border-radius: 4px;';
  userDiv.innerHTML = `<strong>You:</strong> ${escapeHtml(query)}`;
  feed.appendChild(userDiv);

  // Append waiting message
  const botDiv = document.createElement('div');
  botDiv.style.cssText = 'font-size: 0.85rem; color: #374151; line-height: 1.5; padding: 10px 14px; background: #f9fafb; border: 1px solid #e5e7eb; border-left: 3px solid #15803d; border-radius: 4px;';
  botDiv.innerHTML = `<strong>Operations Co-Pilot:</strong> <em>Retrieving spreadsheet ledger records via FAISS...</em>`;
  feed.appendChild(botDiv);
  feed.scrollTop = feed.scrollHeight;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'user', content: query }],
      }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    let sourcesHtml = '';
    if (data.sources && data.sources.length > 0) {
      sourcesHtml = '<div style="margin-top: 8px; font-size: 0.75rem; color: #6b7280; display: flex; flex-wrap: wrap; gap: 4px;">';
      data.sources.forEach(s => {
        sourcesHtml += `<span style="background: #ffffff; border: 1px solid #d1d5db; color: #800000; padding: 2px 6px; border-radius: 3px; font-family: monospace;">[${escapeHtml(s.file)}: ${escapeHtml(s.sheet)}]</span>`;
      });
      sourcesHtml += '</div>';
    }

    botDiv.innerHTML = `<strong>Operations Co-Pilot:</strong> <div style="margin-top: 6px; white-space: pre-wrap; color: #111827;">${escapeHtml(data.answer)}</div>${sourcesHtml}`;
  } catch (err) {
    botDiv.innerHTML = `<strong>Operations Co-Pilot:</strong> <span style="color: #ef4444;">Error contacting RAG assistant: ${err.message}</span>`;
  } finally {
    if (btn) btn.disabled = false;
    feed.scrollTop = feed.scrollHeight;
  }
}
