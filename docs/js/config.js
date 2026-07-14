window.APP_CONFIG = {
  storageKey: 'expenseTrackerDemo',
  defaultApiBase: 'http://127.0.0.1:8000/api',
  // On GitHub Pages, default to demo mode so the UI is fully usable without a hosted API.
  defaultDemoMode: /github\.io$/i.test(location.hostname) || location.protocol === 'file:',
};
