// CyberAssess — HTMX config + upload handling

// HTMX configuration
document.body.addEventListener('htmx:configRequest', function(event) {
  // Add CSRF or other headers if needed later
});

// HTMX-aware redirects (e.g., auth redirect on 401)
document.body.addEventListener('htmx:responseError', function(event) {
  if (event.detail.xhr.status === 401) {
    window.location.href = '/login';
  }
});

// Handle HX-Redirect header
document.body.addEventListener('htmx:beforeSwap', function(event) {
  if (event.detail.xhr.status === 401) {
    window.location.href = '/login';
    event.detail.shouldSwap = false;
  }
});

// Upload drop zone handling
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

// Upload progress handler
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
