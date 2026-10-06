(() => {
  const root = document.documentElement;
  const params = new URLSearchParams(window.location.search);
  if (params.has('dark')) root.dataset.theme = 'dark';
  root.classList.remove('no-js');

  document.querySelectorAll('[data-upload-form]').forEach((form) => {
    const input = form.querySelector('[data-upload-input]');
    if (!input) return;
    input.addEventListener('change', () => {
      if (input.files.length) form.requestSubmit();
    });
  });
})();
