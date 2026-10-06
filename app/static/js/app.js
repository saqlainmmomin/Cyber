// CyberAssess — HTMX config + interaction layer

// ── HTMX Configuration ─────────────────────────

document.body.addEventListener('htmx:configRequest', function(event) {
  // Add CSRF or other headers if needed later
});

// ── Global Yozora behaviour ──────────────────────

const activeRequests = new Set();

function decodeHeader(value) {
  if (!value) return '';
  try { return decodeURIComponent(value); } catch (_error) { return value; }
}

function toastContainer() {
  let container = document.querySelector('[data-global-toasts], .toasts');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toasts';
    container.setAttribute('data-global-toasts', 'true');
    container.setAttribute('aria-live', 'polite');
    document.body.appendChild(container);
  }
  return container;
}

function toastIcon(symbol) {
  const svg = document.createElement('svg');
  svg.className = 'i lead-i';
  const use = document.createElement('use');
  use.setAttribute('href', `#i-${symbol}`);
  svg.appendChild(use);
  return svg;
}

function dismissToast(item) {
  if (!item) return;
  if (item._toastTimer) window.clearTimeout(item._toastTimer);
  item.remove();
}

function toast(kind = 'success', message = '', action = null) {
  const tone = kind === 'info' || kind === 'information' ? 'information' : kind;
  const isError = tone === 'error';
  const item = document.createElement('div');
  item.className = `toast${isError ? ' bad' : tone === 'information' ? ' info' : ''}`;
  item.setAttribute('role', isError ? 'alert' : 'status');
  item.appendChild(toastIcon(isError ? 'alert' : 'check'));

  const text = document.createElement('span');
  text.className = 'msg grow';
  text.textContent = String(message);
  item.appendChild(text);

  const actionLabel = typeof action === 'string' ? action : action && action.label;
  if (actionLabel) {
    const actionButton = document.createElement('button');
    actionButton.className = 'btn ghost sm';
    actionButton.type = 'button';
    actionButton.textContent = actionLabel;
    if (action && typeof action.onClick === 'function') actionButton.addEventListener('click', action.onClick);
    item.appendChild(actionButton);
  }

  if (isError) {
    const close = document.createElement('button');
    close.className = 'btn ghost icon sm';
    close.type = 'button';
    close.setAttribute('aria-label', 'Dismiss');
    close.appendChild(toastIcon('x'));
    close.addEventListener('click', () => dismissToast(item));
    item.appendChild(close);
  }

  toastContainer().appendChild(item);
  if (!isError) item._toastTimer = window.setTimeout(() => dismissToast(item), 4000);
  return item;
}

window.toast = toast;

function requestTarget(detail) {
  if (detail && detail.target) {
    if (typeof detail.target !== 'string') return detail.target;
    try { return document.querySelector(detail.target); } catch (_error) { return null; }
  }
  const selector = detail && detail.requestConfig && detail.requestConfig.target;
  if (selector) {
    try { return document.querySelector(selector); } catch (_error) { return null; }
  }
  return null;
}

function requestButton(detail) {
  const element = detail && detail.elt;
  if (element && element.matches && element.matches('button')) return element;
  if (element && element.querySelector) {
    return element.querySelector('button[type="submit"], button.btn');
  }
  return document.activeElement && document.activeElement.closest
    ? document.activeElement.closest('button.btn')
    : null;
}

function requestSkeleton(target, state) {
  state.timer = window.setTimeout(() => {
    if (state.settled || !target) return;
    const stack = document.createElement('span');
    stack.className = 'skel-stack';
    ['62%', '88%', '72%'].forEach((width) => {
      const line = document.createElement('span');
      line.className = 'skel';
      line.style.width = width;
      stack.appendChild(line);
    });
    target.replaceChildren(stack);
    target.setAttribute('aria-busy', 'true');
    state.skeleton = stack;
  }, 300);
}

function cleanupRequest(state) {
  if (!state) return;
  state.settled = true;
  window.clearTimeout(state.timer);
  if (state.button) {
    state.button.classList.remove('loading');
    state.button.removeAttribute('aria-busy');
  }
  if (state.target) {
    state.target.removeAttribute('aria-busy');
    if (state.skeleton && state.skeleton.isConnected) state.skeleton.remove();
  }
  activeRequests.delete(state);
}

function swapAlert(target, title, body) {
  if (!target) return;
  const alert = document.createElement('div');
  alert.className = 'alert c-non';
  alert.setAttribute('role', 'alert');
  alert.appendChild(toastIcon('alert'));
  const copy = document.createElement('div');
  const heading = document.createElement('b');
  heading.textContent = title;
  copy.appendChild(heading);
  copy.appendChild(document.createTextNode(body));
  alert.appendChild(copy);
  target.replaceChildren(alert);
  target.classList.remove('swap-in');
  void target.offsetWidth;
  target.classList.add('swap-in');
}

function requestError(event, fallback) {
  const detail = event.detail || {};
  const xhr = detail.xhr;
  if (xhr && xhr.getResponseHeader('X-Conclusion-Conflict')) return;
  if (xhr && xhr.status === 401) {
    window.location.href = '/login';
    detail.shouldSwap = false;
    return;
  }
  const message = decodeHeader(xhr && xhr.getResponseHeader('X-Toast-Message')) || fallback;
  detail.shouldSwap = false;
  detail.isError = false;
  swapAlert(requestTarget(detail), 'The request failed', message);
  toast('error', message);
}

document.body.addEventListener('htmx:beforeRequest', (event) => {
  const detail = event.detail || {};
  const state = { elt: detail.elt, target: requestTarget(detail), button: requestButton(detail), settled: false };
  if (state.button) {
    state.button.classList.add('loading');
    state.button.setAttribute('aria-busy', 'true');
  }
  if (state.target) requestSkeleton(state.target, state);
  activeRequests.add(state);
});

document.body.addEventListener('htmx:responseError', (event) => {
  requestError(event, 'Something went wrong. Please try again.');
});

document.body.addEventListener('htmx:sendError', (event) => {
  const detail = event.detail || {};
  detail.shouldSwap = false;
  swapAlert(requestTarget(detail), 'The request failed', 'The request could not be completed. Check your connection and try again.');
  toast('error', 'The request could not be completed. Check your connection and try again.');
});

// Handle HX-Redirect and the optimistic-concurrency conflict response.
document.body.addEventListener('htmx:beforeSwap', function(event) {
  const xhr = event.detail.xhr;
  if (xhr && xhr.status === 409 && xhr.getResponseHeader('X-Conclusion-Conflict')) {
    event.detail.shouldSwap = true;
    event.detail.isError = false;
  }
  if (xhr && xhr.status === 401) {
    window.location.href = '/login';
    event.detail.shouldSwap = false;
  }
});

document.body.addEventListener('htmx:afterSwap', (event) => {
  const target = event.detail && event.detail.target;
  if (target) {
    target.classList.remove('swap-in');
    void target.offsetWidth;
    target.classList.add('swap-in');
    window.setTimeout(() => target.classList.remove('swap-in'), 220);
  }
  const xhr = event.detail && event.detail.xhr;
  const msg = xhr && xhr.getResponseHeader('X-Toast-Message');
  if (msg) toast(xhr.getResponseHeader('X-Toast-Type') || 'success', decodeHeader(msg));
});

document.body.addEventListener('htmx:afterRequest', (event) => {
  const detail = event.detail || {};
  const modal = detail.elt && detail.elt.closest && detail.elt.closest('[data-modal], .scrim-modal');
  if (modal && !detail.successful) modalClose(modal);
  activeRequests.forEach((state) => {
    if (state.elt === detail.elt) cleanupRequest(state);
  });
});

document.body.addEventListener('htmx:afterSettle', (event) => {
  const target = event.detail && event.detail.target;
  activeRequests.forEach((state) => {
    if (state.target === target) cleanupRequest(state);
  });
});

document.addEventListener('click', (event) => {
  const toastTrigger = event.target.closest && event.target.closest('[data-toast-kind]');
  if (toastTrigger) {
    toast(toastTrigger.dataset.toastKind, toastTrigger.dataset.toastMessage || toastTrigger.textContent.trim(), toastTrigger.dataset.toastAction || null);
    return;
  }
});

document.addEventListener('click', (event) => {
  const row = event.target.closest && event.target.closest('tr[data-href]');
  if (row && !event.target.closest('a, button, input, select, textarea, label')) {
    window.location.href = row.dataset.href;
    return;
  }
  const copy = event.target.closest && event.target.closest('[data-copy-checksum]');
  if (copy && navigator.clipboard) {
    navigator.clipboard.writeText(copy.dataset.copyChecksum).then(() => toast('success', 'Checksum copied'));
  }
});

// ── Menus and modal dialogs ─────────────────────

function focusable(container) {
  return [...container.querySelectorAll('a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')]
    .filter((element) => !element.hidden && element.offsetParent !== null);
}

function modalOpen(modal, opener) {
  if (!modal) return;
  modal.__yozoraOpener = opener || modal.__yozoraOpener || null;
  modal.hidden = false;
  document.documentElement.classList.add('modal-open');
  document.body.classList.add('modal-open');
  const first = modal.querySelector('input:not([type="hidden"]):not([disabled]), [autofocus]') || focusable(modal)[0];
  if (first) first.focus();
}

function refreshModalLock() {
  const open = [...document.querySelectorAll('[data-modal], .scrim-modal, [data-confirm-dialog]')]
    .some((modal) => !modal.hidden);
  document.documentElement.classList.toggle('modal-open', open);
  document.body.classList.toggle('modal-open', open);
}

function modalClose(modal) {
  if (!modal) return;
  const opener = modal.__yozoraOpener;
  modal.hidden = true;
  if (modal.matches('[data-confirm-dialog]')) modal.remove();
  refreshModalLock();
  if (opener && opener.isConnected) opener.focus();
}

function syncConfirm(form) {
  const input = form.querySelector('[name="confirm_name"], [data-confirm-input]');
  const submit = form.querySelector('[type="submit"], [data-confirm-submit]');
  if (input && submit && form.dataset.confirmValue !== undefined) {
    submit.disabled = input.value !== form.dataset.confirmValue;
  }
}

function menuFor(trigger) {
  const selector = trigger.dataset.menuTarget;
  if (selector) {
    try { return document.querySelector(selector); } catch (_error) { return null; }
  }
  return trigger.closest('.anchor')?.querySelector('.menu') || trigger.parentElement?.querySelector('.menu');
}

function menuItems(menu) {
  return [...menu.querySelectorAll('[role="menuitem"], [role="option"], button.mi')]
    .filter((item) => !item.disabled && item.getAttribute('aria-disabled') !== 'true');
}

function positionMenu(menu) {
  if (!menu || !menu.matches('.anchor .menu')) return;
  menu.classList.remove('flip-x', 'flip-y');
  requestAnimationFrame(() => {
    const rect = menu.getBoundingClientRect();
    if (rect.bottom > window.innerHeight - 8) menu.classList.add('flip-y');
    if (rect.left < 8) menu.classList.add('flip-x');
  });
}

function menuClose(menu, restoreFocus = false) {
  if (!menu) return;
  menu.classList.remove('open', 'flip-x', 'flip-y');
  const trigger = menu.__yozoraTrigger;
  if (trigger) trigger.setAttribute('aria-expanded', 'false');
  if (restoreFocus && trigger && trigger.isConnected) trigger.focus();
}

function menusCloseAll(restoreFocus = false, except = null) {
  document.querySelectorAll('.anchor .menu.open').forEach((menu) => {
    if (menu !== except) menuClose(menu, restoreFocus);
  });
  const account = document.getElementById('userMenu');
  if (account && account.classList.contains('open') && account !== except) {
    account.classList.remove('open');
    document.getElementById('userBtn')?.setAttribute('aria-expanded', 'false');
    if (restoreFocus) document.getElementById('userBtn')?.focus();
  }
}

document.addEventListener('click', (event) => {
  const opener = event.target.closest && event.target.closest('[data-menu]');
  if (opener) {
    const menu = menuFor(opener);
    if (!menu) return;
    event.stopPropagation();
    const open = !menu.classList.contains('open');
    menusCloseAll(false, menu);
    menu.__yozoraTrigger = opener;
    menu.classList.toggle('open', open);
    opener.setAttribute('aria-expanded', String(open));
    if (open) {
      positionMenu(menu);
      if (menu.getAttribute('role') === 'menu') menuItems(menu)[0]?.focus();
    }
    return;
  }
  if (!event.target.closest?.('.anchor .menu')) menusCloseAll(false);

  const modalOpener = event.target.closest && event.target.closest('[data-modal-open]');
  if (modalOpener) {
    const modal = document.getElementById(modalOpener.dataset.modalOpen);
    if (modal) modalOpen(modal, modalOpener);
    return;
  }
  const modalCloser = event.target.closest && event.target.closest('[data-modal-close]');
  if (modalCloser) {
    event.preventDefault();
    modalClose(modalCloser.closest('[data-modal], .scrim-modal, [data-confirm-dialog]'));
    return;
  }
  const scrim = event.target.closest && event.target.closest('[data-modal], .scrim-modal, [data-confirm-dialog]');
  if (scrim && event.target === scrim) modalClose(scrim);
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    const modal = [...document.querySelectorAll('[data-modal], .scrim-modal, [data-confirm-dialog]')]
      .find((item) => !item.hidden);
    if (modal) modalClose(modal);
    menusCloseAll(true);
    return;
  }
  if (event.key === 'Tab') {
    const modal = event.target.closest && event.target.closest('[data-modal], .scrim-modal, [data-confirm-dialog]');
    if (!modal || modal.hidden) return;
    const items = focusable(modal);
    if (!items.length) return;
    const index = items.indexOf(document.activeElement);
    const next = items[(index + (event.shiftKey ? -1 : 1) + items.length) % items.length];
    if (index === -1 || (event.shiftKey && index === 0) || (!event.shiftKey && index === items.length - 1)) {
      event.preventDefault();
      next.focus();
    }
  }
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    const menu = event.target.closest && event.target.closest('.anchor .menu.open');
    if (!menu) return;
    const items = menuItems(menu);
    const index = items.indexOf(document.activeElement);
    if (!items.length) return;
    event.preventDefault();
    items[(index + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length].focus();
  }
});

document.addEventListener('input', (event) => {
  const form = event.target.closest && event.target.closest('[data-confirm-value]');
  if (form) syncConfirm(form);
});
document.querySelectorAll('[data-confirm-value]').forEach(syncConfirm);
refreshModalLock();

document.body.addEventListener('htmx:load', (event) => {
  const root = event.detail && event.detail.elt ? event.detail.elt : document;
  root.querySelectorAll?.('[data-confirm-value]').forEach(syncConfirm);
});

// HTMX's native confirmation hook is rendered as the same accessible modal as
// explicit data-modal controls. The request is only issued after confirmation.
document.body.addEventListener('htmx:confirm', (event) => {
  const question = event.detail && event.detail.question;
  const issueRequest = event.detail && event.detail.issueRequest;
  if (!question || typeof issueRequest !== 'function') return;
  event.preventDefault();
  const scrim = document.createElement('div');
  scrim.className = 'scrim-modal';
  scrim.setAttribute('data-confirm-dialog', 'true');
  scrim.setAttribute('role', 'presentation');
  const modal = document.createElement('div');
  modal.className = 'modal';
  modal.setAttribute('role', 'dialog');
  modal.setAttribute('aria-modal', 'true');
  const title = document.createElement('h2');
  title.textContent = 'Confirm action';
  const copy = document.createElement('p');
  copy.textContent = question;
  const foot = document.createElement('div');
  foot.className = 'foot';
  const cancel = document.createElement('button');
  cancel.className = 'btn ghost';
  cancel.type = 'button';
  cancel.textContent = 'Cancel';
  const confirm = document.createElement('button');
  confirm.className = /delete|purge|archive|revoke/i.test(question) ? 'btn destructive' : 'btn secondary';
  confirm.type = 'button';
  confirm.textContent = 'Continue';
  foot.append(cancel, confirm);
  modal.append(title, copy, foot);
  scrim.appendChild(modal);
  document.body.appendChild(scrim);
  modalOpen(scrim, event.target);
  cancel.addEventListener('click', () => modalClose(scrim));
  confirm.addEventListener('click', () => {
    modalClose(scrim);
    issueRequest(true);
  });
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
    toast('information', 'Copied to clipboard');
  }).catch(() => {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    toast('information', 'Copied to clipboard');
  });
});

// ── Save Indicator ──────────────────────────────

document.body.addEventListener('htmx:afterSwap', (event) => {
  const indicator = document.querySelector('[data-save-indicator]');
  if (!indicator) return;

  const target = event.detail.target;
  // Only a questionnaire save counts; loading a section or other posts are not a save.
  const config = event.detail.requestConfig;
  const path = config && config.path ? config.path.split('?')[0] : '';
  const isSave = path.endsWith('/questionnaire/save');
  if (isSave && target && (target.id === 'section-content' || target.closest('[data-questionnaire-form]'))) {
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
          window.location.href = '/engagements/new';
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
