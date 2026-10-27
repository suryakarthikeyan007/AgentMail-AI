// AgentMail AI - Frontend Dashboard Application Logic

const API_BASE = '/api';

// Viva Preset Email Payloads
const PRESETS = {
  interview: {
    sender: 'recruiter@techinnovators.com',
    subject: 'Technical Interview Invitation - AI Engineer Role',
    thread_id: 'thread_interview_901',
    body: 'Hi Pradeep,\n\nWe reviewed your application and would like to schedule an interview tomorrow at 3:00 PM IST. Can you confirm if this time works for you?\n\nBest regards,\nSarah Jenkins\nTechInnovators Talent Team'
  },
  salary: {
    sender: 'hr@cloudscale.io',
    subject: 'Offer Discussion - AI Associate',
    thread_id: 'thread_salary_404',
    body: 'Dear Pradeep,\n\nWe are pleased to inform you that the panel approved your candidacy. Can you accept an annual salary of ₹12 LPA starting next month?\n\nRegards,\nHR Operations'
  },
  resume: {
    sender: 'talent@deepmindcareers.org',
    subject: 'Request for Resume & Project Details',
    thread_id: 'thread_resume_102',
    body: 'Hello Pradeep,\n\nYour profile in Agentic AI caught our attention. Could you please send over your updated resume and highlight your key projects?\n\nLooking forward to hearing from you.'
  },
  spam: {
    sender: 'winner@promo-rewards-fast.net',
    subject: 'URGENT: Claim your $5,000 cash voucher today!',
    thread_id: 'thread_spam_888',
    body: 'DEAR VALUED CUSTOMER,\n\nYOU HAVE BEEN SELECTED AS OUR TOP LUCKY WINNER. CLICK THE LINK BELOW IMMEDIATELY TO CLAIM YOUR CASH PRIZE!\n\nUnsubscribe here.'
  },
  followup: {
    sender: 'recruiter@techinnovators.com',
    subject: 'Re: Technical Interview Invitation - AI Engineer Role',
    thread_id: 'thread_interview_901',
    body: 'Hi Pradeep,\n\nJust following up on my previous message regarding the interview. Did you receive our request?'
  }
};

// Authoritative Client-Side State
let auditRecords = [];
let pendingApprovals = [];
let isBackendConnected = false;

// DOM Elements
const statsElements = {
  total: document.getElementById('stat-total'),
  auto: document.getElementById('stat-auto'),
  approvals: document.getElementById('stat-approvals'),
  clarifications: document.getElementById('stat-clarifications'),
  tools: document.getElementById('stat-tools'),
  ignored: document.getElementById('stat-ignored'),
  highrisk: document.getElementById('stat-highrisk'),
  speed: document.getElementById('stat-speed')
};

const emailForm = document.getElementById('email-demo-form');
const senderInput = document.getElementById('input-sender');
const threadInput = document.getElementById('input-thread-id');
const subjectInput = document.getElementById('input-subject');
const bodyInput = document.getElementById('input-body');
const processBtn = document.getElementById('btn-process');
const spinner = document.getElementById('process-spinner');
const processBtnText = document.getElementById('btn-process-text');
const decisionsTableBody = document.getElementById('decisions-table-body');
const approvalList = document.getElementById('approval-items-list');
const approvalsCount = document.getElementById('approvals-count');

// Modal Elements
const editModal = document.getElementById('edit-modal');
const modalSenderSubject = document.getElementById('modal-sender-subject');
const modalFlagReason = document.getElementById('modal-flag-reason');
const modalEditedBody = document.getElementById('modal-edited-body');
const modalMessageId = document.getElementById('modal-message-id');
const modalCloseBtn = document.getElementById('modal-close-btn');
const modalCancelBtn = document.getElementById('modal-cancel-btn');
const modalSubmitBtn = document.getElementById('modal-submit-btn');

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
  setupTabs();
  setupPresets();
  setupEventListeners();
  checkSystemHealth();
  refreshAllData();
  // Auto refresh every 8 seconds
  setInterval(refreshAllData, 8000);
  setInterval(checkSystemHealth, 15000);
});

function setupEventListeners() {
  document.getElementById('btn-refresh-data').addEventListener('click', () => {
    checkSystemHealth();
    refreshAllData();
  });

  document.getElementById('btn-clear-form').addEventListener('click', () => {
    senderInput.value = '';
    subjectInput.value = '';
    bodyInput.value = '';
  });

  processBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    await handleProcessEmail();
  });

  emailForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await handleProcessEmail();
  });

  modalCloseBtn.addEventListener('click', () => editModal.style.display = 'none');
  modalCancelBtn.addEventListener('click', () => editModal.style.display = 'none');
  modalSubmitBtn.addEventListener('click', handleModalSubmit);
}

function setupTabs() {
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(btn => {
    btn.addEventListener('click', () => {
      tabs.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const targetId = btn.dataset.tab;
      document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
      const targetContent = document.getElementById(targetId);
      if (targetContent) targetContent.style.display = 'block';
    });
  });
}

function setupPresets() {
  document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const presetKey = btn.dataset.preset;
      const data = PRESETS[presetKey];
      if (data) {
        senderInput.value = data.sender;
        threadInput.value = data.thread_id;
        subjectInput.value = data.subject;
        bodyInput.value = data.body;
      }
    });
  });
}

// ISSUE 6 FIX: Verified Service Health Checking (Ollama, Embeddings, Database, Backend)
async function checkSystemHealth() {
  const textBackend = document.getElementById('text-backend-status');
  const indBackend = document.getElementById('ind-backend');
  const textOllama = document.getElementById('text-ollama-status');
  const indOllama = document.getElementById('ind-ollama');
  const textEmbedding = document.getElementById('text-embedding-status');
  const indEmbedding = document.getElementById('ind-embedding');
  const testModeBadge = document.getElementById('test-mode-badge');

  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      isBackendConnected = true;
      const data = await res.json();

      if (textBackend) textBackend.textContent = 'Backend: Online (Port 8000)';
      if (indBackend) indBackend.className = 'indicator live';

      if (textOllama) {
        if (data.ollama && data.ollama.connected) {
          textOllama.textContent = `Ollama: Connected (${data.ollama.active_model})`;
          if (indOllama) indOllama.className = 'indicator live';
        } else {
          textOllama.textContent = 'Ollama: Offline (Fallback Mode)';
          if (indOllama) indOllama.className = 'indicator offline';
        }
      }

      if (textEmbedding) {
        if (data.embedding && data.embedding.status === 'active') {
          textEmbedding.textContent = `Embedding: Active (${data.embedding.model})`;
          if (indEmbedding) indEmbedding.className = 'indicator live';
        } else {
          textEmbedding.textContent = 'Embedding: Ready';
          if (indEmbedding) indEmbedding.className = 'indicator live';
        }
      }

      if (testModeBadge) {
        testModeBadge.textContent = data.test_mode ? 'TEST_MODE: SAFE EMULATION' : 'PRODUCTION: LIVE GMAIL API';
        testModeBadge.className = data.test_mode ? 'badge badge-accent' : 'badge badge-success';
      }
      return;
    }
  } catch (err) {
    // Backend offline / GitHub Pages static hosting
    isBackendConnected = false;
  }

  // Display authentic demo-mode status badges rather than false connected labels
  if (textBackend) textBackend.textContent = 'Backend: Demo Mode (GitHub Pages)';
  if (indBackend) indBackend.className = 'indicator offline';
  if (textOllama) textOllama.textContent = 'AI Engine: Client Simulation';
  if (indOllama) indOllama.className = 'indicator live';
  if (textEmbedding) textEmbedding.textContent = 'Embedding: In-Memory RAG';
  if (indEmbedding) indEmbedding.className = 'indicator live';
  if (testModeBadge) {
    testModeBadge.textContent = 'DEMO PREVIEW (SAFE DISPATCH)';
    testModeBadge.className = 'badge badge-accent';
  }
}

// ISSUE 3 FIX: Singular/plural helper and consistent timestamp formatter
function pluralize(count, singular, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`;
}

function formatTimestamp(val) {
  if (!val) return '-';
  if (typeof val === 'string') {
    // If it is an ISO string like "2026-10-27 08:15:38" or "2026-10-27T08:15:38"
    if (val.includes('-') && (val.includes(':') || val.includes('T'))) {
      const timePart = val.replace('T', ' ').split(' ')[1] || val;
      return timePart.split('.')[0];
    }
    // If it's already a clean time like "8:15:38 PM"
    if (val.includes(':')) {
      return val;
    }
  }
  try {
    const d = new Date(val);
    return isNaN(d.getTime()) ? String(val) : d.toLocaleTimeString('en-US', { hour12: true });
  } catch (e) {
    return String(val);
  }
}

function updateStats(data) {
  if (!data) return;
  if (statsElements.total) statsElements.total.textContent = data.total_emails_processed ?? 0;
  if (statsElements.auto) statsElements.auto.textContent = data.auto_replies ?? 0;
  if (statsElements.approvals) statsElements.approvals.textContent = data.human_approvals ?? 0;
  if (statsElements.clarifications) statsElements.clarifications.textContent = data.clarification_requests ?? 0;
  if (statsElements.tools) statsElements.tools.textContent = data.tool_required_cases ?? 0;
  if (statsElements.ignored) statsElements.ignored.textContent = data.ignored_emails ?? 0;
  if (statsElements.highrisk) statsElements.highrisk.textContent = data.high_risk_emails ?? 0;
  if (statsElements.speed) statsElements.speed.textContent = `${data.avg_processing_time_ms ?? 0} ms`;
}

function computeStatsFromLocal() {
  const total = auditRecords.length;
  const auto = auditRecords.filter(r => r.final_action === 'AUTO_REPLY' || r.final_action === 'APPROVED_AND_SENT' || r.final_action === 'EDITED_AND_SENT').length;
  const approvals = pendingApprovals.length;
  const clarifications = auditRecords.filter(r => r.planner_decision === 'CLARIFICATION_REQUIRED' || r.final_action === 'CLARIFICATION_REQUIRED').length;
  const tools = auditRecords.filter(r => r.planner_decision === 'TOOL_REQUIRED' || r.final_action === 'TOOL_REQUIRED').length;
  const ignored = auditRecords.filter(r => r.final_action === 'IGNORE' || r.planner_decision === 'IGNORE').length;
  const highrisk = auditRecords.filter(r => r.risk_level === 'HIGH').length;
  const totalTime = auditRecords.reduce((acc, r) => acc + (Number(r.processing_time_ms) || 0), 0);
  const avg = total > 0 ? Math.round(totalTime / total) : 0;
  return {
    total_emails_processed: total,
    auto_replies: auto,
    human_approvals: approvals,
    clarification_requests: clarifications,
    tool_required_cases: tools,
    ignored_emails: ignored,
    high_risk_emails: highrisk,
    avg_processing_time_ms: avg
  };
}

async function refreshAllData() {
  await Promise.all([
    fetchStats(),
    fetchEmails(),
    fetchApprovals()
  ]);
}

async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/stats`);
    if (res.ok) {
      isBackendConnected = true;
      const data = await res.json();
      updateStats(data);
    } else {
      updateStats(computeStatsFromLocal());
    }
  } catch (err) {
    isBackendConnected = false;
    updateStats(computeStatsFromLocal());
  }
}

async function fetchEmails() {
  try {
    const res = await fetch(`${API_BASE}/emails?limit=20`);
    if (res.ok) {
      isBackendConnected = true;
      const data = await res.json();
      auditRecords = data.emails || [];
      renderDecisionsTable(auditRecords);
    } else {
      renderDecisionsTable(auditRecords);
    }
  } catch (err) {
    isBackendConnected = false;
    renderDecisionsTable(auditRecords);
  }
}

async function fetchApprovals() {
  try {
    const res = await fetch(`${API_BASE}/approvals?status=PENDING`);
    if (res.ok) {
      isBackendConnected = true;
      const data = await res.json();
      pendingApprovals = data.items || [];
      renderApprovals(pendingApprovals);
    } else {
      renderApprovals(pendingApprovals);
    }
  } catch (err) {
    isBackendConnected = false;
    renderApprovals(pendingApprovals);
  }
}

// ISSUE 1 & ISSUE 3 FIX:
// Correct singular/plural labels, clean timestamp formatting without "PM" truncation,
// and single authoritative records mapping.
function renderDecisionsTable(emails) {
  const records = emails || [];
  const countEl = document.getElementById('records-count');
  if (countEl) {
    countEl.textContent = pluralize(records.length, 'Record');
  }

  if (records.length === 0) {
    decisionsTableBody.innerHTML = `<tr><td colspan="9" class="text-center text-muted">No emails processed yet.</td></tr>`;
    return;
  }

  decisionsTableBody.innerHTML = records.map(email => {
    const actionBadgeClass = (email.final_action === 'AUTO_REPLY' || email.final_action === 'APPROVED_AND_SENT' || email.final_action === 'EDITED_AND_SENT') ? 'badge-success'
      : (email.final_action === 'HUMAN_APPROVAL' ? 'badge-warning'
      : (email.final_action === 'IGNORE' || email.final_action === 'REJECTED_STOP' ? 'badge-outline' : 'badge-accent'));

    const riskBadgeClass = email.risk_level === 'HIGH' ? 'badge-danger'
      : (email.risk_level === 'MEDIUM' ? 'badge-warning' : 'badge-success');

    const formattedTime = formatTimestamp(email.created_at);

    return `
      <tr>
        <td style="white-space:nowrap; font-variant-numeric:tabular-nums;">${formattedTime}</td>
        <td title="${escapeHtml(email.sender)}"><strong>${escapeHtml(email.sender.split('<')[0])}</strong></td>
        <td>${escapeHtml(email.subject)}</td>
        <td><span class="badge badge-outline">${escapeHtml(email.category || '-')}</span></td>
        <td>${escapeHtml(email.priority || '-')}</td>
        <td><code>${escapeHtml(email.planner_decision || '-')}</code></td>
        <td><span class="badge ${riskBadgeClass}">${escapeHtml(email.risk_level || 'LOW')}</span></td>
        <td><span class="badge ${actionBadgeClass}">${escapeHtml(email.final_action || '-')}</span></td>
        <td>${email.processing_time_ms ? `${email.processing_time_ms}ms` : '-'}</td>
      </tr>
    `;
  }).join('');
}

// ISSUE 4 FIX:
// Explicit separation of priority, risk_level, and approval_required on approval cards
function renderApprovals(items) {
  const list = items || [];
  if (approvalsCount) {
    approvalsCount.textContent = pluralize(list.length, 'Pending Approval', 'Pending Approvals');
  }

  if (list.length === 0) {
    approvalList.innerHTML = `<div class="empty-state">No pending approval requests. System is operating safely.</div>`;
    return;
  }

  approvalList.innerHTML = list.map(item => {
    const priority = item.priority || 'High';
    const riskLevel = item.risk_level || 'MEDIUM';
    const riskBadgeClass = riskLevel === 'HIGH' ? 'badge-danger' : (riskLevel === 'MEDIUM' ? 'badge-warning' : 'badge-success');
    const ruleApplied = item.approval_rule_applied || (item.reason && item.reason.includes('Calendar') ? 'RULE_CALENDAR_UNVERIFIED_GATE' : 'RULE_MANDATORY_APPROVAL');

    return `
      <div class="approval-card" id="approval-${item.message_id}">
        <div class="approval-header">
          <div>
            <div class="approval-meta">From: <strong>${escapeHtml(item.sender)}</strong> &bull; Subject: <strong>${escapeHtml(item.subject)}</strong></div>
            <div style="font-size: 0.75rem; color: var(--color-amber); margin-top: 0.25rem;">
              ⚠️ Flagged Reason: ${escapeHtml(item.reason)}
            </div>
          </div>
          <div style="display:flex; flex-wrap:wrap; gap:0.4rem; justify-content:flex-end;">
            <span class="badge badge-outline">Priority: ${escapeHtml(priority)}</span>
            <span class="badge ${riskBadgeClass}">Risk: ${escapeHtml(riskLevel)}</span>
            <span class="badge badge-warning">Approval Required: YES (${escapeHtml(ruleApplied)})</span>
          </div>
        </div>

        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.75rem;">
          <div>
            <div style="font-size:0.72rem; color:var(--text-muted); margin-bottom:0.25rem;">Original Email:</div>
            <div class="approval-content-box">${escapeHtml(item.original_body)}</div>
          </div>
          <div>
            <div style="font-size:0.72rem; color:var(--text-muted); margin-bottom:0.25rem;">Proposed Safe Draft:</div>
            <div class="approval-content-box">${escapeHtml(item.draft_body)}</div>
          </div>
        </div>

        <div class="approval-actions">
          <button class="btn btn-secondary btn-sm" onclick="openEditModal('${escapeJs(item.message_id)}', '${escapeJs(item.sender)}', '${escapeJs(item.subject)}', '${escapeJs(item.reason)}', '${escapeJs(item.draft_body)}')">
            ✏️ Edit & Re-Verify
          </button>
          <button class="btn btn-danger btn-sm" onclick="handleRejectApproval('${escapeJs(item.message_id)}')">
            ✖ Reject
          </button>
          <button class="btn btn-success btn-sm" onclick="handleApprove('${escapeJs(item.message_id)}')">
            ✓ Approve & Send
          </button>
        </div>
      </div>
    `;
  }).join('');
}

async function handleProcessEmail() {
  const payload = {
    sender: senderInput.value.trim(),
    thread_id: threadInput.value.trim() || undefined,
    subject: subjectInput.value.trim(),
    body: bodyInput.value.trim()
  };

  if (!payload.sender || !payload.subject || !payload.body) {
    alert('Please provide Sender, Subject, and Email Body.');
    return;
  }

  processBtn.disabled = true;
  spinner.style.display = 'inline';
  processBtnText.textContent = 'Agent Pipeline Processing...';
  animatePipelineTrack();

  const traceBadge = document.getElementById('trace-status-badge');
  traceBadge.textContent = 'Analyzing...';
  traceBadge.className = 'badge badge-warning';

  try {
    const res = await fetch(`${API_BASE}/process-email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (res.ok && data.status === 'success') {
      isBackendConnected = true;
      const result = data.result;
      displayTrace(result, false);
      traceBadge.textContent = 'Success (Local Backend)';
      traceBadge.className = 'badge badge-success';
      await refreshAllData();
    } else {
      simulateClientSidePipeline(payload);
    }
  } catch (err) {
    console.warn('Backend API unreachable. Running in client-side interactive simulation mode for GitHub Pages.');
    simulateClientSidePipeline(payload);
  } finally {
    processBtn.disabled = false;
    spinner.style.display = 'none';
    processBtnText.textContent = '🚀 Run Agentic AI Pipeline';
  }
}

// ISSUE 1 & ISSUE 4 FIX:
// Accurate Calendar Availability Grounding ("I will need to confirm my availability"),
// and explicit separation of priority, risk_level, and approval_required.
function simulateClientSidePipeline(payload) {
  const bodyLower = (payload.body || '').toLowerCase();
  const subjectLower = (payload.subject || '').toLowerCase();
  const traceBadge = document.getElementById('trace-status-badge');
  traceBadge.textContent = 'Demo Mode (GitHub Pages)';
  traceBadge.className = 'badge badge-accent';

  const demoId = `msg_${Date.now()}`;
  let result;

  if (bodyLower.includes('interview') || bodyLower.includes('schedule') || subjectLower.includes('interview')) {
    // ISSUE 1 FIX:
    // Calendar is UNVERIFIED. Draft NEVER says "I have checked my schedule".
    // Uses: "I will need to confirm my availability before committing to that time."
    result = {
      message_id: demoId,
      thread_id: payload.thread_id || 'thread_interview_901',
      sender: payload.sender,
      subject: payload.subject,
      classification: {
        category: 'Interview',
        intent: 'Interview scheduling request',
        priority: 'High',
        confidence: 0.95,
        sensitivity: 'Medium',
        entities: ['interview', 'ai engineer', 'tomorrow at 3:00 PM IST']
      },
      rag_context: {
        sources: ['knowledge_base/education/academic_background.md', 'knowledge_base/response_guidelines/email_guidelines.md'],
        formatted_text: 'Rule: NEVER commit to an interview time unless calendar availability is verified.\nCandidate: Pradeep Kumar A. (B.Tech AI & DS, Anna University, CGPA: 8.85/10).'
      },
      calendar_audit: {
        lookup_performed: true,
        requested_slot: 'tomorrow at 3:00 PM IST',
        availability_result: 'UNVERIFIED',
        status: 'UNVERIFIED_CALENDAR_OFFLINE',
        verified: false,
        reason: "Calendar lookup performed for 'tomorrow at 3:00 PM IST': External calendar tool is offline or unverified. Actual free/busy status cannot be guaranteed.",
        recommended_wording: "I will need to confirm my availability before committing to tomorrow at 3:00 PM IST. Could you please share 2-3 alternative time slots?"
      },
      planner_decision: {
        decision: 'HUMAN_APPROVAL',
        priority: 'High',
        risk_level: 'MEDIUM',
        approval_required: true,
        approval_rule_applied: 'RULE_CALENDAR_UNVERIFIED_GATE',
        reason: "APPROVAL REQUIRED: Interview scheduling requested for 'tomorrow at 3:00 PM IST'. Calendar status: UNVERIFIED_CALENDAR_OFFLINE. Automatic commitments are blocked; supervisor authorization required.",
        confidence: 0.94,
        required_information: ['Verified calendar availability'],
        recommended_action: 'Ask recruiter for 2-3 alternative time slots or confirm availability with supervisor.'
      },
      quality_audit: {
        approved: false,
        risk_level: 'MEDIUM',
        approval_required: true,
        approval_rule_applied: 'RULE_CALENDAR_UNVERIFIED_GATE',
        issues: ['Pending supervisor review to prevent unverified calendar schedule conflicts.'],
        reason: 'Risk level: MEDIUM. Approval required: true. Rule: RULE_CALENDAR_UNVERIFIED_GATE.'
      },
      draft_response: {
        subject: `Re: ${payload.subject}`,
        body: `Dear Recruiter,\n\nThank you for considering me for the AI Engineer role. I am excited about this opportunity.\n\nI will need to confirm my availability before committing to tomorrow at 3:00 PM IST, as my calendar is currently unverified. Could you please share 2-3 alternative dates or time slots so I can ensure no conflicts?\n\nBest regards,\nPradeep Kumar A.\nB.Tech Artificial Intelligence & Data Science\nAnna University`,
        reasoning_summary: 'Polite clarification requesting alternative slots without inventing calendar availability.'
      },
      final_action: 'HUMAN_APPROVAL',
      action_reason: 'Zero-Hallucination Gate: Rerouted to Human Approval Queue due to unverified calendar commitment.',
      processing_time_ms: 1240,
      pipeline_trace: [
        { step: 'PREPROCESS', status: 'COMPLETED', details: `Cleaned email text (${payload.body.length} chars). Signatures & quotes normalized.` },
        { step: 'CLASSIFY', status: 'COMPLETED', category: 'Interview', priority: 'High', confidence: 0.95, details: 'Classified category: Interview, Intent: Interview scheduling, Priority: High' },
        { step: 'RETRIEVE_RAG', status: 'COMPLETED', sources: ['academic_background.md', 'email_guidelines.md'], details: 'Retrieved 2 candidate profile & scheduling policy chunks' },
        { step: 'RETRIEVE_MEMORY', status: 'COMPLETED', is_thread_existing: true, turn_history_count: 1, details: 'Active conversation thread found (1 prior turn)' },
        { step: 'CALENDAR_LOOKUP', status: 'COMPLETED', requested_slot: 'tomorrow at 3:00 PM IST', availability_result: 'UNVERIFIED', calendar_status: 'UNVERIFIED_CALENDAR_OFFLINE', verified: false, details: 'External calendar lookup performed. Offline/unverified mode. Automatic commitments blocked.' },
        { step: 'PLAN', status: 'COMPLETED', decision: 'HUMAN_APPROVAL', priority: 'High', risk_level: 'MEDIUM', approval_required: true, approval_rule_applied: 'RULE_CALENDAR_UNVERIFIED_GATE', reason: 'Unverified calendar commitment requested. Human approval required.' },
        { step: 'WRITE_DRAFT', status: 'COMPLETED', draft_subject: `Re: ${payload.subject}`, details: 'Generated safe clarification draft (78 words) requesting alternative slots without claiming schedule was checked.' },
        { step: 'QUALITY_AUDIT', status: 'COMPLETED', risk_level: 'MEDIUM', approval_required: true, approval_rule_applied: 'RULE_CALENDAR_UNVERIFIED_GATE', audit_approved: false, details: 'Audit verified draft contains no false schedule claims. Rerouted to human approval queue.' },
        { step: 'QUEUE_HUMAN_APPROVAL', status: 'PENDING', priority: 'High', risk_level: 'MEDIUM', approval_rule: 'RULE_CALENDAR_UNVERIFIED_GATE', reason: 'Zero-Hallucination Gate enforced.', details: 'Held for supervisor review to prevent unverified calendar schedule conflicts.' }
      ]
    };
  } else if (bodyLower.includes('salary') || bodyLower.includes('lpa') || bodyLower.includes('ctc')) {
    result = {
      message_id: demoId,
      thread_id: payload.thread_id || 'thread_salary_404',
      sender: payload.sender,
      subject: payload.subject,
      classification: { category: 'Sensitive', intent: 'Salary offer discussion', priority: 'High', confidence: 0.98, sensitivity: 'High' },
      rag_context: { sources: ['email_guidelines.md'], formatted_text: 'Policy: Any email discussing salary figures (e.g. ₹12 LPA) MUST be escalated to HUMAN_APPROVAL with HIGH risk severity.' },
      planner_decision: { decision: 'HUMAN_APPROVAL', priority: 'High', risk_level: 'HIGH', approval_required: true, approval_rule_applied: 'RULE_FINANCIAL_LEGAL_GATE', reason: 'APPROVAL REQUIRED: Contains sensitive financial, salary, or legal topics. Risk Level: HIGH.', confidence: 0.99 },
      quality_audit: { approved: false, risk_level: 'HIGH', approval_required: true, approval_rule_applied: 'RULE_FINANCIAL_LEGAL_GATE', issues: ['Contains sensitive salary or compensation terms.'] },
      draft_response: { subject: `Re: ${payload.subject}`, body: `Dear HR Operations,\n\nThank you for extending this offer. I have received the proposed compensation details and will review them thoroughly.\n\nBest regards,\nPradeep Kumar A.` },
      final_action: 'HUMAN_APPROVAL',
      action_reason: 'Financial Safety Gate: Escalated to Human Approval Queue.',
      processing_time_ms: 1100,
      pipeline_trace: [
        { step: 'PREPROCESS', status: 'COMPLETED', details: 'Cleaned email text' },
        { step: 'CLASSIFY', status: 'COMPLETED', category: 'Sensitive', priority: 'High', confidence: 0.98, details: 'Identified compensation offer discussion' },
        { step: 'PLAN', status: 'COMPLETED', decision: 'HUMAN_APPROVAL', priority: 'High', risk_level: 'HIGH', approval_required: true, approval_rule_applied: 'RULE_FINANCIAL_LEGAL_GATE', reason: 'Financial terms require human authority.' },
        { step: 'QUEUE_HUMAN_APPROVAL', status: 'PENDING', priority: 'High', risk_level: 'HIGH', approval_rule: 'RULE_FINANCIAL_LEGAL_GATE', reason: 'Financial terms require human authority.', details: 'Held for supervisor review.' }
      ]
    };
  } else if (bodyLower.includes('voucher') || bodyLower.includes('winner') || bodyLower.includes('claim')) {
    result = {
      message_id: demoId,
      thread_id: payload.thread_id || 'thread_spam_888',
      sender: payload.sender,
      subject: payload.subject,
      classification: { category: 'Spam/Low Value', intent: 'Promotional marketing scam', priority: 'Low', confidence: 0.99 },
      rag_context: { sources: ['email_guidelines.md'], formatted_text: 'Policy: Unsolicited bulk marketing and scam pitches MUST be ignored.' },
      planner_decision: { decision: 'IGNORE', priority: 'Low', risk_level: 'LOW', approval_required: false, approval_rule_applied: 'RULE_SPAM_FILTER', reason: 'Spam or promotional message detected; ignoring to conserve resources.', confidence: 0.99 },
      quality_audit: { approved: true, risk_level: 'LOW', approval_required: false, approval_rule_applied: 'RULE_SPAM_FILTER', issues: [] },
      draft_response: { subject: '', body: '', reasoning_summary: 'No reply drafted for spam.' },
      final_action: 'IGNORE',
      action_reason: 'Spam filter gate: Dispatched zero messages.',
      processing_time_ms: 850,
      pipeline_trace: [
        { step: 'PREPROCESS', status: 'COMPLETED', details: 'Identified promotional lottery pattern' },
        { step: 'CLASSIFY', status: 'COMPLETED', category: 'Spam/Low Value', priority: 'Low', confidence: 0.99, details: 'Classified as promotional spam' },
        { step: 'PLAN', status: 'COMPLETED', decision: 'IGNORE', priority: 'Low', risk_level: 'LOW', approval_required: false, approval_rule_applied: 'RULE_SPAM_FILTER', reason: 'Filtered unsolicited noise' }
      ]
    };
  } else if (bodyLower.includes('following up') || bodyLower.includes('previous message') || (payload.thread_id && payload.thread_id.includes('interview'))) {
    result = {
      message_id: demoId,
      thread_id: payload.thread_id || 'thread_interview_901',
      sender: payload.sender,
      subject: payload.subject,
      classification: { category: 'Follow-up', intent: 'Recruiter follow-up on interview', priority: 'High', confidence: 0.96 },
      rag_context: { sources: ['academic_background.md'], formatted_text: 'Candidate: Pradeep Kumar A. (B.Tech AI & DS, Anna University).' },
      planner_decision: { decision: 'AUTO_REPLY', priority: 'High', risk_level: 'LOW', approval_required: false, approval_rule_applied: 'RULE_AUTONOMOUS_SAFE_REPLY', reason: 'Follow-up on known interview thread. Memory context available.', confidence: 0.94 },
      quality_audit: { approved: true, risk_level: 'LOW', approval_required: false, approval_rule_applied: 'RULE_AUTONOMOUS_SAFE_REPLY', issues: [] },
      draft_response: {
        subject: `Re: ${payload.subject}`,
        body: `Dear Recruiter,\n\nFollowing up on our earlier discussion regarding the technical interview, I wanted to confirm that I received your note. I look forward to coordinating the next steps.\n\nBest regards,\nPradeep Kumar A.\nB.Tech Artificial Intelligence & Data Science`,
        reasoning_summary: 'Maintained thread continuity citing prior conversation memory.'
      },
      final_action: 'AUTO_REPLY',
      action_reason: 'Draft verified safe for autonomous dispatch (Thread Memory Activated).',
      processing_time_ms: 1020,
      pipeline_trace: [
        { step: 'PREPROCESS', status: 'COMPLETED', details: 'Cleaned email text' },
        { step: 'CLASSIFY', status: 'COMPLETED', category: 'Follow-up', priority: 'High', confidence: 0.96, details: 'Follow-up on active interview thread' },
        { step: 'RETRIEVE_MEMORY', status: 'COMPLETED', is_thread_existing: true, turn_history_count: 2, summary: 'Thread with recruiter. Prior discussion: interview scheduling.', details: 'Loaded 2 prior thread turns from SQLite' },
        { step: 'PLAN', status: 'COMPLETED', decision: 'AUTO_REPLY', priority: 'High', risk_level: 'LOW', approval_required: false, approval_rule_applied: 'RULE_AUTONOMOUS_SAFE_REPLY', reason: 'Thread continuity grounded in memory.' },
        { step: 'DISPATCH', status: 'COMPLETED', dispatch_mode: 'TEST_MODE_SIMULATION', delivery_status: 'SIMULATED_SUCCESS', details: 'Email safely simulated.' }
      ]
    };
  } else {
    // General / Resume inquiry
    result = {
      message_id: demoId,
      thread_id: payload.thread_id || 'thread_resume_102',
      sender: payload.sender,
      subject: payload.subject,
      classification: { category: 'Job', intent: 'Resume & profile inquiry', priority: 'Medium', confidence: 0.92 },
      rag_context: { sources: ['resume_summary.md', 'technical_skills.md'], formatted_text: 'Pradeep Kumar A. - AI Engineer (Anna University, CGPA: 8.85). Intern at CogniFlow Systems. Specializing in Agentic AI, Llama 3.1, n8n, and Python.' },
      planner_decision: { decision: 'AUTO_REPLY', priority: 'Medium', risk_level: 'LOW', approval_required: false, approval_rule_applied: 'RULE_AUTONOMOUS_SAFE_REPLY', reason: 'Request is factual, safe, and 100% supported by RAG knowledge base.', confidence: 0.93 },
      quality_audit: { approved: true, risk_level: 'LOW', approval_required: false, approval_rule_applied: 'RULE_AUTONOMOUS_SAFE_REPLY', issues: [] },
      draft_response: { subject: `Re: ${payload.subject}`, body: `Dear Recruiter,\n\nThank you for reaching out! My resume is attached. I am a Final-Year B.Tech AI & Data Science student at Anna University with an 8.85 CGPA. I completed an internship at CogniFlow Systems and specialize in Agentic AI architectures, RAG pipelines, and n8n workflow engineering.\n\nBest regards,\nPradeep Kumar A.` },
      final_action: 'AUTO_REPLY',
      action_reason: 'Draft verified safe for autonomous dispatch (RAG Grounded).',
      processing_time_ms: 1350,
      pipeline_trace: [
        { step: 'PREPROCESS', status: 'COMPLETED', details: 'Cleaned email text' },
        { step: 'CLASSIFY', status: 'COMPLETED', category: 'Job', priority: 'Medium', confidence: 0.92, details: 'Inquiry regarding resume and background' },
        { step: 'RETRIEVE_RAG', status: 'COMPLETED', sources: ['resume_summary.md', 'technical_skills.md'], details: 'Retrieved academic & technical skills profile' },
        { step: 'PLAN', status: 'COMPLETED', decision: 'AUTO_REPLY', priority: 'Medium', risk_level: 'LOW', approval_required: false, approval_rule_applied: 'RULE_AUTONOMOUS_SAFE_REPLY', reason: 'Factual grounding verified.' },
        { step: 'DISPATCH', status: 'COMPLETED', dispatch_mode: 'TEST_MODE_SIMULATION', delivery_status: 'SIMULATED_SUCCESS', details: 'Email safely simulated.' }
      ]
    };
  }

  displayTrace(result, true);

  // Authoritative State Update
  auditRecords.unshift({
    id: Date.now(),
    message_id: result.message_id,
    created_at: new Date().toLocaleTimeString('en-US', { hour12: true }),
    sender: payload.sender,
    subject: payload.subject,
    category: result.classification.category,
    priority: result.classification.priority || 'Medium',
    planner_decision: result.planner_decision.decision,
    risk_level: result.quality_audit.risk_level || result.planner_decision.risk_level || 'LOW',
    final_action: result.final_action,
    processing_time_ms: result.processing_time_ms
  });

  if (result.final_action === 'HUMAN_APPROVAL') {
    pendingApprovals.unshift({
      message_id: result.message_id,
      thread_id: result.thread_id,
      sender: payload.sender,
      subject: payload.subject,
      original_body: payload.body,
      draft_body: result.draft_response.body,
      planner_decision: result.planner_decision.decision,
      priority: result.planner_decision.priority || 'High',
      risk_level: result.quality_audit.risk_level || 'MEDIUM',
      approval_rule_applied: result.planner_decision.approval_rule_applied || 'RULE_CALENDAR_UNVERIFIED_GATE',
      reason: result.planner_decision.reason || result.action_reason
    });
  }

  renderDecisionsTable(auditRecords);
  renderApprovals(pendingApprovals);
  updateStats(computeStatsFromLocal());
}

function animatePipelineTrack() {
  const nodes = document.querySelectorAll('.step-node');
  nodes.forEach(n => {
    n.classList.remove('active', 'completed');
  });

  let current = 0;
  const interval = setInterval(() => {
    if (current < nodes.length) {
      if (current > 0) nodes[current - 1].classList.remove('active'), nodes[current - 1].classList.add('completed');
      nodes[current].classList.add('active');
      current++;
    } else {
      clearInterval(interval);
      nodes[nodes.length - 1].classList.remove('active');
      nodes[nodes.length - 1].classList.add('completed');
    }
  }, 350);
}

// ISSUE 2 FIX:
// Render structured human-readable steps without raw JSON dump.
// Keep technical raw JSON available in an expandable debug panel.
function displayTrace(res, isSimulated = false) {
  document.getElementById('trace-empty').style.display = 'none';
  document.getElementById('trace-overview-content').style.display = 'block';

  // Summary box
  const summaryBox = document.getElementById('trace-summary-box');
  const actionColor = (res.final_action === 'AUTO_REPLY' || res.final_action === 'APPROVED_AND_SENT') ? 'var(--color-green)'
    : (res.final_action === 'HUMAN_APPROVAL' ? 'var(--color-amber)' : 'var(--color-blue)');

  summaryBox.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
      <span style="font-weight:700; color:${actionColor}; font-size:0.95rem;">Action: ${escapeHtml(res.final_action)}</span>
      <span class="badge badge-outline">Processed in ${res.processing_time_ms} ms</span>
    </div>
    <div style="font-size:0.8rem; color:var(--text-secondary); margin-bottom:0.25rem;">${escapeHtml(res.action_reason)}</div>
    ${isSimulated ? '<div style="font-size:0.75rem; color:var(--color-accent); font-style:italic;">💡 Simulated demo execution on GitHub Pages. Connect local FastAPI backend on port 8000 for live Ollama inference.</div>' : ''}
  `;

  // Structured Steps Timeline
  const stepsList = document.getElementById('trace-steps-list');
  const traceItems = res.pipeline_trace || [];

  stepsList.innerHTML = traceItems.map((t, index) => {
    let extra = '';
    const stepName = t.step || `STEP_${index + 1}`;
    const status = t.status || 'COMPLETED';

    if (stepName === 'PREPROCESS') {
      extra = `Cleaned incoming message. ${escapeHtml(t.details || 'Signatures and quote history stripped.')}`;
    } else if (stepName === 'CLASSIFY') {
      extra = `Category: <strong>${escapeHtml(t.category)}</strong> &bull; Priority: <strong>${escapeHtml(t.priority || 'Medium')}</strong> &bull; Confidence: <strong>${Math.round((t.confidence || 0.9) * 100)}%</strong>`;
    } else if (stepName === 'RETRIEVE_RAG') {
      const sources = (t.sources || []).map(s => s.split('/').pop()).join(', ') || 'knowledge_base';
      extra = `Retrieved authentic knowledge chunks from: <code>${escapeHtml(sources)}</code>`;
    } else if (stepName === 'RETRIEVE_MEMORY') {
      extra = `Thread Existing: <strong>${t.is_thread_existing ? 'YES' : 'NO (New Conversation)'}</strong> &bull; Turns: <strong>${t.turn_history_count ?? 0}</strong> &bull; ${escapeHtml(t.details || 'Conversation memory checked.')}`;
    } else if (stepName === 'CALENDAR_LOOKUP') {
      const avail = t.availability_result || 'UNVERIFIED';
      const badgeCls = avail === 'AVAILABLE' ? 'badge-success' : (avail === 'CONFLICT' ? 'badge-danger' : 'badge-warning');
      extra = `Slot: <strong>${escapeHtml(t.requested_slot || '-')}</strong> &bull; Result: <span class="badge ${badgeCls}">${escapeHtml(avail)}</span> &bull; ${escapeHtml(t.details || '')}`;
    } else if (stepName === 'PLAN') {
      extra = `Decision: <strong style="color:var(--color-pink);">${escapeHtml(t.decision)}</strong> &bull; Risk: <strong>${escapeHtml(t.risk_level || t.risk_severity || 'LOW')}</strong> &bull; Priority: <strong>${escapeHtml(t.priority || 'Medium')}</strong> &bull; Rule: <code>${escapeHtml(t.approval_rule_applied || 'DEFAULT')}</code><br><span style="font-size:0.75rem; color:var(--text-muted);">${escapeHtml(t.reason || '')}</span>`;
    } else if (stepName === 'WRITE_DRAFT') {
      extra = `Subject: <strong>${escapeHtml(t.draft_subject || 'Re: Subject')}</strong> &bull; ${escapeHtml(t.details || (t.snippet ? `Snippet: "${t.snippet}"` : 'Draft prepared.'))}`;
    } else if (stepName === 'QUALITY_AUDIT') {
      const issuesText = (t.issues && t.issues.length > 0) ? `Flagged: ${t.issues.join('; ')}` : 'No policy violations detected.';
      extra = `Risk Level: <strong>${escapeHtml(t.risk_level || 'LOW')}</strong> &bull; Approved: <strong>${t.audit_approved ? 'YES' : 'NO'}</strong> &bull; ${escapeHtml(issuesText)}`;
    } else if (stepName === 'QUEUE_HUMAN_APPROVAL') {
      extra = `Held for supervisor review. Reason: <strong>${escapeHtml(t.reason || t.details || 'Zero-Hallucination Gate enforced.')}</strong>`;
    } else if (stepName === 'DISPATCH') {
      extra = `Mode: <strong>${escapeHtml(t.dispatch_mode || 'SIMULATED')}</strong> &bull; Status: <strong>${escapeHtml(t.delivery_status || 'SIMULATED_SUCCESS')}</strong> &bull; ${escapeHtml(t.details || '')}`;
    } else {
      // Fallback for any other step: Parse into structured readable key-values without dumping raw JSON
      const cleanDetails = Object.entries(t)
        .filter(([k]) => !['step', 'status'].includes(k))
        .map(([k, v]) => `<strong>${k}:</strong> ${typeof v === 'object' ? JSON.stringify(v) : escapeHtml(String(v))}`)
        .join(' &bull; ');
      extra = cleanDetails || 'Step executed successfully.';
    }

    return `
      <div class="timeline-item">
        <div>
          <div class="timeline-step-title">
            <span>${index + 1}. ${escapeHtml(stepName)}</span>
            <span class="badge ${status === 'COMPLETED' ? 'badge-success' : 'badge-warning'}">${escapeHtml(status)}</span>
          </div>
          <div class="timeline-step-desc">${extra}</div>
        </div>
      </div>
    `;
  }).join('');

  // Expandable Technical Debug Panel (Issue 2)
  const debugPanelHtml = `
    <details class="tech-debug-panel" style="margin-top:1rem; border:1px solid var(--border-color); border-radius:6px; padding:0.5rem 0.75rem; background:rgba(0,0,0,0.25);">
      <summary style="cursor:pointer; font-size:0.75rem; color:var(--text-secondary); font-weight:600;">🛠️ Expand Technical Raw JSON Trace (for Examiners / Technical Audit)</summary>
      <pre class="code-block" style="margin-top:0.5rem; max-height:220px; overflow-y:auto; font-size:0.72rem;">${escapeHtml(JSON.stringify(res, null, 2))}</pre>
    </details>
  `;
  stepsList.insertAdjacentHTML('beforeend', debugPanelHtml);

  // Tab: Planner Logic
  document.getElementById('tab-planner-code').textContent = JSON.stringify(res.planner_decision, null, 2);

  // Tab: RAG
  const ragInfo = document.getElementById('tab-rag-info');
  ragInfo.innerHTML = `<div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:0.5rem;">Sources cited: ${(res.rag_context && res.rag_context.sources ? res.rag_context.sources.join(', ') : 'General Knowledge Base')}</div>`;
  document.getElementById('tab-rag-code').textContent = (res.rag_context && res.rag_context.formatted_text) ? res.rag_context.formatted_text : 'No chunk text';

  // Tab: Quality
  document.getElementById('tab-quality-code').textContent = JSON.stringify(res.quality_audit, null, 2);

  // Tab: Response
  document.getElementById('response-subject-display').textContent = `Subject: ${(res.draft_response && res.draft_response.subject) ? res.draft_response.subject : '(None)'}`;
  document.getElementById('response-body-display').textContent = (res.draft_response && res.draft_response.body) ? res.draft_response.body : '(No response drafted - Email Ignored or Pending)';
}

// ISSUE 5 FIX:
// Approval Actions with Duplicate Prevention, Audit Logging, and Delivery Outcome Reporting
window.handleApprove = async function(messageId) {
  if (!confirm('Approve and dispatch this verified email draft?')) return;

  if (isBackendConnected) {
    try {
      const res = await fetch(`${API_BASE}/approval`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message_id: messageId, comment: 'Supervisor approved from dashboard UI' })
      });
      const data = await res.json();
      if (res.ok) {
        const deliveryMsg = data.dispatch ? `Delivery Status: ${data.dispatch.delivery_status} (Exact Draft SHA: ${data.dispatch.body_sha256})` : 'Delivered safely.';
        alert(`✓ Email Approved!\n${deliveryMsg}`);
        await refreshAllData();
      } else {
        alert(`Approval rejected: ${data.detail || 'Could not approve email'}`);
      }
    } catch (err) {
      alert(`Approval error: ${err.message}`);
    }
  } else {
    // Client-side offline/demo mode fallback
    pendingApprovals = pendingApprovals.filter(item => item.message_id !== messageId);
    const rec = auditRecords.find(r => r.message_id === messageId || r.id === messageId);
    if (rec) rec.final_action = 'APPROVED_AND_SENT';
    renderApprovals(pendingApprovals);
    renderDecisionsTable(auditRecords);
    updateStats(computeStatsFromLocal());
    alert('✓ Draft approved! Simulated delivery recorded: SIMULATED_SUCCESS (TEST_MODE=true).');
  }
};

window.handleRejectApproval = async function(messageId) {
  if (!confirm('Reject and halt this draft? No email will be dispatched.')) return;

  if (isBackendConnected) {
    try {
      const res = await fetch(`${API_BASE}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message_id: messageId, comment: 'Supervisor rejected from dashboard UI' })
      });
      const data = await res.json();
      if (res.ok) {
        alert('✖ Email rejected and halted. Delivery Status: NOT_SENT.');
        await refreshAllData();
      } else {
        alert(`Rejection failed: ${data.detail || 'Could not reject email'}`);
      }
    } catch (err) {
      alert(`Rejection error: ${err.message}`);
    }
  } else {
    // Client-side offline/demo mode fallback
    pendingApprovals = pendingApprovals.filter(item => item.message_id !== messageId);
    const rec = auditRecords.find(r => r.message_id === messageId || r.id === messageId);
    if (rec) rec.final_action = 'REJECTED_STOP';
    renderApprovals(pendingApprovals);
    renderDecisionsTable(auditRecords);
    updateStats(computeStatsFromLocal());
    alert('✖ Email draft rejected and stopped. Delivery Status: NOT_SENT.');
  }
};

window.openEditModal = function(messageId, sender, subject, reason, draftBody) {
  modalMessageId.value = messageId;
  modalSenderSubject.textContent = `To: ${sender} | Subject: ${subject}`;
  modalFlagReason.textContent = reason;
  modalEditedBody.value = draftBody;
  editModal.style.display = 'flex';
};

async function handleModalSubmit() {
  const messageId = modalMessageId.value;
  const editedBody = modalEditedBody.value.trim();
  if (!editedBody) {
    alert('Email body cannot be empty.');
    return;
  }

  if (isBackendConnected) {
    try {
      const res = await fetch(`${API_BASE}/edit-response`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message_id: messageId,
          edited_body: editedBody,
          comment: 'Edited and re-verified via supervisor modal'
        })
      });
      const data = await res.json();
      if (res.status === 400) {
        alert(`Edit Blocked: ${data.detail || 'Cannot edit dispatched email'}`);
      } else if (data.status === 'warning') {
        alert(`Safety Warning: ${data.message}\nIssues: ${data.audit.issues.join(', ')}`);
      } else {
        alert(`✓ Edited response passed quality audit and was dispatched successfully!\nDelivery Status: ${data.delivery_status || 'SENT'}`);
        editModal.style.display = 'none';
        await refreshAllData();
      }
    } catch (err) {
      alert(`Error submitting edit: ${err.message}`);
    }
  } else {
    // Client-side offline/demo mode fallback
    pendingApprovals = pendingApprovals.filter(item => item.message_id !== messageId);
    const rec = auditRecords.find(r => r.message_id === messageId || r.id === messageId);
    if (rec) rec.final_action = 'EDITED_AND_SENT';
    editModal.style.display = 'none';
    renderApprovals(pendingApprovals);
    renderDecisionsTable(auditRecords);
    updateStats(computeStatsFromLocal());
    alert('✓ Edited response re-verified and simulated successfully! Delivery Status: SIMULATED_SUCCESS.');
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function escapeJs(str) {
  if (!str) return '';
  return String(str).replace(/'/g, "\\'").replace(/\n/g, '\\n').replace(/\r/g, '');
}
