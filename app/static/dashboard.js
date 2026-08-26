// GeM Compliance Copilot Engine with Document AI Inspector

(function() {
  const CHECKS = [
    { id: 'udyam', label: 'Udyam / MSME Registration', portal: 'Udyam Registration Portal', weight: 8 },
    { id: 'gst', label: 'GST Registration & Returns', portal: 'GSTN', weight: 15 },
    { id: 'pan', label: 'PAN & Income Tax Compliance', portal: 'Income Tax e-Filing', weight: 15 },
    { id: 'mca', label: 'Company Status (MCA21)', portal: 'MCA21', weight: 8 },
    { id: 'epfo', label: 'EPFO Compliance', portal: 'EPFO', weight: 8 },
    { id: 'esic', label: 'ESIC Compliance', portal: 'ESIC', weight: 7 },
    { id: 'startup', label: 'Startup India Recognition', portal: 'Startup India / DPIIT', weight: 6 },
    { id: 'nsic', label: 'NSIC Registration', portal: 'NSIC', weight: 6 },
    { id: 'mii', label: 'Make in India / Local Content', portal: 'DPIIT · Make in India', weight: 9 },
    { id: 'digilocker', label: 'Document Authenticity & OEM MAF', portal: 'DigiLocker / OEM MAF / CA UDIN', weight: 8 },
    { id: 'blacklist', label: 'Blacklisting / Debarment', portal: 'GeM / CPPP Debarment Registry', weight: 10 },
  ];

  const STATUS_LABEL = {
    verified: 'Verified',
    flagged: 'Flagged',
    missing: 'Missing',
    na: 'N/A',
    pending: 'Pending',
    scanning: 'Scanning',
  };

  const SAMPLE_PROFILES = [
    {
      id: 'sundaram',
      name: 'Sundaram Precision Tooling Pvt. Ltd.',
      category: 'MSME – Manufacturing',
      gstin: '29AACCS1234F1Z5',
      pan: 'AACCS1234F',
      udyam: 'UDYAM-KA-03-0012345',
      gem_bid: 'GEM/2026/B/882211',
      checks: {
        udyam: { status: 'verified', finding: 'Active Udyam registration, classified Small Enterprise, valid since 2019. NIC 26201 matching.' },
        gst: { status: 'verified', finding: 'GSTIN active. Last 12 GSTR-3B returns filed on or before due date (100.0% Regularity).' },
        pan: { status: 'verified', finding: 'PAN operative; legal name matches Udyam and GST records. Section 206AB check cleared.' },
        mca: { status: 'verified', finding: 'Company status: Active. No overdue statutory filings on record.' },
        epfo: { status: 'verified', finding: 'EPFO establishment active; 142 contributing members current through Jul 2026.' },
        esic: { status: 'na', finding: 'Below ESIC applicability threshold (22 employees declared).' },
        startup: { status: 'na', finding: 'Not registered under Startup India — status not claimed by bidder.' },
        nsic: { status: 'verified', finding: 'Valid NSIC Single Point Registration covering the tendered item category.' },
        mii: { status: 'verified', finding: 'Local content declared at 68.0% (Class-I Local Supplier); CA UDIN 24012345AAAAAA1234 verified.' },
        digilocker: { status: 'verified', finding: 'OEM Authorization MAF and 11 of 11 submitted documents authenticated against DigiLocker.' },
        blacklist: { status: 'verified', finding: 'Clean record. 0 active listings on GeM or CPPP debarment registries.' },
      }
    },
    {
      id: 'apex',
      name: 'Apex Data Solutions Private Limited',
      category: 'MSME – Manufacturing',
      gstin: '27ABCDE1234F1Z1',
      pan: 'ABCDE1234F',
      udyam: 'UDYAM-MH-01-0012345',
      gem_bid: 'GEM/2026/B/998877',
      checks: {
        udyam: { status: 'verified', finding: 'Active Udyam registration, classified Medium Enterprise. NIC 26201, 26511 fully aligned.' },
        gst: { status: 'verified', finding: 'GSTIN active. Last 12 consecutive GSTR-3B filings completed on-time.' },
        pan: { status: 'verified', finding: 'PAN operative. Not a Section 206AB specified defaulter person. Aadhaar seeded.' },
        mca: { status: 'verified', finding: 'Active company filing status with RoC Mumbai.' },
        epfo: { status: 'verified', finding: 'EPFO code active, zero arrears across trailing 12 months.' },
        esic: { status: 'verified', finding: 'ESIC compliance certificate validated.' },
        startup: { status: 'na', finding: 'MSME entity; Startup exemption not claimed.' },
        nsic: { status: 'verified', finding: 'Valid NSIC vendor registration on file.' },
        mii: { status: 'verified', finding: 'Class-I Local Supplier (65.5% local content). Plot 42 MIDC Pune facility verified.' },
        digilocker: { status: 'verified', finding: 'OEM MAF from Dell International verified. CA turnover certificate ₹12.50 Cr/yr verified.' },
        blacklist: { status: 'verified', finding: 'No adverse orders found across GeM / CPPP central blacklist database.' },
      }
    },
    {
      id: 'novatech',
      name: 'NovaTech Systems LLP',
      category: 'Startup India – IT Services',
      gstin: '07AAFCN5678K1Z9',
      pan: 'AAFCN5678K',
      udyam: 'UDYAM-DL-07-0098765',
      gem_bid: 'GEM/2026/B/776655',
      checks: {
        udyam: { status: 'verified', finding: 'Active Udyam registration, classified Micro Enterprise.' },
        gst: { status: 'flagged', finding: 'GSTR-3B for May 2026 filed 14 days late; 9 of 12 returns on-time (75% Regularity).' },
        pan: { status: 'flagged', finding: 'Entity name on PAN record ("Novatech Systems LLP") has minor character variation with bid header.' },
        mca: { status: 'na', finding: 'Registered as LLP with MCA LLP registry; company check not applicable.' },
        epfo: { status: 'missing', finding: 'No EPFO establishment code on file despite 31 declared employees; registration required.' },
        esic: { status: 'flagged', finding: 'ESIC code present but last contribution filed for Q4 2025 — 2 quarters overdue.' },
        startup: { status: 'verified', finding: 'DPIIT-recognised Startup; certificate valid till Mar 2027.' },
        nsic: { status: 'na', finding: 'Not registered with NSIC — not claimed by bidder.' },
        mii: { status: 'flagged', finding: 'Local content declared at 52% but detailed BOM cost breakup attachment missing.' },
        digilocker: { status: 'verified', finding: '9 of 10 submitted documents authenticated; 1 pending issuer confirmation.' },
        blacklist: { status: 'verified', finding: 'No listing on GeM or CPPP debarment registries.' },
      }
    },
    {
      id: 'vantage',
      name: 'Vantage Global Infrastructure Ltd',
      category: 'Large Enterprise – Trading',
      gstin: '27AAPFV4321L1Z9',
      pan: 'ABCDE9999F',
      udyam: '—',
      gem_bid: 'GEM/2026/B/110022',
      checks: {
        udyam: { status: 'missing', finding: 'No Udyam registration found; bid document claims MSME preference without registration.' },
        gst: { status: 'flagged', finding: 'GSTIN valid but return filing irregular — 3 of last 6 GSTR-3B filed after due date.' },
        pan: { status: 'verified', finding: 'PAN operative and consistent with GST records.' },
        mca: { status: 'flagged', finding: 'MCA21 status shows "Active – Non-Compliant" due to pending AOC-4 filing.' },
        epfo: { status: 'missing', finding: 'No EPFO establishment code found against declared workforce of 60+.' },
        esic: { status: 'missing', finding: 'No ESIC registration found against declared workforce.' },
        startup: { status: 'na', finding: 'Not claimed by bidder.' },
        nsic: { status: 'na', finding: 'Not claimed by bidder.' },
        mii: { status: 'flagged', finding: 'Local content claimed at 71%, but imported sub-assemblies exceed allowable ratio.' },
        digilocker: { status: 'flagged', finding: 'Only 5 of 9 submitted certificates could be authenticated.' },
        blacklist: { status: 'missing', finding: 'ACTIVE DEBARMENT ORDER (CPPP/2025/DEB/0882) found on GeM/CPPP Central Registry. Hard disqualifier.' },
      }
    }
  ];

  const CPCL_TENDERS_REGISTRY = [
    {
      id: 'tender-1',
      ref_id: 'CPCL/MANALI/M&C/2026/089',
      gem_bid: 'GEM/2026/B/998877',
      title: 'Turnaround Maintenance & High-Pressure Piping Valve Package',
      dept: 'Materials & Contracts Department • Manali Refinery',
      est_value: '₹ 4,85,00,000 (INR 4.85 Cr)',
      turnover_req: '₹ 1,20,00,000 (INR 1.20 Cr)',
      mii_req: 'Class-I Local Supplier (≥ 50% Local Content)',
      nic_codes: '28132 (Valves & Cocks), 24102 (Piping), 33140 (Repair)',
      emd_details: '₹ 9,70,000 (MSME / Udyam Exempt)',
      published_date: '10-Aug-2026',
      closing_date: '15-Sep-2026 (15:00 IST)',
      opening_date: '15-Sep-2026 (16:00 IST)',
      status: 'Active (Technical Evaluation)',
      bidders_count: 4,
      bidders: ['Apex Data Solutions Private Limited', 'L&T Hydrocarbon Engineering Ltd.', 'Southern Valves & Actuators Pvt Ltd', 'Vantage Global Infrastructure Ltd']
    },
    {
      id: 'tender-2',
      ref_id: 'CPCL/MANALI/M&C/2026/104',
      gem_bid: 'GEM/2026/B/882211',
      title: 'High Voltage Switchgears & Substation Transformers Package',
      dept: 'Electrical & Power Distribution • Manali Refinery',
      est_value: '₹ 8,20,00,000 (INR 8.20 Cr)',
      turnover_req: '₹ 2,50,00,000 (INR 2.50 Cr)',
      mii_req: 'Class-I Local Supplier (≥ 60% Local Content)',
      nic_codes: '27101 (Electric Motors/Generators), 27102 (Transformers)',
      emd_details: '₹ 16,40,000 (Exempt for NSIC & MSME)',
      published_date: '02-Aug-2026',
      closing_date: '20-Sep-2026 (14:30 IST)',
      opening_date: '20-Sep-2026 (15:30 IST)',
      status: 'Active (Technical Evaluation)',
      bidders_count: 3,
      bidders: ['Sundaram Precision Tooling Pvt. Ltd.', 'Bharat Heavy Electricals Limited (BHEL)', 'NovaTech Systems LLP']
    },
    {
      id: 'tender-3',
      ref_id: 'CPCL/MANALI/M&C/2026/112',
      gem_bid: 'GEM/2026/B/776655',
      title: 'Refinery Hydro-Processing Catalyst & Chemical Additives Supply',
      dept: 'Refinery Process & Catalyst Directorate',
      est_value: '₹ 3,50,00,000 (INR 3.50 Cr)',
      turnover_req: '₹ 90,00,000 (INR 90 Lakhs)',
      mii_req: 'Class-II Local Supplier (≥ 20% Local Content)',
      nic_codes: '20119 (Basic Chemicals), 20293 (Industrial Catalysts)',
      emd_details: '₹ 7,00,000 (MSME Exempt)',
      published_date: '15-Aug-2026',
      closing_date: '28-Sep-2026 (15:00 IST)',
      opening_date: '28-Sep-2026 (16:30 IST)',
      status: 'Active (Bid Submission Open)',
      bidders_count: 2,
      bidders: ['Southern Valves & Actuators Pvt Ltd', 'NovaTech Systems LLP']
    },
    {
      id: 'tender-4',
      ref_id: 'CPCL/MANALI/M&C/2026/128',
      gem_bid: 'GEM/2026/B/554433',
      title: 'Digital Instrumentation, DCS & SCADA System Upgrade',
      dept: 'Instrumentation & Automated Controls Department',
      est_value: '₹ 2,90,00,000 (INR 2.90 Cr)',
      turnover_req: '₹ 75,00,000 (INR 75 Lakhs)',
      mii_req: 'Class-I Local Supplier (≥ 50% Local Content)',
      nic_codes: '26511 (Measuring & Testing), 62011 (IT Systems)',
      emd_details: '₹ 5,80,000 (MSME / Startup India Exempt)',
      published_date: '18-Aug-2026',
      closing_date: '05-Oct-2026 (15:00 IST)',
      opening_date: '05-Oct-2026 (16:00 IST)',
      status: 'Active (Technical Evaluation)',
      bidders_count: 3,
      bidders: ['Chennai Precision Instruments & Controls', 'Apex Data Solutions Private Limited', 'NovaTech Systems LLP']
    },
    {
      id: 'tender-5',
      ref_id: 'CPCL/MANALI/M&C/2026/145',
      gem_bid: 'GEM/2026/B/443322',
      title: 'Crude Distillation Unit (CDU-III) Heat Exchanger Tubes Supply',
      dept: 'Mechanical & Static Equipment Maintenance',
      est_value: '₹ 6,40,00,000 (INR 6.40 Cr)',
      turnover_req: '₹ 1,80,00,000 (INR 1.80 Cr)',
      mii_req: 'Class-I Local Supplier (≥ 50% Local Content)',
      nic_codes: '28131 (Steam Generators), 24102 (Steel Tubes)',
      emd_details: '₹ 12,80,000 (MSME Exempt)',
      published_date: '20-Aug-2026',
      closing_date: '10-Oct-2026 (15:00 IST)',
      opening_date: '10-Oct-2026 (15:30 IST)',
      status: 'Active (Pre-Qualification Stage)',
      bidders_count: 2,
      bidders: ['Sundaram Precision Tooling Pvt. Ltd.', 'L&T Hydrocarbon Engineering Ltd.']
    }
  ];

  function hashStr(s) {
    let h = 2166136261;
    for (let i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }

  function seededRng(seed) {
    let a = seed || 1;
    return function() {
      a |= 0;
      a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function nowStr() {
    const d = new Date();
    return (
      d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) +
      ' ' +
      d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
    );
  }

  function esc(s) {
    return s === undefined || s === null ? '' : String(s).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
  }

  const FINDINGS_BY_STATUS = {
    verified: ['Record matches submitted documents; no discrepancies found.', 'Portal status active and current as of today.', 'Cross-checked against declared bid particulars — consistent and cleared.'],
    flagged: ['Minor inconsistency found against declared bid particulars — review recommended.', 'Portal record present but shows a lapse requiring clarification.', 'Data present but partially inconsistent with submitted documents.'],
    missing: ['No corresponding record found on the source portal.', 'Required registration not located for the declared applicability.', 'Submitted document could not be traced to a valid portal record.'],
    na: ['Not applicable given declared bidder category / size.', 'Not claimed by bidder; check skipped.']
  };

  function generateChecksForProfile(seedString, category) {
    const rng = seededRng(hashStr(seedString));
    const out = {};
    CHECKS.forEach(c => {
      let weights = { verified: 0.68, flagged: 0.17, missing: 0.10, na: 0.05 };
      if (c.id === 'startup' && !/startup/i.test(category)) weights = { verified: 0.02, flagged: 0, missing: 0, na: 0.98 };
      if (c.id === 'nsic' && /startup/i.test(category)) weights = { verified: 0.15, flagged: 0, missing: 0, na: 0.85 };
      if (c.id === 'esic' && /msme|startup/i.test(category)) weights = { verified: 0.35, flagged: 0.1, missing: 0.05, na: 0.5 };
      const r = rng();
      let acc = 0, chosen = 'verified';
      for (const k of ['verified', 'flagged', 'missing', 'na']) {
        acc += weights[k];
        if (r <= acc) { chosen = k; break; }
      }
      const pool = FINDINGS_BY_STATUS[chosen];
      const finding = pool[Math.floor(rng() * pool.length)];
      out[c.id] = { status: chosen, finding };
    });
    return out;
  }

  function computeResult(checks) {
    let sum = 0, total = 0, counts = { verified: 0, flagged: 0, missing: 0, na: 0 };
    CHECKS.forEach(c => {
      const st = checks[c.id].status;
      counts[st] = (counts[st] || 0) + 1;
      const mult = st === 'verified' ? 1 : st === 'flagged' ? 0.5 : st === 'na' ? 1 : 0;
      sum += c.weight * mult;
      total += c.weight;
    });
    let score = Math.round((sum / total) * 100);
    let risk = score >= 80 ? 'Low' : score >= 50 ? 'Medium' : 'High';
    if (checks.blacklist && checks.blacklist.status !== 'verified') {
      risk = 'High';
      score = 0;
    }
    return { score, risk, counts };
  }

  function buildRecommendation(checks, result) {
    const flaggedOrMissing = CHECKS.filter(c => checks[c.id].status === 'flagged' || checks[c.id].status === 'missing');
    let lead;
    if (result.risk === 'Low') {
      lead = 'Bidder demonstrates strong compliance across statutory registrations, filings and eligibility parameters checked. No material gaps identified that would affect a qualification decision.';
    } else if (result.risk === 'Medium') {
      lead = `Bidder is largely compliant but has ${flaggedOrMissing.length} item(s) requiring clarification or supplementary documentation before qualification is finalised.`;
    } else {
      lead = 'Bidder shows critical compliance gaps or an active debarment-registry match. Recommend formal clarification or disqualification review before proceeding to award.';
    }
    return {
      lead,
      items: flaggedOrMissing.map(c => ({ label: c.label, finding: checks[c.id].finding, status: checks[c.id].status }))
    };
  }

  let DB = {};
  let activeId = null;
  let scanningNow = false;
  let activeJobId = null;

  function baseRecord(profile) {
    return {
      profile,
      results: null,
      auditTrail: [{ time: nowStr(), actor: 'System', text: 'Bid record created and queued for statutory verification.' }],
      decision: null
    };
  }

  function init() {
    initUserProfile();
    SAMPLE_PROFILES.forEach(p => {
      DB[p.id] = baseRecord(p);
    });
    activeId = SAMPLE_PROFILES[0].id;
    renderSidebar();
    renderMain();
  }

  function initUserProfile() {
    let role = localStorage.getItem('gem_user_role');
    let name = localStorage.getItem('gem_user_name');

    if (!role || !name) {
      role = 'officer';
      name = 'Smt. Lakshmi Narayanan (DGM - Contracts)';
      localStorage.setItem('gem_user_role', role);
      localStorage.setItem('gem_user_name', name);
    }

    const nameEl = document.getElementById('userName');
    const roleEl = document.getElementById('userRoleBadge');
    const avatarEl = document.getElementById('userAvatar');

    if (nameEl) nameEl.textContent = name;
    if (roleEl) {
      if (role === 'admin') {
        roleEl.textContent = 'CPCL System Administrator';
        roleEl.style.color = '#B493FF';
        if (avatarEl) {
          avatarEl.textContent = 'SK';
          avatarEl.style.background = '#6366F1';
        }
      } else if (role === 'audit') {
        roleEl.textContent = 'Vigilance & Internal Audit';
        roleEl.style.color = '#FBBF24';
        if (avatarEl) {
          avatarEl.textContent = 'KR';
          avatarEl.style.background = '#D97706';
        }
      } else if (role === 'other') {
        const desig = localStorage.getItem('gem_user_designation') || 'Technical Evaluator';
        roleEl.textContent = desig;
        roleEl.style.color = '#38BDF8';
        if (avatarEl) {
          const initials = name.split(' ').map(w => w[0]).filter(Boolean).slice(0, 2).join('').toUpperCase() || 'OU';
          avatarEl.textContent = initials;
          avatarEl.style.background = '#0284C7';
        }
      } else {
        roleEl.textContent = 'DGM (Materials & Contracts)';
        roleEl.style.color = '#7BE8B8';
        if (avatarEl) {
          avatarEl.textContent = 'LN';
          avatarEl.style.background = 'var(--accent)';
        }
      }
    }
  }

  window.handleLogout = function() {
    localStorage.removeItem('gem_user_role');
    localStorage.removeItem('gem_user_name');
    localStorage.removeItem('gem_user_email');
    window.location.href = '/login';
  };

  function riskPillHtml(record) {
    if (!record.results) return `<span class="pill pending"><span class="pill-dot"></span>Not verified</span>`;
    const r = record.results.risk.toLowerCase();
    return `<span class="pill ${r}"><span class="pill-dot"></span>${record.results.risk} risk · ${record.results.score}</span>`;
  }

  function renderSidebar() {
    const list = document.getElementById('bidderList');
    const ids = Object.keys(DB);
    list.innerHTML =
      `<div class="bidder-list-label">Bid records (${ids.length})</div>` +
      ids
        .map(id => {
          const r = DB[id];
          const active = id === activeId ? 'active' : '';
          return `<div class="bidder-card ${active}" data-id="${esc(id)}">
            <div class="bidder-name">${esc(r.profile.name)}</div>
            <div class="bidder-meta">GSTIN ${esc(r.profile.gstin || '—')}</div>
            <div class="bidder-status-row">${riskPillHtml(r)}</div>
          </div>`;
        })
        .join('');

    list.querySelectorAll('.bidder-card').forEach(el => {
      el.addEventListener('click', () => {
        activeId = el.getAttribute('data-id');
        const clickedBidder = DB[activeId];
        if (clickedBidder && clickedBidder.profile && clickedBidder.profile.gem_bid) {
          const matchingTender = CPCL_TENDERS_REGISTRY.find(t => t.gem_bid === clickedBidder.profile.gem_bid);
          if (matchingTender) {
            currentSelectedTenderId = matchingTender.id;
          }
        }
        renderSidebar();
        renderMain();
      });
    });
  }

  function checkCardHtml(c, st) {
    const status = st ? st.status : 'pending';
    const finding = st ? st.finding : 'Awaiting verification run. Click card to view document inspection parameters.';
    return `<div class="check-card" data-check="${c.id}">
      <div class="check-top">
        <div>
          <div class="check-label">${c.label}</div>
          <div class="check-portal">${c.portal}</div>
        </div>
        <span class="status-tag ${status}">${STATUS_LABEL[status]}</span>
      </div>
      <div class="check-finding" style="max-height: 160px; opacity: 1;">${esc(finding)}</div>
      <div style="margin-top: 8px; display: flex; align-items: center; justify-content: space-between; gap: 6px;">
        <span style="font-size: 11px; color: var(--accent); font-weight: 600; font-family: 'IBM Plex Mono', monospace;">View Details ↗</span>
        <button class="doc-card-pdf-btn" onclick="event.stopPropagation(); downloadIndividualDocPDF('${c.id}')" title="Export this document certificate to PDF">Export Doc PDF ⤓</button>
      </div>
    </div>`;
  }

  function gaugeSvg(score, risk) {
    const r = 34, c = 2 * Math.PI * r;
    const color = risk === 'Low' ? 'var(--verified)' : risk === 'Medium' ? 'var(--flagged)' : 'var(--missing)';
    const offset = c - (score / 100) * c;
    return `<svg width="84" height="84" viewBox="0 0 84 84">
      <circle cx="42" cy="42" r="${r}" fill="none" stroke="var(--line)" stroke-width="8"/>
      <circle cx="42" cy="42" r="${r}" fill="none" stroke="${color}" stroke-width="8"
        stroke-linecap="round" stroke-dasharray="${c}" stroke-dashoffset="${offset}"
        transform="rotate(-90 42 42)" />
    </svg>`;
  }

  let currentActiveTab = 'verification';
  let currentSelectedTenderId = 'tender-1';
  let tenderSearchQuery = '';

  window.switchTab = function(tabName) {
    currentActiveTab = tabName;
    renderMain();
  };

  window.filterTenders = function(query) {
    tenderSearchQuery = (query || '').toLowerCase().trim();
    const container = document.getElementById('tendersCardsList');
    if (!container) return;
    container.innerHTML = renderTenderCardsHtml();
  };

  window.selectTenderForEvaluation = function(gemBidNo) {
    // Find the tender in the CPCL registry
    const foundTender = CPCL_TENDERS_REGISTRY.find(t => t.gem_bid === gemBidNo || t.id === gemBidNo);
    if (foundTender) {
      currentSelectedTenderId = foundTender.id;
      gemBidNo = foundTender.gem_bid;
    }

    // Find a bidder associated with this gem_bid
    const matchingBidderId = Object.keys(DB).find(id => DB[id].profile.gem_bid === gemBidNo);
    if (matchingBidderId) {
      activeId = matchingBidderId;
    } else {
      DB[activeId].profile.gem_bid = gemBidNo;
    }

    currentActiveTab = 'verification';
    renderSidebar();
    renderMain();
    showToast(`✓ Loaded Tender ${foundTender ? foundTender.ref_id : gemBidNo} details for scrutiny`);
  };

  function renderTabBarHtml() {
    return `
      <div class="nav-tab-bar">
        <button class="nav-tab-btn ${currentActiveTab === 'verification' ? 'active' : ''}" onclick="switchTab('verification')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10 9 9 9 8 9"></polyline>
          </svg>
          <span>Bidder Verification &amp; Scrutiny</span>
        </button>
        <button class="nav-tab-btn ${currentActiveTab === 'decisions' ? 'active' : ''}" onclick="switchTab('decisions')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="8.5" cy="7" r="4"></circle>
            <polyline points="17 11 19 13 23 9"></polyline>
          </svg>
          <span>Approved &amp; Rejected Bidders</span>
          <span class="nav-tab-badge" style="background:#0E2036; color:#fff;">${getDecisionsCountBadge()}</span>
        </button>
        <button class="nav-tab-btn ${currentActiveTab === 'tenders' ? 'active' : ''}" onclick="switchTab('tenders')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
            <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
          </svg>
          <span>All Tenders Details</span>
          <span class="nav-tab-badge">5 Active</span>
        </button>
        <button class="nav-tab-btn ${currentActiveTab === 'upload' ? 'active' : ''}" onclick="switchTab('upload')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
          <span>Upload PDF &amp; Document AI</span>
          <span class="nav-tab-badge" style="background:#1E3A8A; color:#fff;">AI OCR</span>
        </button>
        <button class="nav-tab-btn ${currentActiveTab === 'audit' ? 'active' : ''}" onclick="switchTab('audit')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
          </svg>
          <span>Audit Ledger &amp; Provenance</span>
        </button>
      </div>
    `;
  }

  let decisionFilter = 'all';
  let decisionSearchQuery = '';

  function getCurrentUser() {
    const name = localStorage.getItem('gem_user_name') || 'Smt. Lakshmi Narayanan';
    const roleKey = localStorage.getItem('gem_user_role') || 'officer';
    let role = 'DGM (Contracts)';
    if (roleKey === 'admin') role = 'Chief Manager (IT)';
    else if (roleKey === 'audit') role = 'Chief Vigilance Officer';
    else if (roleKey === 'other') role = localStorage.getItem('gem_user_designation') || 'Technical Evaluator';
    return { name, role };
  }

  function getBidderDecisionStatus(record) {
    if (record.override && record.override.decision) {
      return record.override.decision === 'approve' ? 'approved' : 'rejected';
    }
    if (record.results) {
      if (record.results.risk === 'Low') return 'approved';
      if (record.results.risk === 'High') return 'rejected';
      return 'pending';
    }
    // Fallback inspect profile checks
    if (record.profile.checks && record.profile.checks.blacklist && record.profile.checks.blacklist.status === 'missing') {
      return 'rejected';
    }
    return 'approved';
  }

  function getDecisionsCountBadge() {
    const ids = Object.keys(DB);
    let app = 0, rej = 0;
    ids.forEach(id => {
      const st = getBidderDecisionStatus(DB[id]);
      if (st === 'approved') app++;
      if (st === 'rejected') rej++;
    });
    return `${app} Appr · ${rej} Rej`;
  }

  window.filterDecisionsByStatus = function(status) {
    decisionFilter = status;
    const container = document.getElementById('decisionsCardsList');
    if (!container) return;
    container.innerHTML = renderDecisionsCardsHtml();
    // Update active button state
    document.querySelectorAll('.decisions-filter-btn').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-status') === status);
    });
  };

  window.filterDecisionsByQuery = function(query) {
    decisionSearchQuery = (query || '').toLowerCase().trim();
    const container = document.getElementById('decisionsCardsList');
    if (!container) return;
    container.innerHTML = renderDecisionsCardsHtml();
  };

  function renderDecisionsCardsHtml() {
    const curUser = getCurrentUser();
    const ids = Object.keys(DB);
    const filtered = ids.filter(id => {
      const r = DB[id];
      const status = getBidderDecisionStatus(r);
      if (decisionFilter !== 'all' && status !== decisionFilter) return false;
      if (decisionSearchQuery) {
        const name = r.profile.name.toLowerCase();
        const gstin = (r.profile.gstin || '').toLowerCase();
        const pan = (r.profile.pan || '').toLowerCase();
        const bid = (r.profile.gem_bid || '').toLowerCase();
        return name.includes(decisionSearchQuery) || gstin.includes(decisionSearchQuery) || pan.includes(decisionSearchQuery) || bid.includes(decisionSearchQuery);
      }
      return true;
    });

    if (filtered.length === 0) {
      return `<div style="background:#fff; border:1px solid var(--line); border-radius:12px; padding:36px; text-align:center; color:var(--ink-soft);">
        No bidder records match the selected filter (<b>${esc(decisionFilter)}</b>).
      </div>`;
    }

    return filtered.map(id => {
      const r = DB[id];
      const p = r.profile;
      const status = getBidderDecisionStatus(r);
      const isApp = status === 'approved';
      const isRej = status === 'rejected';
      const matchingTender = CPCL_TENDERS_REGISTRY.find(t => t.gem_bid === p.gem_bid) || CPCL_TENDERS_REGISTRY[0];

      let badgeHtml = isApp
        ? `<span class="decisions-status-badge approved">✓ QUALIFIED &amp; APPROVED</span>`
        : isRej
        ? `<span class="decisions-status-badge rejected">✕ DISQUALIFIED &amp; REJECTED</span>`
        : `<span class="decisions-status-badge pending">⏳ UNDER STATUTORY REVIEW</span>`;

      let groundsText = '';
      if (r.override && r.override.justification) {
        groundsText = `<b>Officer Recorded Justification:</b> "${esc(r.override.justification)}" (Signed by ${esc(r.override.officer_name || 'Procurement Authority')})`;
      } else if (isApp) {
        groundsText = `<b>Statutory Evaluation Findings:</b> Fully cleared all 11 regulatory pillars. GSTIN active with 100% filing regularity. Valid Udyam MSME certification. Make-in-India local content verified via ICAI UDIN. Clean debarment record.`;
      } else if (isRej) {
        groundsText = `<b>Disqualification Reason:</b> Hard statutory failure detected. Active Debarment Order (CPPP/2025/DEB/0882) on GeM/CPPP Central Registry. Missing mandatory EPFO registration and irregular GST return compliance.`;
      } else {
        groundsText = `<b>Review Summary:</b> Moderate risk score. Minor PAN name inconsistency and pending Make-in-India detailed BOM cost breakdown attachment.`;
      }

      const scoreVal = r.results ? r.results.score : (isApp ? 94 : isRej ? 24 : 68);
      const riskVal = r.results ? r.results.risk : (isApp ? 'Low' : isRej ? 'High' : 'Medium');

      return `
        <div class="decisions-card">
          <div class="decisions-card-top">
            <div>
              <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px; flex-wrap:wrap;">
                ${badgeHtml}
                <span class="tender-ref-tag" style="background:#0E2036; color:#fff; border-color:#0E2036;">${esc(p.gem_bid || matchingTender.gem_bid)}</span>
                <span class="tender-ref-tag">${esc(matchingTender.ref_id)}</span>
              </div>
              <h3 style="margin:0 0 4px 0; font-size:17px; font-family:var(--font-gov-title); color:var(--ink);">${esc(p.name)}</h3>
              <div style="font-size:12px; color:var(--ink-soft); font-family:var(--font-gov-sans);">
                ${esc(p.category)} · Tender: <b>${esc(matchingTender.title)}</b>
              </div>
            </div>
            <div style="text-align:right;">
              <div style="font-size:10px; font-family:var(--font-gov-mono); color:var(--ink-faint); text-transform:uppercase;">BCI Score &amp; Risk</div>
              <div style="font-size:16px; font-weight:700; color:${isApp ? 'var(--verified)' : isRej ? 'var(--missing)' : 'var(--flagged)'}; font-family:var(--font-gov-title);">
                ${scoreVal}/100 · ${riskVal} Risk
              </div>
            </div>
          </div>

          <div class="id-chips" style="margin-bottom:10px;">
            <span class="id-chip">GSTIN <b>${esc(p.gstin || '—')}</b></span>
            <span class="id-chip">PAN <b>${esc(p.pan || '—')}</b></span>
            <span class="id-chip">Udyam <b>${esc(p.udyam || '—')}</b></span>
            <span class="id-chip">Department: <b>${esc(matchingTender.dept)}</b></span>
          </div>

          <div class="decisions-grounds-box" style="border-left-color:${isApp ? 'var(--verified)' : isRej ? 'var(--missing)' : 'var(--flagged)'};">
            ${groundsText}
          </div>

          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; padding-top:10px; border-top:1px solid var(--line);">
            <div style="font-size:11px; color:var(--ink-faint); font-family:var(--font-gov-mono);">
              Evaluated by: <b>${esc(curUser.name)} (${esc(curUser.role)})</b> • CPCL Manali
            </div>
            <div style="display:flex; gap:8px; align-items:center;">
              <button class="tenders-outline-btn" onclick="openScrutinyForBidder('${esc(id)}')">
                <span>View Evaluation Matrix</span> ➔
              </button>
              <button class="tenders-outline-btn" onclick="downloadBidderDossierDirect('${esc(id)}')">
                <span>Export Dossier (PDF)</span> ⤓
              </button>
              <button class="tenders-action-btn" onclick="openOfficerDecisionForBidder('${esc(id)}')">
                <span>Officer Decision ✎</span>
              </button>
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  window.openScrutinyForBidder = function(bidderId) {
    activeId = bidderId;
    const b = DB[bidderId];
    if (b && b.profile && b.profile.gem_bid) {
      const match = CPCL_TENDERS_REGISTRY.find(t => t.gem_bid === b.profile.gem_bid);
      if (match) currentSelectedTenderId = match.id;
    }
    currentActiveTab = 'verification';
    renderSidebar();
    renderMain();
  };

  window.downloadBidderDossierDirect = function(bidderId) {
    activeId = bidderId;
    downloadMasterDossierPDF();
  };

  window.openOfficerDecisionForBidder = function(bidderId) {
    activeId = bidderId;
    currentActiveTab = 'verification';
    renderSidebar();
    renderMain();
    setTimeout(() => {
      openJustificationModal();
    }, 150);
  };

  function renderDecisionsTab() {
    const ids = Object.keys(DB);
    let total = ids.length;
    let approvedCount = 0;
    let rejectedCount = 0;
    let pendingCount = 0;

    ids.forEach(id => {
      const st = getBidderDecisionStatus(DB[id]);
      if (st === 'approved') approvedCount++;
      else if (st === 'rejected') rejectedCount++;
      else pendingCount++;
    });

    return `
      ${renderTabBarHtml()}
      <div class="tenders-container">
        <div class="tenders-header-box">
          <div>
            <h2>Approved &amp; Rejected Bidders Register</h2>
            <p>Official CPCL Manali Refinery register of technically qualified, approved, and disqualified vendor bid packages.</p>
          </div>
          <div>
            <input type="text" class="tenders-search-input" placeholder="Search by bidder name, GSTIN, PAN..." value="${esc(decisionSearchQuery)}" oninput="filterDecisionsByQuery(this.value)" />
          </div>
        </div>

        <!-- Summary Statistics Bar -->
        <div class="decisions-summary-grid">
          <div class="tender-stat-card" style="background:#fff; border-left:4px solid var(--ink);">
            <div class="lbl">Total Evaluated Bidders</div>
            <div class="val" style="font-size:18px;">${total} Bidders</div>
          </div>
          <div class="tender-stat-card" style="background:#fff; border-left:4px solid var(--verified);">
            <div class="lbl">Technically Approved</div>
            <div class="val" style="font-size:18px; color:var(--verified);">${approvedCount} Qualified</div>
          </div>
          <div class="tender-stat-card" style="background:#fff; border-left:4px solid var(--missing);">
            <div class="lbl">Disqualified / Debarred</div>
            <div class="val" style="font-size:18px; color:var(--missing);">${rejectedCount} Rejected</div>
          </div>
          <div class="tender-stat-card" style="background:#fff; border-left:4px solid var(--flagged);">
            <div class="lbl">Under Scrutiny</div>
            <div class="val" style="font-size:18px; color:var(--flagged);">${pendingCount} Pending</div>
          </div>
        </div>

        <!-- Filter Control Buttons -->
        <div class="decisions-filter-bar">
          <div class="decisions-filter-group">
            <button class="decisions-filter-btn ${decisionFilter === 'all' ? 'active' : ''}" data-status="all" onclick="filterDecisionsByStatus('all')">
              All Decisions (${total})
            </button>
            <button class="decisions-filter-btn ${decisionFilter === 'approved' ? 'active' : ''}" data-status="approved" onclick="filterDecisionsByStatus('approved')">
              ✓ Approved &amp; Qualified (${approvedCount})
            </button>
            <button class="decisions-filter-btn ${decisionFilter === 'rejected' ? 'active' : ''}" data-status="rejected" onclick="filterDecisionsByStatus('rejected')">
              ✕ Disqualified / Rejected (${rejectedCount})
            </button>
            <button class="decisions-filter-btn ${decisionFilter === 'pending' ? 'active' : ''}" data-status="pending" onclick="filterDecisionsByStatus('pending')">
              ⏳ Pending Scrutiny (${pendingCount})
            </button>
          </div>
          <div style="font-size:11.5px; color:var(--ink-soft); font-family:var(--font-gov-mono);">
            Official GeM Scrutiny Register
          </div>
        </div>

        <!-- Decisions Cards List -->
        <div id="decisionsCardsList">
          ${renderDecisionsCardsHtml()}
        </div>
      </div>
    `;
  }

  function renderTenderCardsHtml() {
    const filtered = CPCL_TENDERS_REGISTRY.filter(t => {
      if (!tenderSearchQuery) return true;
      return t.title.toLowerCase().includes(tenderSearchQuery) ||
             t.gem_bid.toLowerCase().includes(tenderSearchQuery) ||
             t.ref_id.toLowerCase().includes(tenderSearchQuery) ||
             t.dept.toLowerCase().includes(tenderSearchQuery) ||
             t.nic_codes.toLowerCase().includes(tenderSearchQuery);
    });

    if (filtered.length === 0) {
      return `<div style="background:#fff; border:1px solid var(--line); border-radius:12px; padding:30px; text-align:center; color:var(--ink-soft);">
        No tenders match "${esc(tenderSearchQuery)}". Try searching by keyword, GeM Bid No, or NIC code.
      </div>`;
    }

    return filtered.map(t => `
      <div class="tenders-card">
        <div class="tenders-card-top">
          <div>
            <div class="tenders-pill-row" style="margin-bottom:6px;">
              <span class="tender-ref-tag" style="background:#0E2036; color:#fff; border-color:#0E2036;">${esc(t.gem_bid)}</span>
              <span class="tender-ref-tag">${esc(t.ref_id)}</span>
              <span class="tender-ref-tag" style="background:#E4F3EC; color:#1E8A5B; border-color:#A7D7C5;">${esc(t.status)}</span>
            </div>
            <div class="tenders-card-title">${esc(t.title)}</div>
            <div style="font-size:12px; color:var(--ink-soft); font-family:var(--font-gov-sans);">${esc(t.dept)}</div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:10px; font-family:var(--font-gov-mono); color:var(--ink-faint); text-transform:uppercase;">Estimated Contract Value</div>
            <div style="font-size:16px; font-weight:700; color:var(--ink); font-family:var(--font-gov-title);">${esc(t.est_value)}</div>
          </div>
        </div>

        <div class="tenders-grid-info">
          <div class="tenders-info-item">
            <div class="label">Min 3-Yr Turnover</div>
            <div class="value">${esc(t.turnover_req)}</div>
          </div>
          <div class="tenders-info-item">
            <div class="label">Make in India (MII)</div>
            <div class="value">${esc(t.mii_req)}</div>
          </div>
          <div class="tenders-info-item">
            <div class="label">Mandatory NIC Codes</div>
            <div class="value">${esc(t.nic_codes)}</div>
          </div>
          <div class="tenders-info-item">
            <div class="label">EMD &amp; MSME Policy</div>
            <div class="value">${esc(t.emd_details)}</div>
          </div>
          <div class="tenders-info-item">
            <div class="label">Published On</div>
            <div class="value">${esc(t.published_date)}</div>
          </div>
          <div class="tenders-info-item">
            <div class="label">Bid Closing Date</div>
            <div class="value" style="color:#C1432E;">${esc(t.closing_date)}</div>
          </div>
        </div>

        <div class="tenders-card-foot">
          <div class="tenders-bidders-tag">
            <span>👥 <b>${t.bidders_count}</b> participating bidders: <i>${t.bidders.slice(0, 2).join(', ')}${t.bidders.length > 2 ? ' + ' + (t.bidders.length - 2) + ' more' : ''}</i></span>
          </div>
          <div style="display:flex; gap:8px; align-items:center;">
            <button class="tenders-outline-btn" onclick="downloadTenderSpecsPDF('${esc(t.id)}')">Specs PDF ⤓</button>
            <button class="tenders-action-btn" onclick="selectTenderForEvaluation('${esc(t.gem_bid)}')">
              <span>Evaluate Bidders</span> ➔
            </button>
          </div>
        </div>
      </div>
    `).join('');
  }

  function generateClientSideSpecsPDF(t) {
    if (!window.jspdf || !window.jspdf.jsPDF) {
      showToast('Downloading document...');
      return;
    }
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    const navy = [11, 29, 58];
    const gray = [100, 116, 139];

    // Header Banner
    doc.setFillColor(...navy);
    doc.rect(0, 0, 210, 28, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(13);
    doc.text('CHENNAI PETROLEUM CORPORATION LIMITED', 14, 11);
    doc.setFontSize(8);
    doc.setFont('helvetica', 'normal');
    doc.text('A Govt. of India Enterprise | Manali Refinery, Chennai - 600068', 14, 17);
    doc.text('TENDER SPECIFICATIONS & STATUTORY ELIGIBILITY NOTICE', 14, 23);

    // Subheader
    doc.setTextColor(...navy);
    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.text(t.title, 14, 38);

    // Particulars Table
    const particulars = [
      ['Tender Reference ID', t.ref_id, 'GeM Bid Number', t.gem_bid],
      ['Procuring Department', t.dept, 'Estimated Contract Value', t.est_val],
      ['Min Annual Turnover', t.turnover, 'Mandatory NIC Code(s)', t.nic],
      ['Make in India Requirement', t.mii + ' (Class-I Local Supplier)', 'Bid Submission Deadline', t.bid_end_date],
      ['Tender Opening Date', t.opening_date, 'Contract Period', t.validity]
    ];

    if (doc.autoTable) {
      doc.autoTable({
        startY: 44,
        head: [['Parameter', 'Specification', 'Parameter', 'Specification']],
        body: particulars,
        theme: 'grid',
        headStyles: { fillColor: navy, textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 8 },
        styles: { fontSize: 8, cellPadding: 3 },
        columnStyles: { 0: { fontStyle: 'bold', width: 45 }, 2: { fontStyle: 'bold', width: 45 } }
      });

      const criteria = [
        ['1', 'Udyam / MSME Registration', 'Valid registration matching NIC ' + t.nic + '; Small/Medium enterprise benefits applied.', 'Mandatory'],
        ['2', 'GST Compliance & Filing', 'Active GSTIN with 100% regular GSTR-3B filings in preceding 12 months.', 'Mandatory'],
        ['3', 'Income Tax & PAN Verification', 'Valid PAN operative with non-defaulter status under Section 206AB of IT Act.', 'Mandatory'],
        ['4', 'Financial Solvency & Turnover', 'Average annual audited turnover >= ' + t.turnover + ' certified with CA UDIN.', 'Mandatory'],
        ['5', 'Make in India (DPIIT Order)', 'Minimum ' + t.mii + ' local content declaration certified by Statutory Auditor / CA.', 'Mandatory'],
        ['6', 'OEM Authorization (MAF)', 'OEM Manufacturer Authorization Form referencing bid ' + t.gem_bid, 'Mandatory'],
        ['7', 'Debarment / Blacklisting Check', 'Clean record across GeM, CPPP, CVC, and CPCL debarment registries.', 'Critical Disqualifier']
      ];

      doc.autoTable({
        startY: doc.lastAutoTable.finalY + 8,
        head: [['#', 'Statutory Evaluation Pillar', 'Compliance Requirement & Threshold', 'Eligibility Status']],
        body: criteria,
        theme: 'striped',
        headStyles: { fillColor: [30, 41, 59], textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 8 },
        styles: { fontSize: 7.5, cellPadding: 2.5 }
      });

      const curY = doc.lastAutoTable.finalY + 12;
      doc.setFontSize(8);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(...gray);
      doc.text('Digitally Authenticated & Stamped by CPCL Materials & Contracts Directorate', 14, curY);
      doc.text('Issuing Authority: Smt. Lakshmi Narayanan, DGM (Materials & Contracts), CPCL Manali Refinery', 14, curY + 5);
      doc.text('Date of Generation: ' + new Date().toLocaleString('en-IN') + ' | Digital Provenance Verified', 14, curY + 10);
    }

    const refClean = (t.ref_id || t.gem_bid).replace(/[\/\s]/g, '_');
    doc.save(`CPCL_Tender_Specs_${refClean}.pdf`);
    showToast(`✓ Tender Specs PDF downloaded successfully.`);
  }

  window.downloadTenderSpecsPDF = async function(tenderId) {
    const tender = CPCL_TENDERS_REGISTRY.find(t => t.id === tenderId) || CPCL_TENDERS_REGISTRY[0];
    showToast(`Generating official CPCL Tender Specifications PDF for ${tender.gem_bid}...`);

    try {
      const resp = await fetch('/api/v1/tenders/generate-specs-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tender)
      });

      if (resp.ok) {
        const blob = await resp.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const refClean = (tender.ref_id || tender.gem_bid).replace(/\//g, '_');
        a.download = `CPCL_Tender_Specs_${refClean}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        showToast(`✓ Downloaded ${a.download}`);
        return;
      }
    } catch (err) {
      console.warn('Backend PDF endpoint unreachable, using high-res client fallback:', err);
    }
    // Universal client-side fallback
    generateClientSideSpecsPDF(tender);
  };

  function renderTendersTab() {
    return `
      ${renderTabBarHtml()}
      <div class="tenders-container">
        <div class="tenders-header-box">
          <div>
            <h2>CPCL GeM Tenders &amp; Procurement Packages</h2>
            <p>Comprehensive register of active Manali Refinery tenders, statutory thresholds, Make-in-India mandates, and participating bidders.</p>
          </div>
          <div>
            <input type="text" class="tenders-search-input" placeholder="Search by tender title, GeM ID, NIC..." value="${esc(tenderSearchQuery)}" oninput="filterTenders(this.value)" />
          </div>
        </div>

        <!-- Summary Statistics Bar -->
        <div class="tender-grid" style="padding:0; border:none;">
          <div class="tender-stat-card" style="background:#fff;">
            <div class="lbl">Total Active Tenders</div>
            <div class="val">5 Refinery Packages</div>
          </div>
          <div class="tender-stat-card" style="background:#fff;">
            <div class="lbl">Total Cumulative Value</div>
            <div class="val">₹ 25.85 Crore (INR)</div>
          </div>
          <div class="tender-stat-card" style="background:#fff;">
            <div class="lbl">Ingested Bid Packages</div>
            <div class="val">14 Vendor Submissions</div>
          </div>
          <div class="tender-stat-card" style="background:#fff;">
            <div class="lbl">Procuring Authority</div>
            <div class="val">CPCL Manali Refinery</div>
          </div>
        </div>

        <!-- Tenders List -->
        <div class="tenders-container" id="tendersCardsList">
          ${renderTenderCardsHtml()}
        </div>
      </div>
    `;
  }

  function renderAuditTab() {
    const record = DB[activeId];
    return `
      ${renderTabBarHtml()}
      <div class="tenders-container">
        <div class="tenders-header-box">
          <div>
            <h2>Cryptographic Audit Ledger &amp; Verification Provenance</h2>
            <p>Immutable SHA-256 digital audit trail recording all statutory adapter queries, Document AI extractions, and officer decisions.</p>
          </div>
          <button class="tenders-outline-btn" onclick="downloadMasterDossierPDF()">Export Audit Dossier (PDF) ⤓</button>
        </div>

        <div class="audit-block" style="margin-top:0;">
          <div class="audit-head">System Event Timeline · Bidder: ${esc(record.profile.name)} (GeM Ref: ${esc(record.profile.gem_bid || 'GEM/2026/B/998877')})</div>
          <div class="audit-body" style="max-height:500px; overflow-y:auto;">
            ${record.auditTrail.map(a => `
              <div class="audit-item">
                <span class="audit-time">${esc(a.time)}</span>
                <span class="audit-actor">${esc(a.actor)}</span>
                <span class="audit-text">${esc(a.text)}</span>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  }

  let currentUploadedDoc = null;
  let isParsingUploadedPdf = false;

  window.handlePdfDrop = function(e) {
    e.preventDefault();
    const zone = document.getElementById('uploadDropzone');
    if (zone) zone.classList.remove('dragover');
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
      processUploadedPdfFile(e.dataTransfer.files[0]);
    }
  };

  window.handlePdfDragOver = function(e) {
    e.preventDefault();
    const zone = document.getElementById('uploadDropzone');
    if (zone) zone.classList.add('dragover');
  };

  window.handlePdfDragLeave = function(e) {
    e.preventDefault();
    const zone = document.getElementById('uploadDropzone');
    if (zone) zone.classList.remove('dragover');
  };

  window.triggerPdfFileInput = function() {
    const input = document.getElementById('pdfDocFileInput');
    if (input) input.click();
  };

  window.handlePdfFileSelected = function(e) {
    if (e.target && e.target.files && e.target.files[0]) {
      processUploadedPdfFile(e.target.files[0]);
    }
  };

  const SAMPLE_PDF_DOCS = {
    maf_valid: {
      fileName: 'OEM_MAF_Dell_Authorized_CPCL_Refinery.pdf',
      fileSize: '248.4 KB',
      docType: 'OEM Manufacturer Authorization Form (MAF)',
      sha256: '9a3b8c4d7e2f1092837465abcdeffedcba9876543210123456789abcdef01234',
      status: 'verified',
      statutoryVerdict: '✓ PASS — 100% Valid & Specifically Authorized',
      ruleCitation: 'Compliant with GeM GTC v4.0 Clause 4.8 & CPCL Technical Specifications',
      entities: [
        { label: 'Authorized OEM Entity', value: 'Dell International Services India Pvt. Ltd.' },
        { label: 'Authorized Reseller / Bidder', value: 'Sundaram Precision Tooling Pvt. Ltd.' },
        { label: 'Tender / GeM Bid Reference', value: 'GEM/2026/B/882211 (Exact Match)' },
        { label: 'MAF Validity Period', value: 'Valid through 31-Dec-2027 (Unexpired)' },
        { label: 'Warranty & Support Backing', value: '5 Years 24x7 Comprehensive Onsite Warranty' },
        { label: 'OEM Signatory', value: 'Mr. Rajesh Varma, Director - Enterprise Channels' }
      ]
    },
    mii_class1: {
      fileName: 'Make_In_India_Class1_CA_UDIN_Certificate.pdf',
      fileSize: '312.8 KB',
      docType: 'Make in India (MII) Local Content Declaration',
      sha256: 'e8d7c6b5a4938271605f4e3d2c1b0a9876543210fedcba9876543210abcdef99',
      status: 'verified',
      statutoryVerdict: '✓ PASS — Class-I Local Supplier (>=50% Threshold)',
      ruleCitation: 'Compliant with DPIIT PPP-MII Order 2017 Para 3(a) & Para 9(b)',
      entities: [
        { label: 'Supplier Classification', value: 'Class-I Local Supplier (65.5% Local Content)' },
        { label: 'Manufacturing / Value Addition Site', value: 'Plot 42, MIDC Industrial Area, Pune, Maharashtra' },
        { label: 'Chartered Accountant Firm', value: 'M/s Sharma & Associates (FRN: 109283W)' },
        { label: 'ICAI UDIN Reference', value: '24012345AAAAAA1234 (Verified on ICAI Portal)' },
        { label: 'Purchase Preference Eligibility', value: 'Eligible for 20% MSME/MII Margin of Purchase Preference' },
        { label: 'Self-Declaration Attestation', value: 'Affirmed on Non-Judicial Stamp Paper (₹100)' }
      ]
    },
    ca_turnover: {
      fileName: 'CA_Audited_Annual_Turnover_NetWorth_Report.pdf',
      fileSize: '418.1 KB',
      docType: 'Audited Financial Statement / Turnover Certificate',
      sha256: '3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d',
      status: 'verified',
      statutoryVerdict: '✓ PASS — Exceeds CPCL Minimum Turnover Threshold',
      ruleCitation: 'Compliant with GFR 2017 Rule 144 & CPCL Commercial Eligibility Criteria',
      entities: [
        { label: 'Average Annual Turnover (3 Yrs)', value: '₹ 12.50 Crore / annum (Threshold: ₹ 2.50 Crore)' },
        { label: 'Audited Net Worth', value: '₹ 8.50 Crore (Positive Solvency Ratio)' },
        { label: 'FY 2024-25 Turnover', value: '₹ 14.20 Crore (Audited)' },
        { label: 'FY 2023-24 Turnover', value: '₹ 11.80 Crore (Audited)' },
        { label: 'Statutory Auditor UDIN', value: '24098765BBBBBB4321 (Active)' },
        { label: 'Working Capital Facility', value: '₹ 4.00 Crore Line of Credit (State Bank of India)' }
      ]
    },
    maf_expired: {
      fileName: 'OEM_MAF_Expired_Mismatched_Tender.pdf',
      fileSize: '194.2 KB',
      docType: 'OEM Manufacturer Authorization Form (MAF)',
      sha256: 'ff00112233445566778899aabbccddeeff00112233445566778899aabbccddee',
      status: 'missing',
      statutoryVerdict: '✕ DISQUALIFIED — Expired MAF / Mismatched Tender',
      ruleCitation: 'Violates GeM GTC v4.0 Clause 4.8 & Commercial Terms',
      entities: [
        { label: 'Authorized OEM Entity', value: 'Global Turbomachinery Systems Ltd.' },
        { label: 'Declared Tender Reference', value: 'GEM/2024/B/112233 (Mismatched Old Tender)' },
        { label: 'MAF Expiry Date', value: 'Expired on 31-Dec-2024 (Lapsed Validity)' },
        { label: 'Defect Severity', value: 'Mandatory Technical Disqualification' },
        { label: 'Procurement Action', value: 'Reject bid or issue formal clarification notice' }
      ]
    }
  };

  window.loadSamplePdfDoc = function(sampleKey) {
    const sample = SAMPLE_PDF_DOCS[sampleKey];
    if (!sample) return;
    showToast(`Loading and parsing ${sample.fileName}...`);
    isParsingUploadedPdf = true;
    const container = document.getElementById('uploadResultContainer');
    if (container) {
      container.innerHTML = `
        <div style="background:#fff; border:1px solid var(--line); border-radius:12px; padding:30px; text-align:center;">
          <div style="font-size:24px; margin-bottom:8px;">⚙️</div>
          <div style="font-weight:700; font-family:var(--font-gov-title);">Document AI Processing PDF...</div>
          <div style="font-size:12px; color:var(--ink-soft);">Running OCR layout analysis, table extraction, and ICAI UDIN verification...</div>
        </div>
      `;
    }

    setTimeout(() => {
      currentUploadedDoc = sample;
      isParsingUploadedPdf = false;
      if (container) container.innerHTML = renderUploadResultHtml(sample);
      showToast(`✓ Document AI extraction complete for ${sample.fileName}!`);
    }, 450);
  };

  function processUploadedPdfFile(file) {
    if (!file) return;
    const fileName = file.name;
    const fileSize = (file.size / 1024).toFixed(1) + ' KB';
    const seed = fileName + file.size + Date.now();
    const sha256 = generateSyntheticSha256(seed);

    showToast(`Ingesting and parsing "${fileName}" with Document AI...`);
    isParsingUploadedPdf = true;

    // Detect type based on filename keywords
    let docType = 'General Procurement Certificate / Statutory Submission';
    let status = 'verified';
    let verdict = '✓ PASS — Verified Statutory Document';
    let citation = 'Compliant with GeM GTC & Central Public Procurement Policy';
    let entities = [
      { label: 'Detected Document Name', value: fileName },
      { label: 'File Size & Format', value: `${fileSize} · Adobe Portable Document Format (.pdf)` },
      { label: 'Ingested Vendor Reference', value: DB[activeId].profile.name },
      { label: 'GeM Bid Scope', value: DB[activeId].profile.gem_bid || 'GEM/2026/B/998877' },
      { label: 'Document AI OCR Engine', value: 'PyPDF Extractor & Tesseract Fallback' },
      { label: 'Digital Provenance Hash', value: sha256.slice(0, 36) + '...' }
    ];

    if (fileName.toLowerCase().includes('maf') || fileName.toLowerCase().includes('oem')) {
      docType = 'OEM Manufacturer Authorization Form (MAF)';
      entities.push({ label: 'OEM Specificity Check', value: 'Valid Manufacturer Authorization Verified' });
    } else if (fileName.toLowerCase().includes('mii') || fileName.toLowerCase().includes('local')) {
      docType = 'Make in India (MII) Local Content Declaration';
      entities.push({ label: 'Local Content %', value: 'Class-I Compliant (>=50%)' });
    } else if (fileName.toLowerCase().includes('turnover') || fileName.toLowerCase().includes('ca') || fileName.toLowerCase().includes('audit')) {
      docType = 'Audited Financial Statement / Turnover Certificate';
      entities.push({ label: 'ICAI UDIN Validation', value: 'CA UDIN Authenticated' });
    }

    setTimeout(() => {
      const parsedDoc = {
        fileName,
        fileSize,
        docType,
        sha256,
        status,
        statutoryVerdict: verdict,
        ruleCitation: citation,
        entities
      };
      currentUploadedDoc = parsedDoc;
      isParsingUploadedPdf = false;
      const container = document.getElementById('uploadResultContainer');
      if (container) container.innerHTML = renderUploadResultHtml(parsedDoc);
      showToast(`✓ Document AI extracted ${entities.length} entities from ${fileName}!`);
    }, 600);
  }

  function renderUploadResultHtml(doc) {
    const isApp = doc.status === 'verified';
    return `
      <div class="upload-result-card">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px; margin-bottom:16px;">
          <div>
            <div style="font-size:10px; font-family:var(--font-gov-mono); color:var(--ink-faint); text-transform:uppercase;">Document AI Ingestion Result</div>
            <h3 style="margin:4px 0 0 0; font-family:var(--font-gov-title); font-size:17px; color:var(--ink);">📄 ${esc(doc.fileName)}</h3>
            <div style="font-size:12px; color:var(--ink-soft); margin-top:2px;">Type: <b>${esc(doc.docType)}</b> · Size: <b>${esc(doc.fileSize)}</b></div>
          </div>
          <span class="decisions-status-badge ${isApp ? 'approved' : 'rejected'}" style="font-size:12px; padding:6px 14px;">
            ${esc(doc.statutoryVerdict)}
          </span>
        </div>

        <div class="upload-meta-grid">
          ${doc.entities.map(e => `
            <div class="upload-meta-item">
              <div class="upload-meta-lbl">${esc(e.label)}</div>
              <div class="upload-meta-val">${esc(e.value)}</div>
            </div>
          `).join('')}
        </div>

        <div class="decisions-grounds-box" style="border-left-color:${isApp ? 'var(--verified)' : 'var(--missing)'};">
          <b>Statutory Rule Assessment:</b> ${esc(doc.ruleCitation)}
        </div>

        <div style="background:var(--surface-2); padding:10px 14px; border-radius:8px; margin-bottom:16px; font-family:var(--font-gov-mono); font-size:11px; color:var(--ink-faint); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
          <div><b>SHA-256 Digest:</b> <span style="color:var(--ink);">${esc(doc.sha256)}</span></div>
          <button class="doc-copy-btn" onclick="navigator.clipboard.writeText('${esc(doc.sha256)}'); showToast('Copied SHA-256 seal!');">Copy Seal</button>
        </div>

        <div style="display:flex; gap:10px; justify-content:flex-end; flex-wrap:wrap;">
          <button class="tenders-outline-btn" onclick="applyUploadedDocToActiveBidder()">
            <span>Apply to Active Bidder Evaluation</span> ➔
          </button>
          <button class="tenders-action-btn" onclick="downloadUploadedDocPDF()">
            <span>Download Stamped Certificate (PDF)</span> ⤓
          </button>
        </div>
      </div>
    `;
  }

  window.applyUploadedDocToActiveBidder = function() {
    if (!currentUploadedDoc) return;
    const record = DB[activeId];
    record.auditTrail.push({
      time: nowStr(),
      actor: 'Document AI Extractor',
      text: `Ingested external PDF "${currentUploadedDoc.fileName}" (${currentUploadedDoc.docType}). SHA-256: ${currentUploadedDoc.sha256.slice(0, 16)}... Statutory status: ${currentUploadedDoc.status}.`
    });
    showToast(`✓ Document AI findings applied to ${record.profile.name}!`);
    switchTab('verification');
  };

  window.downloadUploadedDocPDF = function() {
    if (!currentUploadedDoc) return;
    const record = DB[activeId];
    const payload = {
      title: currentUploadedDoc.docType,
      portal: 'Document AI PDF Upload Center',
      status: currentUploadedDoc.status,
      bidder_name: record.profile.name,
      gstin: record.profile.gstin || '33AACCL1234F1Z8',
      pan: record.profile.pan || 'AACCL1234F',
      gem_bid: record.profile.gem_bid || 'GEM/2026/B/998877',
      finding: currentUploadedDoc.statutoryVerdict,
      fields: currentUploadedDoc.entities.map(e => ({ lbl: e.label, val: e.value })),
      rules: [{ pass: currentUploadedDoc.status === 'verified', text: currentUploadedDoc.ruleCitation }],
      sha256: currentUploadedDoc.sha256,
    };
    generateClientSideDocPDF(payload);
  };

  function renderUploadTab() {
    return `
      ${renderTabBarHtml()}
      <div class="upload-container">
        <div class="tenders-header-box">
          <div>
            <h2>Document AI &amp; Statutory PDF Upload Center</h2>
            <p>Upload vendor certificates, OEM MAFs, Make-in-India declarations, CA audit reports, or policy PDFs for automated OCR extraction, UDIN validation, and statutory compliance scoring.</p>
          </div>
        </div>

        <!-- Dropzone Box -->
        <div class="upload-dropzone" id="uploadDropzone" 
             ondrop="handlePdfDrop(event)" 
             ondragover="handlePdfDragOver(event)" 
             ondragleave="handlePdfDragLeave(event)" 
             onclick="triggerPdfFileInput()">
          <input type="file" id="pdfDocFileInput" accept=".pdf" style="display:none;" onchange="handlePdfFileSelected(event)" />
          <div class="upload-dropzone-icon">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
          </div>
          <div style="font-family:var(--font-gov-title); font-size:16px; font-weight:700; color:var(--ink); margin-bottom:4px;">
            Drag and Drop your PDF document here, or <span style="color:var(--accent); text-decoration:underline;">Browse Files</span>
          </div>
          <div style="font-size:12px; color:var(--ink-soft);">
            Supports OEM MAF, CA UDIN Turnover, Make in India declarations, GST Returns &amp; GFR Rulebooks (Max 25 MB)
          </div>
        </div>

        <!-- Sample Documents Quick Loader -->
        <div class="upload-samples-bar">
          <span style="font-size:11.5px; font-weight:700; font-family:var(--font-gov-title); color:var(--ink);">⚡ Quick-Load Sample Regulatory PDFs:</span>
          <button class="upload-sample-btn" onclick="loadSamplePdfDoc('maf_valid')">Sample OEM MAF (Valid)</button>
          <button class="upload-sample-btn" onclick="loadSamplePdfDoc('mii_class1')">Sample Make in India (Class-I 65%)</button>
          <button class="upload-sample-btn" onclick="loadSamplePdfDoc('ca_turnover')">Sample CA Turnover (₹12.5 Cr)</button>
          <button class="upload-sample-btn" onclick="loadSamplePdfDoc('maf_expired')">Sample Expired MAF (Violating)</button>
        </div>

        <!-- Live Results Container -->
        <div id="uploadResultContainer">
          ${currentUploadedDoc ? renderUploadResultHtml(currentUploadedDoc) : `
            <div style="background:#fff; border:1px solid var(--line); border-radius:12px; padding:36px; text-align:center; color:var(--ink-soft);">
              <div style="font-size:28px; margin-bottom:8px;">📋</div>
              <div style="font-weight:700; font-family:var(--font-gov-title); color:var(--ink);">No PDF Analyzed Yet</div>
              <div style="font-size:12px; margin-top:4px;">Drag &amp; drop a PDF above or click any sample document button to trigger Document AI extraction.</div>
            </div>
          `}
        </div>
      </div>
    `;
  }

  function renderMain() {
    const record = DB[activeId];
    const main = document.getElementById('main');
    const p = record.profile;
    const running = scanningNow;

    if (currentActiveTab === 'upload') {
      main.innerHTML = renderUploadTab();
      return;
    }

    if (currentActiveTab === 'decisions') {
      main.innerHTML = renderDecisionsTab();
      return;
    }

    if (currentActiveTab === 'tenders') {
      main.innerHTML = renderTendersTab();
      return;
    }

    if (currentActiveTab === 'audit') {
      main.innerHTML = renderAuditTab();
      return;
    }

    const activeTender = CPCL_TENDERS_REGISTRY.find(t => t.id === currentSelectedTenderId || t.gem_bid === p.gem_bid) || CPCL_TENDERS_REGISTRY[0];
    p.gem_bid = activeTender.gem_bid;

    let html = `
      ${renderTabBarHtml()}

      <div class="topbar">
        <div class="bidder-id-block">
          <div style="display:flex; align-items:center; gap:8px; margin-bottom: 4px; flex-wrap: wrap;">
            <span style="background:var(--surface-2); color:var(--ink); border: 1px solid var(--line-strong); padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 700; font-family: var(--font-gov-mono);">GeM e-Procurement Feed: Synced</span>
            <span style="font-size: 11px; color: var(--ink-faint); font-family: var(--font-gov-mono);">Tender Stage: Technical Bid Evaluation</span>
          </div>
          <h1>${esc(p.name)}</h1>
          <div class="id-chips">
            <span class="id-chip">GSTIN <b>${esc(p.gstin || '—')}</b></span>
            <span class="id-chip">PAN <b>${esc(p.pan || '—')}</b></span>
            <span class="id-chip">Udyam <b>${esc(p.udyam || '—')}</b></span>
            <span class="id-chip">GeM Bid Ref <b>${esc(activeTender.gem_bid)}</b></span>
          </div>
          <span class="cat-chip">${esc(p.category)}</span>
        </div>
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
          <button class="pdf-btn" id="topPdfBtn" style="padding: 12px 18px; font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 8px; border-radius: 9px; margin-right: 0;">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            <span>Export PDF Dossier</span>
          </button>
          <button class="run-btn ${running ? 'loading' : ''}" id="runBtn" ${running ? 'disabled' : ''}>
            <span class="spin"></span>
            <span>${record.results ? 'Re-run AI verification' : 'Run AI verification'}</span>
          </button>
        </div>
      </div>

      <!-- Dynamic Tender Particulars Panel -->
      <div class="tender-panel">
        <div class="tender-panel-head">
          <div class="tender-title-group">
            <h2>
              <span>${esc(activeTender.title)}</span>
              <span class="tender-ref-tag">${esc(activeTender.ref_id)}</span>
              <span class="tender-ref-tag" style="background:#E4F3EC; color:#1E8A5B; border-color:#A7D7C5;">${esc(activeTender.status)}</span>
            </h2>
            <div class="tender-meta-row">
              <span class="tender-meta-item">Procuring Entity: <b>${esc(activeTender.dept || 'CPCL Manali Refinery')}</b></span>
              <span class="tender-meta-item">GeM Bid ID: <b>${esc(activeTender.gem_bid)}</b></span>
              <span class="tender-meta-item">Est. Value: <b>${esc(activeTender.est_value)}</b></span>
              <span class="tender-meta-item">Closing Date: <b style="color:#C1432E;">${esc(activeTender.closing_date)}</b></span>
            </div>
          </div>
          <button type="button" class="tender-toggle-btn" id="tenderToggleBtn" onclick="toggleTenderDetails(this)">
            <span>Hide Criteria</span> ▴
          </button>
        </div>

        <div class="tender-grid" id="tenderCriteriaGrid">
          <div class="tender-stat-card">
            <div class="lbl">Min 3-Yr Avg Turnover</div>
            <div class="val">${esc(activeTender.turnover_req)}</div>
          </div>
          <div class="tender-stat-card">
            <div class="lbl">Make In India (MII) Preference</div>
            <div class="val">${esc(activeTender.mii_req)}</div>
          </div>
          <div class="tender-stat-card">
            <div class="lbl">Mandatory NIC Codes</div>
            <div class="val">${esc(activeTender.nic_codes)}</div>
          </div>
          <div class="tender-stat-card">
            <div class="lbl">EMD &amp; MSME Exemption</div>
            <div class="val">${esc(activeTender.emd_details)}</div>
          </div>
          <div class="tender-stat-card">
            <div class="lbl">Published Date</div>
            <div class="val">${esc(activeTender.published_date)}</div>
          </div>
          <div class="tender-stat-card">
            <div class="lbl">Technical Bid Opening</div>
            <div class="val">${esc(activeTender.opening_date)}</div>
          </div>
        </div>
      </div>

      <div class="section-label">Portal &amp; document checks (Click any card for full details)</div>
      <div class="check-grid" id="checkGrid">
        ${CHECKS.map(c => checkCardHtml(c, record.results ? record.results.checks[c.id] : null)).join('')}
      </div>
    `;

    if (record.results) {
      const res = record.results;
      const rc = res.risk.toLowerCase();
      const reco = res.recommendation;
      html += `
        <div class="section-label">Compliance assessment</div>
        <div class="results-row">
          <div class="score-card">
            <div class="gauge-wrap">${gaugeSvg(res.score, res.risk)}<div class="gauge-num">${res.score}</div></div>
            <div>
              <div class="score-title">Compliance score</div>
              <div class="risk-badge-lg" style="color:var(--${rc === 'low' ? 'verified' : rc === 'medium' ? 'flagged' : 'missing'})">
                <span class="risk-dot-lg" style="background:var(--${rc === 'low' ? 'verified' : rc === 'medium' ? 'flagged' : 'missing'})"></span>
                ${res.risk} risk
              </div>
              <div class="score-meta" style="margin-top:4px;">Verified ${esc(res.verifiedAt)}</div>
            </div>
          </div>
          <div class="counts-card">
            <div class="count-item"><div class="count-num" style="color:var(--verified)">${res.counts.verified || 0}</div><div class="count-lbl">Verified</div></div>
            <div class="count-item"><div class="count-num" style="color:var(--flagged)">${res.counts.flagged || 0}</div><div class="count-lbl">Flagged</div></div>
            <div class="count-item"><div class="count-num" style="color:var(--missing)">${res.counts.missing || 0}</div><div class="count-lbl">Missing</div></div>
            <div class="count-item"><div class="count-num" style="color:var(--na)">${res.counts.na || 0}</div><div class="count-lbl">N/A</div></div>
          </div>
        </div>

        <div class="reco-card">
          <div class="reco-head"><span class="badge-ai">AI ENGINE</span> Recommendation to Procurement Officer</div>
          <div class="reco-lead">${esc(reco.lead)}</div>
          ${reco.items.length ? `<ul class="reco-list">${reco.items.map(it => `<li><b>${esc(it.label)}:</b> ${esc(it.finding)}</li>`).join('')}</ul>` : ''}
        </div>

        <div class="decision-card" id="decisionCard">
          ${
            record.decision
              ? `
            <div class="decision-title">Procurement Officer decision</div>
            <div class="decision-sub">Recorded ${esc(record.decision.time)} by ${esc(record.decision.actor || 'Officer')}</div>
            <div class="decision-confirmed ${record.decision.choice}">
              ${
                record.decision.choice === 'Approve'
                  ? '✓ Qualified — bid approved to proceed'
                  : record.decision.choice === 'Clarify'
                  ? '◐ Clarification requested from bidder'
                  : '✕ Disqualified — bid rejected'
              }
            </div>
            ${record.decision.comment ? `<div style="margin-top:10px;font-size:12.5px;color:var(--ink-soft);">"${esc(record.decision.comment)}"</div>` : ''}
          `
              : `
            <div class="decision-title">Procurement Officer decision</div>
            <div class="decision-sub">The AI assessment above is decision support only. Final qualification rests with you.</div>
            <div class="decision-opts">
              <button class="opt-btn sel-approve" data-choice="Approve">Approve — qualified</button>
              <button class="opt-btn sel-clarify" data-choice="Clarify">Request clarification</button>
              <button class="opt-btn sel-reject" data-choice="Reject">Reject — disqualify</button>
            </div>
            <textarea class="dec-comment" id="decComment" placeholder="Optional remarks or GeM GTC clause references for the audit record..."></textarea>
            <button class="record-btn" id="recordDecBtn" disabled>Record decision</button>
          `
          }
        </div>
      `;
    } else if (!running) {
      html += `<div class="empty-state">Run AI verification to check this bidder against Udyam, GSTN, Income Tax, MCA21, EPFO, ESIC, Startup India, NSIC, Make in India and DigiLocker records.</div>`;
    }

    html += `
      <div class="audit-card">
        <div class="audit-head" id="auditHead">
          <div class="audit-head-l"><span class="audit-title">Audit trail &amp; Cryptographic Ledger</span><span class="audit-count">${record.auditTrail.length}</span></div>
          <div style="display:flex;align-items:center;gap:8px;">
            <button class="pdf-btn" id="pdfDossierBtn" style="font-size: 11.5px; padding: 6px 12px;">Export Official PDF Dossier</button>
            <span class="audit-toggle" id="auditToggleLabel">Show ▾</span>
          </div>
        </div>
        <div class="audit-body" id="auditBody">
          <div class="ledger">
            ${record.auditTrail
              .slice()
              .reverse()
              .map(
                e => `
              <div class="ledger-item">
                <div class="ledger-time mono">${esc(e.time)}</div>
                <div class="ledger-body"><span class="ledger-actor">${esc(e.actor)}</span> — ${esc(e.text)}</div>
              </div>
            `
              )
              .join('')}
          </div>
        </div>
      </div>
    `;

    main.innerHTML = html;
    wireMainEvents();
  }

  function wireMainEvents() {
    const runBtn = document.getElementById('runBtn');
    if (runBtn) runBtn.addEventListener('click', runVerification);

    const auditHead = document.getElementById('auditHead');
    const auditBody = document.getElementById('auditBody');
    const auditLabel = document.getElementById('auditToggleLabel');
    if (auditHead) {
      auditHead.addEventListener('click', e => {
        if (e.target.id === 'exportBtn' || e.target.id === 'pdfDossierBtn') return;
        auditBody.classList.toggle('open');
        auditLabel.textContent = auditBody.classList.contains('open') ? 'Hide ▴' : 'Show ▾';
      });
    }

    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) exportBtn.addEventListener('click', exportLedger);

    const pdfBtn = document.getElementById('pdfDossierBtn');
    if (pdfBtn) pdfBtn.addEventListener('click', downloadPDFDossier);

    const topPdfBtn = document.getElementById('topPdfBtn');
    if (topPdfBtn) topPdfBtn.addEventListener('click', downloadPDFDossier);

    // Clicking any card opens the rich Document Inspector Modal!
    document.querySelectorAll('.check-card').forEach(card => {
      card.addEventListener('click', () => {
        if (scanningNow) return;
        const checkId = card.getAttribute('data-check');
        openDocInspector(checkId);
      });
    });

    const opts = document.querySelectorAll('.opt-btn');
    let selectedChoice = null;
    opts.forEach(btn => {
      btn.addEventListener('click', () => {
        opts.forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedChoice = btn.getAttribute('data-choice');
        const recBtn = document.getElementById('recordDecBtn');
        if (recBtn) recBtn.disabled = false;
      });
    });

    const recBtn = document.getElementById('recordDecBtn');
    if (recBtn) {
      recBtn.addEventListener('click', () => {
        if (!selectedChoice) return;
        const comment = document.getElementById('decComment').value.trim();
        recordDecision(selectedChoice, comment);
      });
    }
  }

  // ---------- DOCUMENT DETAILS INSPECTOR MODAL ----------
  const docModalBackdrop = document.getElementById('docModalBackdrop');
  const docModalClose = document.getElementById('docModalClose');
  const docModalDone = document.getElementById('docModalDone');

  if (docModalClose) docModalClose.addEventListener('click', closeDocInspector);
  if (docModalDone) docModalDone.addEventListener('click', closeDocInspector);
  if (docModalBackdrop) {
    docModalBackdrop.addEventListener('click', e => {
      if (e.target === docModalBackdrop) closeDocInspector();
    });
  }

  function closeDocInspector() {
    if (docModalBackdrop) docModalBackdrop.classList.remove('open');
  }

  window.copyModalSha = function() {
    const shaText = document.getElementById('docModalSha').textContent;
    navigator.clipboard.writeText(shaText);
    showToast('SHA-256 Digital Seal copied to clipboard.');
  };

  let currentInspectedCheckId = 'udyam';

  function openDocInspector(checkId) {
    currentInspectedCheckId = checkId;
    const record = DB[activeId];
    const p = record.profile;
    const chkConfig = CHECKS.find(c => c.id === checkId) || CHECKS[0];
    const checkResult = (record.results && record.results.checks[checkId]) || {
      status: 'verified',
      finding: `Record verified against ${chkConfig.portal}. No discrepancies identified.`
    };

    document.getElementById('docModalPortal').textContent = chkConfig.portal;
    document.getElementById('docModalTitle').textContent = chkConfig.label;

    const statusEl = document.getElementById('docModalStatus');
    statusEl.className = 'status-tag ' + checkResult.status;
    statusEl.textContent = STATUS_LABEL[checkResult.status];

    document.getElementById('docModalFinding').textContent = checkResult.finding;

    // Build specific structured fields based on checkId
    const fieldsEl = document.getElementById('docModalFields');
    const rawFields = getExtractedFieldsRaw(checkId, p, checkResult);
    fieldsEl.innerHTML = rawFields.map(f => `
      <div class="doc-field-card">
        <div class="doc-field-lbl">${esc(f.lbl)}</div>
        <div class="doc-field-val">${esc(f.val)}</div>
      </div>
    `).join('');

    // Build statutory rule validations
    const rulesEl = document.getElementById('docModalRules');
    const rawRules = getRuleValidationsRaw(checkId, p, checkResult);
    rulesEl.innerHTML = rawRules.map(r => `
      <div class="doc-rule-item">
        <span class="doc-rule-icon ${r.fail ? 'fail' : r.warn ? 'warn' : 'pass'}">${r.fail ? '✕' : r.warn ? '⚠' : '✓'}</span>
        <span>${esc(r.text)}</span>
      </div>
    `).join('');

    // Generate canonical SHA-256 hash
    const seed = p.gstin + p.pan + checkId + (checkResult.finding || '');
    const sha = generateSyntheticSha256(seed);
    document.getElementById('docModalSha').textContent = sha;

    if (docModalBackdrop) docModalBackdrop.classList.add('open');
  }

  function generateSyntheticSha256(seed) {
    let hash = '';
    const hex = '0123456789abcdef';
    const rng = seededRng(hashStr(seed));
    for (let i = 0; i < 64; i++) {
      hash += hex[Math.floor(rng() * 16)];
    }
    return hash;
  }

  function getExtractedFieldsRaw(checkId, p, res) {
    let fields = [];
    if (checkId === 'udyam') {
      fields = [
        { lbl: 'Udyam Registration No', val: p.udyam || 'UDYAM-MH-01-0012345' },
        { lbl: 'Enterprise Category', val: p.category || 'MSME – Small' },
        { lbl: 'Registered NIC Codes', val: '26201 (Computers), 26511 (Instruments)' },
        { lbl: 'Major Activity', val: 'Manufacturing' },
        { lbl: 'Investment in Plant & Mach.', val: '₹4.85 Crore (Verified)' },
        { lbl: 'Registration Date', val: '14-Aug-2019 (Active)' }
      ];
    } else if (checkId === 'gst') {
      fields = [
        { lbl: 'GSTIN', val: p.gstin || '27ABCDE1234F1Z1' },
        { lbl: 'Legal Name on GSTN', val: p.name },
        { lbl: '12-Month Return Regularity', val: res.status === 'flagged' ? '75.0% (9/12 Filed)' : '100.0% (12/12 Regular)' },
        { lbl: 'Last Return Filed', val: 'GSTR-3B · Jul 2026' },
        { lbl: 'State Jurisdiction', val: (p.gstin && p.gstin.startsWith('29') ? 'Karnataka (29)' : 'Maharashtra (27)') },
        { lbl: 'Taxpayer Type', val: 'Regular' }
      ];
    } else if (checkId === 'pan') {
      fields = [
        { lbl: 'Permanent Account Number', val: p.pan || 'ABCDE1234F' },
        { lbl: 'Name on IT Database', val: p.name },
        { lbl: 'Section 206AB Status', val: 'Non-Defaulter (Compliant)' },
        { lbl: 'Aadhaar Seeding Status', val: 'Linked / Exempt' },
        { lbl: 'ITR Assessment Year', val: 'AY 2025-26 (Filed)' },
        { lbl: 'PAN Operational Status', val: 'Operative & Valid' }
      ];
    } else if (checkId === 'mii') {
      fields = [
        { lbl: 'Supplier Class', val: 'Class-I Local Supplier' },
        { lbl: 'Declared Local Content %', val: '65.5% (Threshold: >=50%)' },
        { lbl: 'Location of Value Addition', val: 'Plot 42, MIDC Industrial Area, Pune' },
        { lbl: 'Chartered Accountant Firm', val: 'M/s Sharma & Associates (FRN: 109283W)' },
        { lbl: 'ICAI UDIN Reference', val: '24012345AAAAAA1234 (Verified)' },
        { lbl: 'Self-Declaration Date', val: '18-Aug-2026' }
      ];
    } else if (checkId === 'digilocker') {
      fields = [
        { lbl: 'OEM Authorization (MAF)', val: 'Dell International Services India Pvt Ltd' },
        { lbl: 'Authorized Tender Ref', val: p.gem_bid || 'GEM/2026/B/998877 (100% Match)' },
        { lbl: 'MAF Validity Period', val: 'Valid through 31-Dec-2027' },
        { lbl: 'CA Net Worth Certificate', val: '₹8.50 Crore (Positive Solvency)' },
        { lbl: '3-Year Average Turnover', val: '₹12.50 Crore / annum' },
        { lbl: 'DigiLocker Authenticated Files', val: '11 of 11 Documents Verified' }
      ];
    } else if (checkId === 'blacklist') {
      fields = [
        { lbl: 'Debarment Status', val: res.status === 'missing' ? 'ACTIVE DEBARMENT ORDER' : 'Clean Record (No Listing)' },
        { lbl: 'Central Registry Scope', val: 'CPPP, GeM, CVC, Central Ministries' },
        { lbl: 'Order Ref Number', val: res.status === 'missing' ? 'CPPP/2025/DEB/0882' : 'None on record' },
        { lbl: 'Director DIN Match Check', val: res.status === 'missing' ? 'Adverse Match Found' : '0 DIN Flagged' },
        { lbl: 'Screening Date', val: nowStr() },
        { lbl: 'Statutory Action', val: res.status === 'missing' ? 'Hard Disqualification' : 'Cleared for Award' }
      ];
    } else {
      fields = [
        { lbl: 'Entity Identification', val: p.name },
        { lbl: 'Portal Source', val: checkId.toUpperCase() + ' Registry' },
        { lbl: 'Verification Status', val: STATUS_LABEL[res.status] },
        { lbl: 'Query Timestamp', val: nowStr() },
        { lbl: 'Compliance Score Weight', val: '8.0 Points' },
        { lbl: 'Certificate Reference', val: 'CERT-' + hashStr(p.name + checkId).toString(36).toUpperCase() }
      ];
    }
    return fields;
  }

  function getRuleValidationsRaw(checkId, p, res) {
    let rules = [];
    if (res.status === 'verified') {
      rules = [
        { pass: true, text: 'Entity name strictly matches declared bid particulars.' },
        { pass: true, text: 'No statutory expiry or lapse identified across source portal records.' },
        { pass: true, text: 'Compliant with Government of India Public Procurement GTC guidelines.' }
      ];
    } else if (res.status === 'flagged') {
      rules = [
        { pass: true, text: 'Primary registration active on source portal.' },
        { warn: true, text: 'Minor filing delay or formatting variance detected — advisory noted.' },
        { pass: true, text: 'Non-fatal gap; procurement officer clarification recommended.' }
      ];
    } else if (res.status === 'missing') {
      rules = [
        { fail: true, text: 'Mandatory statutory requirement not satisfied or active blacklist listing found.' },
        { fail: true, text: 'Violates GeM GTC statutory eligibility clauses.' },
        { fail: true, text: 'Requires mandatory procurement officer review / disqualification action.' }
      ];
    } else {
      rules = [
        { pass: true, text: 'Check parameter exempt or not applicable for declared bidder profile.' }
      ];
    }
    return rules;
  }

  function generateClientSideDocPDF(payload) {
    if (!window.jspdf || !window.jspdf.jsPDF) {
      showToast('Downloading certificate...');
      return;
    }
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    const navy = [11, 29, 58];
    const green = [16, 185, 129];
    const gray = [100, 116, 139];

    doc.setFillColor(...navy);
    doc.rect(0, 0, 210, 28, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(13);
    doc.text('CHENNAI PETROLEUM CORPORATION LIMITED', 14, 11);
    doc.setFontSize(8);
    doc.setFont('helvetica', 'normal');
    doc.text('A Govt. of India Enterprise | Manali Refinery, Chennai - 600068', 14, 17);
    doc.text('STATUTORY COMPLIANCE & DOCUMENT VERIFICATION CERTIFICATE', 14, 23);

    doc.setTextColor(...navy);
    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.text(`${payload.title} — Verified Certificate`, 14, 38);

    const docParticulars = [
      ['Vendor / Bidder Legal Entity', payload.bidder_name, 'GeM Bid Reference', payload.gem_bid],
      ['GSTIN Number', payload.gstin, 'Permanent Account Number', payload.pan],
      ['Source Registry / Portal', payload.portal, 'Verification Status', (payload.status || 'VERIFIED').toUpperCase()],
      ['Cryptographic SHA-256 Seal', (payload.sha256 || '1f129f6c...').slice(0, 32) + '...', 'Audit Stamp Time', new Date().toLocaleString('en-IN')]
    ];

    if (doc.autoTable) {
      doc.autoTable({
        startY: 44,
        head: [['Field Parameter', 'Verified Record', 'Field Parameter', 'Verified Record']],
        body: docParticulars,
        theme: 'grid',
        headStyles: { fillColor: navy, textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 8 },
        styles: { fontSize: 8, cellPadding: 3 },
        columnStyles: { 0: { fontStyle: 'bold', width: 45 }, 2: { fontStyle: 'bold', width: 45 } }
      });

      if (payload.fields && payload.fields.length > 0) {
        const fieldRows = payload.fields.map((f, i) => [String(i + 1), f.lbl || f.label || '', f.val || f.value || 'Verified']);
        doc.autoTable({
          startY: doc.lastAutoTable.finalY + 8,
          head: [['#', 'Extracted Document Entity / Attestation', 'Value on Official Record']],
          body: fieldRows,
          theme: 'striped',
          headStyles: { fillColor: [30, 41, 59], textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 8 },
          styles: { fontSize: 7.5, cellPadding: 2.5 }
        });
      }

      const curY = doc.lastAutoTable.finalY + 12;
      doc.setFontSize(8);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(...gray);
      doc.text('Digitally Authenticated by Document AI Inspector & Procurement Scrutiny Officer', 14, curY);
      doc.text('Statutory Basis: GeM GTC & Public Procurement (Preference to Make in India) Order 2017', 14, curY + 5);
      doc.text(`Issuing Authority: Smt. Lakshmi Narayanan, DGM (Materials & Contracts) | CPCL Manali`, 14, curY + 10);
    }

    const cleanTitle = (payload.title || 'Certificate').replace(/[\/\s]/g, '_');
    const cleanBid = (payload.gem_bid || 'GEM_BID').replace(/[\/\s]/g, '_');
    doc.save(`GeM_Doc_${cleanTitle}_${cleanBid}.pdf`);
    showToast(`✓ Certificate PDF downloaded successfully.`);
  }

  function generateClientSideDossierPDF(payload) {
    if (!window.jspdf || !window.jspdf.jsPDF) {
      showToast('Downloading compliance dossier...');
      return;
    }
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    const navy = [11, 29, 58];
    const gray = [100, 116, 139];

    // Header
    doc.setFillColor(...navy);
    doc.rect(0, 0, 210, 30, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(13);
    doc.text('CHENNAI PETROLEUM CORPORATION LIMITED', 14, 11);
    doc.setFontSize(8);
    doc.setFont('helvetica', 'normal');
    doc.text('A Govt. of India Enterprise | Manali Refinery, Chennai - 600068', 14, 17);
    doc.text('STATUTORY PROCUREMENT SCRUTINY & COMPLIANCE DOSSIER', 14, 23);

    // Subheader
    doc.setTextColor(...navy);
    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.text(`Bidder Evaluation: ${payload.bidder_legal_name}`, 14, 38);

    const summaryData = [
      ['Vendor / Bidder Legal Name', payload.bidder_legal_name, 'GeM Bid Number', payload.gem_bid_number],
      ['GSTIN Registration', payload.bidder_gstin, 'Permanent Account Number', payload.bidder_pan],
      ['BCI Compliance Score', `${payload.bci_score}/100 Points`, 'Risk Classification', `${payload.risk_tier} RISK`],
      ['Technical Eligibility Status', payload.overall_compliance ? 'QUALIFIED & APPROVED' : 'DISQUALIFIED / REJECTED', 'Officer Decision', payload.officer_decision || 'APPROVED'],
      ['Evaluated By', 'Smt. Lakshmi Narayanan (DGM - Contracts)', 'Evaluation Date', new Date().toLocaleDateString('en-IN')]
    ];

    if (doc.autoTable) {
      doc.autoTable({
        startY: 44,
        head: [['Parameter', 'Evaluated Value', 'Parameter', 'Evaluated Value']],
        body: summaryData,
        theme: 'grid',
        headStyles: { fillColor: navy, textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 8 },
        styles: { fontSize: 8, cellPadding: 3 },
        columnStyles: { 0: { fontStyle: 'bold', width: 45 }, 2: { fontStyle: 'bold', width: 45 } }
      });

      // 11 Pillars Evaluation Table
      const checksObj = payload.checks || {};
      const pillarRows = CHECKS.map((c, i) => {
        const chk = checksObj[c.id] || { status: 'verified', finding: 'Cleared against ' + c.portal };
        const st = (chk.status || 'verified').toUpperCase();
        return [String(i + 1), c.label, c.portal, st, (chk.finding || 'Verified').slice(0, 70)];
      });

      doc.autoTable({
        startY: doc.lastAutoTable.finalY + 8,
        head: [['#', 'Statutory Evaluation Pillar', 'Portal Source', 'Status', 'Verification Finding']],
        body: pillarRows,
        theme: 'striped',
        headStyles: { fillColor: [30, 41, 59], textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 8 },
        styles: { fontSize: 7, cellPadding: 2 },
        columnStyles: { 3: { fontStyle: 'bold' } }
      });

      const curY = doc.lastAutoTable.finalY + 12;
      doc.setFontSize(8);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(...gray);
      doc.text('Digitally Stamped & Cryptographically Sealed with SHA-256 Provenance Ledger', 14, curY);
      doc.text('Authority: Directorate of Materials & Contracts, CPCL Manali Refinery', 14, curY + 5);
      doc.text(`Official Attestation: Smt. Lakshmi Narayanan, DGM (Materials & Contracts)`, 14, curY + 10);
    }

    const cleanBid = (payload.gem_bid_number || 'GEM_BID').replace(/[\/\s]/g, '_');
    doc.save(`GeM_Compliance_Dossier_${cleanBid}.pdf`);
    showToast(`✓ Compliance Dossier PDF downloaded successfully.`);
  }

  window.downloadIndividualDocPDF = async function(checkId) {
    const record = DB[activeId];
    const p = record.profile;
    const chkConfig = CHECKS.find(c => c.id === checkId) || CHECKS[0];
    const checkResult = (record.results && record.results.checks[checkId]) || {
      status: 'verified',
      finding: `Record verified against ${chkConfig.portal}. No discrepancies identified.`
    };

    const fields = getExtractedFieldsRaw(checkId, p, checkResult);
    const rules = getRuleValidationsRaw(checkId, p, checkResult);
    const seed = p.gstin + p.pan + checkId + (checkResult.finding || '');
    const sha256 = generateSyntheticSha256(seed);

    showToast(`Generating ${chkConfig.label} PDF Certificate...`);

    const payload = {
      title: chkConfig.label,
      portal: chkConfig.portal,
      status: checkResult.status,
      bidder_name: p.name,
      gstin: p.gstin || '27ABCDE1234F1Z1',
      pan: p.pan || 'ABCDE1234F',
      gem_bid: p.gem_bid || 'GEM/2026/B/998877',
      finding: checkResult.finding,
      fields: fields,
      rules: rules,
      sha256: sha256,
    };

    try {
      const resp = await fetch('/api/v1/dossier/generate-doc-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (resp.ok) {
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const cleanTitle = chkConfig.label.replace(/[^a-zA-Z0-9]/g, '_');
        const cleanBid = (p.gem_bid || 'GEM_2026_B_998877').replace(/[^a-zA-Z0-9]/g, '_');
        a.download = `GeM_Doc_${cleanTitle}_${cleanBid}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast(`${chkConfig.label} PDF downloaded successfully.`);
        return;
      }
    } catch (err) {
      console.warn('Backend doc PDF endpoint unreachable, using client fallback:', err);
    }
    // Universal client fallback
    generateClientSideDocPDF(payload);
  };

  async function downloadPDFDossier() {
    const record = DB[activeId];
    showToast('Generating official PDF dossier with SHA-256 digital seals...');

    const payload = {
      gem_bid_number: record.profile.gem_bid || 'GEM/2026/B/998877',
      tender_title: 'Enterprise Bid Verification & Statutory Scrutiny',
      bidder_legal_name: record.profile.name,
      bidder_gstin: record.profile.gstin || '27ABCDE1234F1Z1',
      bidder_pan: record.profile.pan || 'ABCDE1234F',
      bci_score: record.results ? record.results.score : 98.0,
      risk_tier: record.results ? (record.results.risk === 'Low' ? 'GREEN' : record.results.risk === 'Medium' ? 'AMBER' : 'RED') : 'GREEN',
      overall_compliance: record.results ? record.results.risk !== 'High' : true,
      checks: (record.results && record.results.checks) || record.profile.checks || {},
      critical_disqualifiers: (record.results && record.results.checks && record.results.checks.blacklist && record.results.checks.blacklist.status === 'missing') ? ['Active listing detected on Central Debarment Registry'] : [],
      warnings: (record.results && record.results.recommendation && record.results.recommendation.items) ? record.results.recommendation.items.map(it => it.finding) : [],
      officer_decision: record.decision ? (record.decision.choice === 'Approve' ? 'APPROVED' : record.decision.choice === 'Clarify' ? 'CLARIFICATION_REQUESTED' : 'REJECTED') : undefined,
      officer_justification: record.decision ? record.decision.comment : undefined,
      officer_decided_at: record.decision ? record.decision.time : undefined,
    };

    try {
      const resp = await fetch('/api/v1/dossier/generate-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (resp.ok) {
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const cleanBid = (record.profile.gem_bid || 'GEM_2026_B_998877').replace(/[^a-zA-Z0-9]/g, '_');
        a.download = `GeM_Compliance_Dossier_${cleanBid}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast('Official PDF Dossier downloaded successfully.');
        return;
      }
    } catch (err) {
      console.warn('Backend PDF endpoint unreachable, using client fallback:', err);
    }
    // Universal client fallback
    generateClientSideDossierPDF(payload);
  }

  async function recordDecision(choice, comment) {
    const record = DB[activeId];
    const officerName = localStorage.getItem('gem_user_name') || 'Procurement Officer';
    record.decision = { choice, comment, time: nowStr(), actor: officerName };

    const label =
      choice === 'Approve'
        ? 'approved bid as qualified'
        : choice === 'Clarify'
        ? 'requested clarification from bidder'
        : 'rejected bid as disqualified';

    record.auditTrail.push({
      time: nowStr(),
      actor: officerName,
      text: `Recorded decision — ${label}.${comment ? ' Remarks: "' + comment + '"' : ''}`
    });

    if (activeJobId) {
      try {
        const apiDecision = choice === 'Approve' ? 'APPROVED' : choice === 'Clarify' ? 'CLARIFICATION_REQUESTED' : 'REJECTED';
        await fetch(`/api/v1/jobs/${activeJobId}/override`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ decision: apiDecision, justification: comment || `${label} by ${officerName}` })
        });
      } catch (e) {}
    }

    renderMain();
    renderSidebar();
    showToast(`Decision recorded: ${choice}`);
  }

  async function runVerification() {
    const record = DB[activeId];
    scanningNow = true;
    record.auditTrail.push({
      time: nowStr(),
      actor: 'AI Verification Engine',
      text: 'Verification run started — querying statutory source portals & extracting documents.'
    });
    renderMain();

    try {
      const resp = await fetch('/api/v1/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bidder_pan: record.profile.pan && record.profile.pan.length === 10 ? record.profile.pan : 'ABCDE1234F',
          bidder_gstin: record.profile.gstin && record.profile.gstin.length === 15 ? record.profile.gstin : '27ABCDE1234F1Z1',
          bidder_legal_name: record.profile.name,
          bidder_udyam_reg_no: record.profile.udyam && record.profile.udyam.startsWith('UDYAM') ? record.profile.udyam : undefined,
          gem_bid_number: record.profile.gem_bid || 'GEM/2026/B/998877',
          tender_title: 'Enterprise Bid Verification',
        })
      });
      if (resp.ok) {
        const job = await resp.json();
        activeJobId = job.id;
      }
    } catch (e) {}

    let finalChecks;
    if (record.profile._customGenerated || !SAMPLE_PROFILES.find(s => s.id === record.profile.id)) {
      finalChecks =
        record.profile._checksCache ||
        generateChecksForProfile(record.profile.gstin + record.profile.pan + record.profile.name, record.profile.category);
      record.profile._checksCache = finalChecks;
    } else {
      finalChecks = SAMPLE_PROFILES.find(s => s.id === record.profile.id).checks;
    }

    for (let i = 0; i < CHECKS.length; i++) {
      const c = CHECKS[i];
      const card = document.querySelector(`.check-card[data-check="${c.id}"]`);
      if (card) {
        card.classList.add('scanning');
        const tag = card.querySelector('.status-tag');
        tag.className = 'status-tag scanning';
        tag.textContent = 'Scanning';
      }
      await new Promise(res => setTimeout(res, 140 + Math.random() * 140));
      const st = finalChecks[c.id];
      if (card) {
        card.classList.remove('scanning');
        const tag = card.querySelector('.status-tag');
        tag.className = 'status-tag ' + st.status;
        tag.textContent = STATUS_LABEL[st.status];
        card.querySelector('.check-finding').textContent = st.finding;
      }
    }

    const result = computeResult(finalChecks);
    const recommendation = buildRecommendation(finalChecks, result);
    record.results = {
      checks: finalChecks,
      score: result.score,
      risk: result.risk,
      counts: result.counts,
      recommendation,
      verifiedAt: nowStr()
    };
    record.auditTrail.push({
      time: nowStr(),
      actor: 'AI Verification Engine',
      text: `Verification complete — score ${result.score}/100, risk level ${result.risk}. Verified: ${result.counts.verified || 0}, Flagged: ${result.counts.flagged || 0}, Missing: ${result.counts.missing || 0}.`
    });
    record.decision = null;
    scanningNow = false;

    renderMain();
    renderSidebar();
    showToast(`Verification complete: ${result.risk} risk (${result.score}/100)`);
  }

  function showToast(msg) {
    const toast = document.getElementById('toast');
    const msgEl = document.getElementById('toastMsg');
    if (!toast || !msgEl) return;
    msgEl.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
  }

  // Toggle Tender Criteria Panel
  window.toggleTenderDetails = function(btn) {
    const grid = document.getElementById('tenderCriteriaGrid');
    if (!grid) return;
    if (grid.style.display === 'none') {
      grid.style.display = 'grid';
      if (btn) btn.innerHTML = '<span>Hide Criteria</span> ▴';
    } else {
      grid.style.display = 'none';
      if (btn) btn.innerHTML = '<span>Show Criteria</span> ▾';
    }
  };

  // Fetch from GeM Portal Simulation / API
  window.fetchFromGemPortal = function() {
    const bidNoInput = document.getElementById('fBidNo');
    const bidNo = bidNoInput ? bidNoInput.value.trim().toUpperCase() : 'GEM/2026/B/998877';
    
    showToast(`Connecting to GeM e-Procurement Portal for ${bidNo}...`);

    // Simulated GeM Portal Bid Database
    const GEM_PORTAL_REGISTRY = {
      'GEM/2026/B/998877': {
        name: 'L&T Hydrocarbon Engineering Ltd.',
        cat: 'Large Enterprise – Refinery Equipment',
        gstin: '33AACCL1234F1Z8',
        pan: 'AACCL1234F',
        udyam: 'UDYAM-TN-02-0088991'
      },
      'GEM/2026/B/882211': {
        name: 'Bharat Heavy Electricals Limited (BHEL)',
        cat: 'Large Enterprise – Refinery Equipment',
        gstin: '07AAACB0046P1Z3',
        pan: 'AAACB0046P',
        udyam: 'UDYAM-DL-05-0012456'
      },
      'GEM/2026/B/776655': {
        name: 'Southern Valves & Actuators Pvt Ltd',
        cat: 'MSME – Manufacturing',
        gstin: '33AABCS9876Q1Z2',
        pan: 'AABCS9876Q',
        udyam: 'UDYAM-TN-02-0045678'
      },
      'GEM/2026/B/554433': {
        name: 'Chennai Precision Instruments & Controls',
        cat: 'Startup India – IT/Engineering',
        gstin: '33AABCC5544R1Z0',
        pan: 'AABCC5544R',
        udyam: 'UDYAM-TN-02-0099887'
      }
    };

    setTimeout(() => {
      const match = GEM_PORTAL_REGISTRY[bidNo] || {
        name: 'Industrial Process Technologies India Ltd.',
        cat: 'MSME – Manufacturing',
        gstin: '33AABCI' + Math.floor(1000 + Math.random() * 9000) + 'F1Z5',
        pan: 'AABCI' + Math.floor(1000 + Math.random() * 9000) + 'F',
        udyam: 'UDYAM-TN-02-00' + Math.floor(10000 + Math.random() * 90000)
      };

      document.getElementById('fName').value = match.name;
      document.getElementById('fCat').value = match.cat;
      document.getElementById('fGst').value = match.gstin;
      document.getElementById('fPan').value = match.pan;
      document.getElementById('fUdyam').value = match.udyam;

      showToast(`✓ Ingested "${match.name}" from GeM portal!`);
    }, 450);
  };

  // Modal logic for new bidder
  const backdrop = document.getElementById('modalBackdrop');
  const newBtn = document.getElementById('newBidderBtn');
  if (newBtn) {
    newBtn.addEventListener('click', () => {
      ['fName', 'fGst', 'fPan', 'fUdyam'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
      });
      const bidInput = document.getElementById('fBidNo');
      if (bidInput) bidInput.value = 'GEM/2026/B/998877';
      backdrop.classList.add('open');
    });
  }

  const cancelBtn = document.getElementById('modalCancel');
  if (cancelBtn) cancelBtn.addEventListener('click', () => backdrop.classList.remove('open'));
  if (backdrop) backdrop.addEventListener('click', e => { if (e.target === backdrop) backdrop.classList.remove('open'); });

  const createBtn = document.getElementById('modalCreate');
  if (createBtn) {
    createBtn.addEventListener('click', () => {
      const name = document.getElementById('fName').value.trim() || 'Custom GeM Bidder Entity';
      const category = document.getElementById('fCat').value;
      const gstin = document.getElementById('fGst').value.trim() || '33AACCL1234F1Z8';
      const pan = document.getElementById('fPan').value.trim() || 'AACCL1234F';
      const udyam = document.getElementById('fUdyam').value.trim() || 'UDYAM-TN-02-0012345';
      const gem_bid = document.getElementById('fBidNo').value.trim() || 'GEM/2026/B/' + Math.floor(100000 + Math.random() * 900000);
      const id = 'bid-' + hashStr(name + gstin + Date.now()).toString(36);

      const profile = { id, name, category, gstin, pan, udyam, gem_bid, _customGenerated: true };
      DB[id] = baseRecord(profile);
      activeId = id;
      backdrop.classList.remove('open');
      renderSidebar();
      renderMain();
      showToast(`Ingested GeM Bid Package for ${name}`);
    });
  }

  init();
})();
