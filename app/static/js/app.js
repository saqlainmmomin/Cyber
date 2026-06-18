// CyberAssess — HTMX config + interaction layer

// ── HTMX Configuration ─────────────────────────

document.body.addEventListener('htmx:configRequest', function(event) {
  // Add CSRF or other headers if needed later
});

// HTMX-aware redirects (e.g., auth redirect on 401)
document.body.addEventListener('htmx:responseError', function(event) {
  if (event.detail.xhr.status === 401) {
    window.location.href = '/login';
  } else {
    CyberToast.show('Something went wrong. Please try again.', 'error');
  }
});

// Handle HX-Redirect header
document.body.addEventListener('htmx:beforeSwap', function(event) {
  if (event.detail.xhr.status === 401) {
    window.location.href = '/login';
    event.detail.shouldSwap = false;
  }
});

// ── Toast Notifications ─────────────────────────

const CyberToast = {
  container: null,

  init() {
    this.container = document.createElement('div');
    this.container.className = 'fixed bottom-6 right-6 z-50 flex flex-col gap-2 pointer-events-none';
    document.body.appendChild(this.container);
  },

  show(message, type = 'success') {
    if (!this.container) this.init();
    const colors = {
      success: 'bg-green-800 text-green-100 border-green-700',
      error: 'bg-red-900 text-red-100 border-red-800',
      info: 'bg-gray-800 text-gray-100 border-gray-700',
    };
    const icons = {
      success: '✓',
      error: '✕',
      info: 'ℹ',
    };
    const toast = document.createElement('div');
    toast.className = `${colors[type] || colors.info} pointer-events-auto px-4 py-3 rounded-lg text-sm border shadow-lg flex items-center gap-2 transform translate-y-2 opacity-0 transition-all duration-200 max-w-sm`;
    toast.innerHTML = `<span class="font-medium">${icons[type] || ''}</span><span>${message}</span>`;
    this.container.appendChild(toast);
    requestAnimationFrame(() => {
      toast.classList.remove('translate-y-2', 'opacity-0');
    });
    setTimeout(() => {
      toast.classList.add('translate-y-2', 'opacity-0');
      setTimeout(() => toast.remove(), 200);
    }, 3000);
  }
};

// Listen for X-Toast-Message header from HTMX responses
document.body.addEventListener('htmx:afterSwap', (event) => {
  const msg = event.detail.xhr?.getResponseHeader('X-Toast-Message');
  if (msg) {
    const type = event.detail.xhr.getResponseHeader('X-Toast-Type') || 'success';
    CyberToast.show(decodeURIComponent(msg), type);
  }
});

// ── Copy to Clipboard ───────────────────────────

document.addEventListener('click', (e) => {
  const trigger = e.target.closest('[data-copy-trigger]');
  if (!trigger) return;

  const targetId = trigger.dataset.copyTrigger;
  const target = document.querySelector(`[data-copy-target="${targetId}"]`);
  if (!target) return;

  const text = target.textContent.trim();
  navigator.clipboard.writeText(text).then(() => {
    CyberToast.show('Copied to clipboard', 'info');
  }).catch(() => {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    CyberToast.show('Copied to clipboard', 'info');
  });
});

// ── Save Indicator ──────────────────────────────

document.body.addEventListener('htmx:afterSwap', (event) => {
  const indicator = document.querySelector('[data-save-indicator]');
  if (!indicator) return;

  const target = event.detail.target;
  if (target && (target.id === 'section-content' || target.closest('[data-questionnaire-form]'))) {
    const now = new Date();
    indicator.textContent = `Saved ${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    indicator.classList.remove('hidden');
    indicator.classList.add('text-green-600', 'dark:text-green-400');
    setTimeout(() => {
      indicator.classList.remove('text-green-600', 'dark:text-green-400');
      indicator.classList.add('text-gray-400', 'dark:text-gray-500');
    }, 2000);
  }
});

// ── Dashboard Search/Filter ─────────────────────

document.addEventListener('input', (e) => {
  if (!e.target.matches('[data-filter-input]')) return;
  const query = e.target.value.toLowerCase();
  document.querySelectorAll('[data-assessment-card]').forEach(card => {
    const text = card.textContent.toLowerCase();
    card.style.display = text.includes(query) ? '' : 'none';
  });
});

// Inject search input if dashboard has more than 3 assessment cards
document.addEventListener('DOMContentLoaded', () => {
  const cards = document.querySelectorAll('[data-assessment-card]');
  if (cards.length > 3) {
    const container = cards[0]?.parentElement;
    if (container) {
      const searchDiv = document.createElement('div');
      searchDiv.className = 'mb-4';
      searchDiv.innerHTML = `<input type="text" data-filter-input placeholder="Filter assessments..."
        class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:border-navy-500 dark:focus:border-navy-400 focus:ring-2 focus:ring-navy-100 dark:focus:ring-navy-900 outline-none transition placeholder-gray-400 dark:placeholder-gray-500">`;
      container.parentElement.insertBefore(searchDiv, container);
    }
  }
});

// ── Keyboard Shortcuts ──────────────────────────

const Shortcuts = {
  enabled: true,

  init() {
    document.addEventListener('keydown', (e) => {
      if (!this.enabled) return;
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;
      if (e.target.isContentEditable) return;

      const key = e.key.toLowerCase();
      const scope = document.querySelector('[data-shortcut-scope]')?.dataset.shortcutScope;

      if (key === '?' && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        this.showHelp();
        return;
      }

      if (scope === 'dashboard') {
        if (key === 'n') {
          e.preventDefault();
          window.location.href = '/assessments/new';
        }
      }

      if (scope === 'questionnaire') {
        if (key === 'j' || key === 'k') {
          e.preventDefault();
          this.navigateQuestions(key === 'j' ? 1 : -1);
        }
        if (['1', '2', '3', '4', '5'].includes(key)) {
          e.preventDefault();
          this.selectOption(parseInt(key));
        }
        if (key === 's' && !e.ctrlKey && !e.metaKey) {
          e.preventDefault();
          const form = document.querySelector('[data-questionnaire-form]');
          if (form) htmx.trigger(form, 'submit');
        }
      }
    });
  },

  currentQuestionIndex: -1,

  navigateQuestions(direction) {
    const cards = Array.from(document.querySelectorAll('[data-question-index]'));
    if (!cards.length) return;

    this.currentQuestionIndex = Math.max(0, Math.min(cards.length - 1, this.currentQuestionIndex + direction));
    const target = cards[this.currentQuestionIndex];
    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    cards.forEach(c => c.classList.remove('ring-2', 'ring-navy-300', 'dark:ring-navy-600'));
    target.classList.add('ring-2', 'ring-navy-300', 'dark:ring-navy-600');
  },

  selectOption(num) {
    const cards = document.querySelectorAll('[data-question-index]');
    if (this.currentQuestionIndex < 0 || this.currentQuestionIndex >= cards.length) return;
    const card = cards[this.currentQuestionIndex];
    const radios = card.querySelectorAll('input[type="radio"]');
    if (radios[num - 1]) {
      radios[num - 1].checked = true;
      radios[num - 1].dispatchEvent(new Event('change', { bubbles: true }));
    }
  },

  showHelp() {
    const existing = document.getElementById('shortcut-help-modal');
    if (existing) { existing.remove(); return; }

    const modal = document.createElement('div');
    modal.id = 'shortcut-help-modal';
    modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/40';
    modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
    modal.innerHTML = `
      <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 max-w-sm w-full mx-4 shadow-xl">
        <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-4">Keyboard Shortcuts</h3>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between"><span class="text-gray-500 dark:text-gray-400">Show this help</span><kbd class="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono text-gray-700 dark:text-gray-300">?</kbd></div>
          <div class="flex justify-between"><span class="text-gray-500 dark:text-gray-400">New assessment</span><kbd class="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono text-gray-700 dark:text-gray-300">n</kbd></div>
          <hr class="border-gray-100 dark:border-gray-800">
          <p class="text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wide">Questionnaire</p>
          <div class="flex justify-between"><span class="text-gray-500 dark:text-gray-400">Next question</span><kbd class="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono text-gray-700 dark:text-gray-300">j</kbd></div>
          <div class="flex justify-between"><span class="text-gray-500 dark:text-gray-400">Previous question</span><kbd class="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono text-gray-700 dark:text-gray-300">k</kbd></div>
          <div class="flex justify-between"><span class="text-gray-500 dark:text-gray-400">Select option 1–5</span><kbd class="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono text-gray-700 dark:text-gray-300">1-5</kbd></div>
          <div class="flex justify-between"><span class="text-gray-500 dark:text-gray-400">Save section</span><kbd class="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono text-gray-700 dark:text-gray-300">s</kbd></div>
        </div>
        <button onclick="this.closest('#shortcut-help-modal').remove()" class="mt-4 w-full text-center text-xs text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300">Press ? or click to close</button>
      </div>`;
    document.body.appendChild(modal);
  }
};

Shortcuts.init();

// ── Collapsible Sections ────────────────────────

document.addEventListener('click', (e) => {
  const section = e.target.closest('[data-collapsible-section]');
  if (!section) return;

  const sectionId = section.dataset.collapsibleSection;
  const assessmentId = section.closest('[data-assessment-id]')?.dataset.assessmentId;
  if (!assessmentId || !sectionId) return;

  const key = `collapsed_${assessmentId}`;
  const collapsed = JSON.parse(localStorage.getItem(key) || '[]');

  if (collapsed.includes(sectionId)) {
    collapsed.splice(collapsed.indexOf(sectionId), 1);
  } else {
    collapsed.push(sectionId);
  }
  localStorage.setItem(key, JSON.stringify(collapsed));
});

// Restore collapsed state after HTMX swap
document.body.addEventListener('htmx:afterSettle', () => {
  const container = document.querySelector('[data-assessment-id]');
  if (!container) return;
  const key = `collapsed_${container.dataset.assessmentId}`;
  const collapsed = JSON.parse(localStorage.getItem(key) || '[]');
  collapsed.forEach(id => {
    const section = document.querySelector(`[data-collapsible-section="${id}"]`);
    if (section) {
      const details = section.querySelector('details');
      if (details) details.removeAttribute('open');
    }
  });
});

// ── Review Queue Filtering ──────────────────────

document.addEventListener('click', (e) => {
  const filter = e.target.closest('[data-review-filter]');
  if (!filter) return;

  const type = filter.dataset.reviewFilter;

  filter.closest('.flex').querySelectorAll('[data-review-filter]').forEach(btn => {
    btn.classList.remove('bg-navy-50', 'dark:bg-navy-900/40', 'text-brand', 'dark:text-navy-300', 'border-navy-200', 'dark:border-navy-700');
    btn.classList.add('text-gray-500', 'dark:text-gray-400', 'border-transparent');
  });
  filter.classList.add('bg-navy-50', 'dark:bg-navy-900/40', 'text-brand', 'dark:text-navy-300', 'border-navy-200', 'dark:border-navy-700');
  filter.classList.remove('text-gray-500', 'dark:text-gray-400', 'border-transparent');

  document.querySelectorAll('[data-review-card]').forEach(card => {
    const status = card.dataset.reviewStatus;
    const risk = card.dataset.riskLevel;
    let show = true;

    if (type === 'draft') show = status === 'draft';
    else if (type === 'high') show = ['critical', 'high'].includes(risk);
    else if (type === 'rejected') show = status === 'rejected';

    card.style.display = show ? '' : 'none';
  });
});

// ── Upload Handling ─────────────────────────────

function initDropZone(zoneId) {
  const zone = document.getElementById(zoneId);
  if (!zone) return;

  ['dragenter', 'dragover'].forEach(type => {
    zone.addEventListener(type, (e) => {
      e.preventDefault();
      zone.classList.add('drag-over');
    });
  });

  ['dragleave', 'drop'].forEach(type => {
    zone.addEventListener(type, (e) => {
      e.preventDefault();
      zone.classList.remove('drag-over');
    });
  });

  zone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const input = zone.querySelector('input[type="file"]');
      if (input) {
        input.files = files;
        htmx.trigger(input, 'change');
      }
    }
  });
}

document.body.addEventListener('htmx:xhr:progress', function(event) {
  if (event.detail.lengthComputable) {
    const percent = Math.round((event.detail.loaded / event.detail.total) * 100);
    const bar = document.getElementById('upload-progress-bar');
    if (bar) {
      bar.style.width = percent + '%';
      bar.textContent = percent + '%';
    }
  }
});
