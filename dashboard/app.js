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
  refreshAllData();
  // Auto refresh every 8 seconds
  setInterval(refreshAllData, 8000);
});

function setupEventListeners() {
  document.getElementById('btn-refresh-data').addEventListener('click', refreshAllData);
  document.getElementById('btn-clear-form').addEventListener('click', () => {
    senderInput.value = '';
    subjectInput.value = '';
    bodyInput.value = '';
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
      const data = await res.json();
      statsElements.total.textContent = data.total_emails_processed || 0;
      statsElements.auto.textContent = data.auto_replies || 0;
      statsElements.approvals.textContent = data.human_approvals || 0;
      statsElements.clarifications.textContent = data.clarification_requests || 0;
      statsElements.tools.textContent = data.tool_required_cases || 0;
      statsElements.ignored.textContent = data.ignored_emails || 0;
      statsElements.highrisk.textContent = data.high_risk_emails || 0;
      statsElements.speed.textContent = `${data.avg_processing_time_ms || 0} ms`;
    }
  } catch (err) {
    console.error('Failed to fetch stats:', err);
  }
}

async function fetchEmails() {
  try {
    const res = await fetch(`${API_BASE}/emails?limit=20`);
    if (res.ok) {
      const data = await res.json();
      renderDecisionsTable(data.emails || []);
      const countEl = document.getElementById('records-count');
      if (countEl) countEl.textContent = `${data.count || 0} Records`;
    }
  } catch (err) {
    console.error('Failed to fetch emails:', err);
  }
}

async function fetchApprovals() {
  try {
    const res = await fetch(`${API_BASE}/approvals?status=PENDING`);
    if (res.ok) {
      const data = await res.json();
      renderApprovals(data.items || []);
    }
  } catch (err) {
    console.error('Failed to fetch approvals:', err);
  }
}

function renderDecisionsTable(emails) {
  if (!emails || emails.length === 0) {
    decisionsTableBody.innerHTML = `<tr><td colspan="9" class="text-center text-muted">No emails processed yet.</td></tr>`;
    return;
  }

  decisionsTableBody.innerHTML = emails.map(email => {
    const actionBadgeClass = email.final_action === 'AUTO_REPLY' ? 'badge-success'
      : (email.final_action === 'HUMAN_APPROVAL' ? 'badge-warning'
      : (email.final_action === 'IGNORE' ? 'badge-outline' : 'badge-accent'));

    const riskBadgeClass = email.risk_level === 'HIGH' ? 'badge-danger'
      : (email.risk_level === 'MEDIUM' ? 'badge-warning' : 'badge-success');

    const formattedTime = email.created_at ? email.created_at.split(' ')[1] || email.created_at : '-';

    return `
      <tr>
        <td>${formattedTime}</td>
        <td title="${escapeHtml(email.sender)}"><strong>${escapeHtml(email.sender.split('<')[0])}</strong></td>
        <td>${escapeHtml(email.subject)}</td>
        <td><span class="badge badge-outline">${email.category || '-'}</span></td>
        <td>${email.priority || '-'}</td>
        <td><code>${email.planner_decision || '-'}</code></td>
        <td><span class="badge ${riskBadgeClass}">${email.risk_level || 'LOW'}</span></td>
        <td><span class="badge ${actionBadgeClass}">${email.final_action || '-'}</span></td>
        <td>${email.processing_time_ms ? `${email.processing_time_ms}ms` : '-'}</td>
      </tr>
    `;
  }).join('');
}

function renderApprovals(items) {
  approvalsCount.textContent = `${items.length} Pending`;
  if (!items || items.length === 0) {
    approvalList.innerHTML = `<div class="empty-state">No pending approval requests. System is operating safely.</div>`;
    return;
  }

  approvalList.innerHTML = items.map(item => `
    <div class="approval-card" id="approval-${item.message_id}">
      <div class="approval-header">
        <div>
          <div class="approval-meta">From: <strong>${escapeHtml(item.sender)}</strong> &bull; Subject: <strong>${escapeHtml(item.subject)}</strong></div>
          <div style="font-size: 0.75rem; color: var(--color-amber); margin-top: 0.2rem;">
            Flagged Reason: ${escapeHtml(item.reason)}
          </div>
        </div>
        <div style="display:flex; gap:0.4rem;">
          <span class="badge badge-warning">${item.planner_decision}</span>
          <span class="badge badge-danger">Risk: ${item.risk_level}</span>
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
        <button class="btn btn-secondary btn-sm" onclick="openEditModal('${item.message_id}', '${escapeJs(item.sender)}', '${escapeJs(item.subject)}', '${escapeJs(item.reason)}', '${escapeJs(item.draft_body)}')">
          ✏️ Edit & Re-Verify
        </button>
        <button class="btn btn-danger btn-sm" onclick="handleRejectApproval('${item.message_id}')">
          ✖ Reject
        </button>
        <button class="btn btn-success btn-sm" onclick="handleApprove('${item.message_id}')">
          ✓ Approve & Send
        </button>
      </div>
    </div>
  `).join('');
}

async function handleProcessEmail() {
  const payload = {
    sender: senderInput.value.trim(),
    thread_id: threadInput.value.trim() || undefined,
    subject: subjectInput.value.trim(),
    body: bodyInput.value.trim()
  };

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
      const result = data.result;
      displayTrace(result);
      traceBadge.textContent = 'Success';
      traceBadge.className = 'badge badge-success';
      await refreshAllData();
    } else {
      // Fallback to client-side simulation (e.g., when hosted statically on GitHub Pages)
      simulateClientSidePipeline(payload);
    }
  } catch (err) {
    // Fallback to client-side simulation when backend API is unreachable (GitHub Pages deployment)
    console.warn('Backend API unreachable. Running in client-side interactive simulation mode for GitHub Pages.');
    simulateClientSidePipeline(payload);
  } finally {
    processBtn.disabled = false;
    spinner.style.display = 'none';
    processBtnText.textContent = '🚀 Run Agentic AI Pipeline';
  }
}

function simulateClientSidePipeline(payload) {
  const bodyLower = (payload.body || '').toLowerCase();
  const subjectLower = (payload.subject || '').toLowerCase();
  const traceBadge = document.getElementById('trace-status-badge');
  traceBadge.textContent = 'Demo Mode (GitHub Pages)';
  traceBadge.className = 'badge badge-accent';

  let result;
  if (bodyLower.includes('interview') || bodyLower.includes('schedule') || subjectLower.includes('interview')) {
    result = {
      message_id: 'gh_demo_01',
      thread_id: payload.thread_id || 'thread_interview_901',
      sender: payload.sender,
      subject: payload.subject,
      classification: {
        category: 'Interview',
        intent: 'Interview scheduling request',
        priority: 'High',
        confidence: 0.95,
        sensitivity: 'Medium',
        entities: ['interview', 'ai engineer']
      },
      rag_context: {
        sources: ['knowledge_base/education/academic_background.md', 'knowledge_base/response_guidelines/email_guidelines.md'],
        formatted_text: 'Rule: NEVER commit to an interview time unless calendar availability is verified.\nCandidate: Pradeep Kumar A. (B.Tech AI & DS, Anna University, CGPA: 8.85/10).'
      },
      planner_decision: {
        decision: 'HUMAN_APPROVAL',
        reason: 'Meeting or interview scheduling requested; calendar availability is unverified. Human approval required to prevent false commitments.',
        confidence: 0.94,
        required_information: ['Verified calendar availability'],
        recommended_action: 'Ask supervisor to confirm availability or request sender for alternative slots'
      },
      quality_audit: {
        approved: true,
        risk_level: 'LOW',
        issues: [],
        reason: 'Response is politely drafted without hallucinated availability commitments.'
      },
      draft_response: {
        subject: `Re: ${payload.subject}`,
        body: `Dear Recruiter,\n\nThank you for considering me for the AI Engineer role. I am excited about this opportunity.\n\nCould you please share your preferred alternative dates and time slots so I can confirm my availability accordingly?\n\nBest regards,\nPradeep Kumar A.\nB.Tech Artificial Intelligence & Data Science`,
        reasoning_summary: 'Polite clarification asking for available slots without inventing calendar availability.'
      },
      final_action: 'HUMAN_APPROVAL',
      action_reason: 'Zero-Hallucination Gate: Rerouted to Human Approval Queue.',
      processing_time_ms: 1240,
      pipeline_trace: [
        { step: 'PREPROCESS', status: 'COMPLETED', details: `Cleaned email text (${payload.body.length} chars)` },
        { step: 'CLASSIFY', status: 'COMPLETED', category: 'Interview', priority: 'High', confidence: 0.95 },
        { step: 'RETRIEVE_RAG', status: 'COMPLETED', sources: ['academic_background.md', 'email_guidelines.md'] },
        { step: 'RETRIEVE_MEMORY', status: 'COMPLETED', is_thread_existing: true, turn_history_count: 1 },
        { step: 'PLAN', status: 'COMPLETED', decision: 'HUMAN_APPROVAL', reason: 'Unverified calendar commitment requested.' },
        { step: 'WRITE_DRAFT', status: 'COMPLETED', draft_subject: `Re: ${payload.subject}` },
        { step: 'QUALITY_AUDIT', status: 'COMPLETED', risk_level: 'LOW', audit_approved: true },
        { step: 'QUEUE_HUMAN_APPROVAL', status: 'PENDING', reason: 'Zero-Hallucination Gate enforced.' }
      ]
    };
  } else if (bodyLower.includes('salary') || bodyLower.includes('lpa') || bodyLower.includes('ctc')) {
    result = {
      message_id: 'gh_demo_02',
      thread_id: payload.thread_id || 'thread_salary_404',
      sender: payload.sender,
      subject: payload.subject,
      classification: { category: 'Sensitive', intent: 'Salary offer discussion', priority: 'High', confidence: 0.98, sensitivity: 'High' },
      rag_context: { sources: ['email_guidelines.md'], formatted_text: 'Policy: Any email discussing salary figures (e.g. ₹12 LPA) MUST be escalated to HUMAN_APPROVAL.' },
      planner_decision: { decision: 'HUMAN_APPROVAL', reason: 'Contains financial/salary offer terms requiring human sign-off.', confidence: 0.99 },
      quality_audit: { approved: true, risk_level: 'LOW', issues: [] },
      draft_response: { subject: `Re: ${payload.subject}`, body: `Dear HR Operations,\n\nThank you for extending this offer. I have received the proposed compensation details and will review them thoroughly.\n\nBest regards,\nPradeep Kumar A.` },
      final_action: 'HUMAN_APPROVAL',
      action_reason: 'Financial Safety Gate: Escalated to Human Approval Queue.',
      processing_time_ms: 1100,
      pipeline_trace: [
        { step: 'PREPROCESS', status: 'COMPLETED', details: 'Cleaned email text' },
        { step: 'CLASSIFY', status: 'COMPLETED', category: 'Sensitive', priority: 'High', confidence: 0.98 },
        { step: 'PLAN', status: 'COMPLETED', decision: 'HUMAN_APPROVAL', reason: 'Financial terms require human authority.' }
      ]
    };
  } else if (bodyLower.includes('voucher') || bodyLower.includes('winner') || bodyLower.includes('claim')) {
    result = {
      message_id: 'gh_demo_03',
      thread_id: payload.thread_id || 'thread_spam_888',
      sender: payload.sender,
      subject: payload.subject,
      classification: { category: 'Spam/Low Value', intent: 'Promotional marketing scam', priority: 'Low', confidence: 0.99 },
      rag_context: { sources: ['email_guidelines.md'], formatted_text: 'Policy: Unsolicited bulk marketing and scam pitches MUST be ignored.' },
      planner_decision: { decision: 'IGNORE', reason: 'Unsolicited promotional spam detected. Silently filtered.', confidence: 0.99 },
      quality_audit: { approved: true, risk_level: 'LOW', issues: [] },
      draft_response: { subject: '', body: '', reasoning_summary: 'No reply drafted for spam.' },
      final_action: 'IGNORE',
      action_reason: 'Spam filter gate: Dispatched zero messages.',
      processing_time_ms: 850,
      pipeline_trace: [
        { step: 'PREPROCESS', status: 'COMPLETED', details: 'Identified promotional pattern' },
        { step: 'CLASSIFY', status: 'COMPLETED', category: 'Spam/Low Value', priority: 'Low', confidence: 0.99 },
        { step: 'PLAN', status: 'COMPLETED', decision: 'IGNORE', reason: 'Filtered unsolicited noise' }
      ]
    };
  } else {
    // General / Resume inquiry
    result = {
      message_id: 'gh_demo_04',
      thread_id: payload.thread_id || 'thread_resume_102',
      sender: payload.sender,
      subject: payload.subject,
      classification: { category: 'Job', intent: 'Resume & profile inquiry', priority: 'Medium', confidence: 0.92 },
      rag_context: { sources: ['resume_summary.md', 'technical_skills.md'], formatted_text: 'Pradeep Kumar A. - AI Engineer specializing in Agentic AI, Llama 3.1, n8n, and Python.' },
      planner_decision: { decision: 'AUTO_REPLY', reason: 'Request is factual, safe, and 100% supported by RAG knowledge base.', confidence: 0.93 },
      quality_audit: { approved: true, risk_level: 'LOW', issues: [] },
      draft_response: { subject: `Re: ${payload.subject}`, body: `Dear Recruiter,\n\nThank you for reaching out! My resume is attached. I specialize in Agentic AI architectures, RAG pipelines, and n8n workflow engineering.\n\nBest regards,\nPradeep Kumar A.` },
      final_action: 'AUTO_REPLY',
      action_reason: 'Draft verified safe for autonomous dispatch (Simulated).',
      processing_time_ms: 1350,
      pipeline_trace: [
        { step: 'PREPROCESS', status: 'COMPLETED', details: 'Cleaned email text' },
        { step: 'CLASSIFY', status: 'COMPLETED', category: 'Job', priority: 'Medium', confidence: 0.92 },
        { step: 'RETRIEVE_RAG', status: 'COMPLETED', sources: ['resume_summary.md', 'technical_skills.md'] },
        { step: 'PLAN', status: 'COMPLETED', decision: 'AUTO_REPLY', reason: 'Factual grounding verified.' },
        { step: 'DISPATCH', status: 'COMPLETED', dispatch_mode: 'GITHUB_PAGES_PREVIEW', details: 'Email would be dispatched in production mode.' }
      ]
    };
  }

  displayTrace(result);

  // Update table and stats in client-side memory
  const existingRows = decisionsTableBody.innerHTML;
  decisionsTableBody.innerHTML = `
    <tr>
      <td>${new Date().toLocaleTimeString()}</td>
      <td><strong>${escapeHtml(payload.sender.split('<')[0])}</strong></td>
      <td>${escapeHtml(payload.subject)}</td>
      <td><span class="badge badge-outline">${result.classification.category}</span></td>
      <td>${result.classification.priority || 'Medium'}</td>
      <td><code>${result.planner_decision.decision}</code></td>
      <td><span class="badge badge-success">LOW</span></td>
      <td><span class="badge ${result.final_action === 'AUTO_REPLY' ? 'badge-success' : 'badge-warning'}">${result.final_action}</span></td>
      <td>${result.processing_time_ms}ms</td>
    </tr>
  ` + existingRows;

  // Add to approval queue if HUMAN_APPROVAL
  if (result.final_action === 'HUMAN_APPROVAL') {
    const approvalCard = `
      <div class="approval-card" id="approval-${result.message_id}">
        <div class="approval-header">
          <div>
            <div class="approval-meta">From: <strong>${escapeHtml(payload.sender)}</strong> &bull; Subject: <strong>${escapeHtml(payload.subject)}</strong></div>
            <div style="font-size: 0.75rem; color: var(--color-amber); margin-top: 0.2rem;">
              Flagged Reason: ${escapeHtml(result.action_reason)}
            </div>
          </div>
          <div style="display:flex; gap:0.4rem;">
            <span class="badge badge-warning">${result.planner_decision.decision}</span>
            <span class="badge badge-success">Risk: LOW</span>
          </div>
        </div>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.75rem;">
          <div>
            <div style="font-size:0.72rem; color:var(--text-muted); margin-bottom:0.25rem;">Original Email:</div>
            <div class="approval-content-box">${escapeHtml(payload.body)}</div>
          </div>
          <div>
            <div style="font-size:0.72rem; color:var(--text-muted); margin-bottom:0.25rem;">Proposed Safe Draft:</div>
            <div class="approval-content-box">${escapeHtml(result.draft_response.body)}</div>
          </div>
        </div>
        <div class="approval-actions">
          <button class="btn btn-secondary btn-sm" onclick="alert('In GitHub Pages demo mode: You can edit this draft when running locally on Windows!')">✏️ Edit</button>
          <button class="btn btn-danger btn-sm" onclick="document.getElementById('approval-${result.message_id}').remove(); alert('Draft rejected and stopped.');">✖ Reject</button>
          <button class="btn btn-success btn-sm" onclick="document.getElementById('approval-${result.message_id}').remove(); alert('Email approved and safely simulated!');">✓ Approve & Send</button>
        </div>
      </div>
    `;
    approvalList.innerHTML = approvalCard + (approvalList.innerHTML.includes('No pending') ? '' : approvalList.innerHTML);
    approvalsCount.textContent = '1 Pending';
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
  }, 400);
}

function displayTrace(res) {
  document.getElementById('trace-empty').style.display = 'none';
  document.getElementById('trace-overview-content').style.display = 'block';

  // Summary box
  const summaryBox = document.getElementById('trace-summary-box');
  const actionColor = res.final_action === 'AUTO_REPLY' ? 'var(--color-green)'
    : (res.final_action === 'HUMAN_APPROVAL' ? 'var(--color-amber)' : 'var(--color-blue)');

  summaryBox.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
      <span style="font-weight:700; color:${actionColor}; font-size:0.95rem;">Action: ${res.final_action}</span>
      <span class="badge badge-outline">Processed in ${res.processing_time_ms} ms</span>
    </div>
    <div style="font-size:0.8rem; color:var(--text-secondary);">${res.action_reason}</div>
  `;

  // Steps Timeline
  const stepsList = document.getElementById('trace-steps-list');
  stepsList.innerHTML = (res.pipeline_trace || []).map(t => {
    let extra = '';
    if (t.step === 'CLASSIFY') extra = `Category: <strong>${t.category}</strong> (Priority: ${t.priority}, Conf: ${t.confidence})`;
    else if (t.step === 'PLAN') extra = `Decision: <strong style="color:var(--color-pink);">${t.decision}</strong> (${t.reason})`;
    else if (t.step === 'QUALITY_AUDIT') extra = `Risk: <strong>${t.risk_level}</strong> (Approved: ${t.audit_approved})`;
    else if (t.step === 'DISPATCH') extra = `Mode: ${t.dispatch_mode} &bull; ${t.details}`;
    else if (t.step === 'QUEUE_HUMAN_APPROVAL') extra = `Held for supervisor review. Reason: ${t.reason}`;
    else extra = t.details || JSON.stringify(t);

    return `
      <div class="timeline-item">
        <div>
          <div class="timeline-step-title">${t.step}</div>
          <div class="timeline-step-desc">${extra}</div>
        </div>
      </div>
    `;
  }).join('');

  // Tab: Planner Logic
  document.getElementById('tab-planner-code').textContent = JSON.stringify(res.planner_decision, null, 2);

  // Tab: RAG
  const ragInfo = document.getElementById('tab-rag-info');
  ragInfo.innerHTML = `<div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:0.5rem;">Sources cited: ${(res.rag_context.sources || []).join(', ') || 'General Knowledge Base'}</div>`;
  document.getElementById('tab-rag-code').textContent = res.rag_context.formatted_text || 'No chunk text';

  // Tab: Quality
  document.getElementById('tab-quality-code').textContent = JSON.stringify(res.quality_audit, null, 2);

  // Tab: Response
  document.getElementById('response-subject-display').textContent = `Subject: ${res.draft_response.subject || '(None)'}`;
  document.getElementById('response-body-display').textContent = res.draft_response.body || '(No response drafted - Email Ignored or Pending)';
}

// Approval actions
window.handleApprove = async function(messageId) {
  if (!confirm('Approve and dispatch this verified email draft?')) return;
  try {
    const res = await fetch(`${API_BASE}/approval`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message_id: messageId, comment: 'Supervisor approved from dashboard UI' })
    });
    if (res.ok) {
      alert('Email approved and safely dispatched!');
      await refreshAllData();
    }
  } catch (err) {
    alert(`Failed to approve: ${err.message}`);
  }
};

window.handleRejectApproval = async function(messageId) {
  if (!confirm('Reject and halt this draft? No email will be dispatched.')) return;
  try {
    const res = await fetch(`${API_BASE}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message_id: messageId, comment: 'Supervisor rejected from dashboard UI' })
    });
    if (res.ok) {
      alert('Email rejected and stopped.');
      await refreshAllData();
    }
  } catch (err) {
    alert(`Failed to reject: ${err.message}`);
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
    if (data.status === 'warning') {
      alert(`Safety Warning: ${data.message}\nIssues: ${data.audit.issues.join(', ')}`);
    } else {
      alert('Edited response passed quality audit and was dispatched successfully!');
      editModal.style.display = 'none';
      await refreshAllData();
    }
  } catch (err) {
    alert(`Error submitting edit: ${err.message}`);
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function escapeJs(str) {
  if (!str) return '';
  return str.replace(/'/g, "\\'").replace(/\n/g, '\\n').replace(/\r/g, '');
}
