(function (global) {
  const cfg = global.APP_CONFIG;

  function getState() {
    const raw = localStorage.getItem(cfg.storageKey);
    const parsed = raw ? JSON.parse(raw) : {};
    return {
      demoMode: parsed.demoMode != null ? parsed.demoMode : cfg.defaultDemoMode,
      apiBase: parsed.apiBase || cfg.defaultApiBase,
      access: parsed.access || null,
      refresh: parsed.refresh || null,
      username: parsed.username || null,
    };
  }

  function setState(patch) {
    const next = { ...getState(), ...patch };
    localStorage.setItem(cfg.storageKey, JSON.stringify(next));
    return next;
  }

  function clearSession() {
    return setState({ access: null, refresh: null, username: null });
  }

  async function request(method, path, { json, formData, auth = true } = {}) {
    const state = getState();
    const headers = new Headers();
    if (auth && state.access) headers.set('Authorization', `Bearer ${state.access}`);

    if (state.demoMode) {
      const result = await global.DemoStore.handle(method, path, {
        headers,
        body: json,
        formData,
      });
      if (result.status >= 400) {
        const err = new Error('Request failed');
        err.status = result.status;
        err.data = result.data;
        throw err;
      }
      return result.data;
    }

    const base = state.apiBase.replace(/\/+$/, '');
    const url = path.startsWith('http') ? path : `${base}${path.startsWith('/') ? '' : '/'}${path}`;
    const opts = { method, headers };
    if (formData) {
      opts.body = formData;
    } else if (json != null) {
      headers.set('Content-Type', 'application/json');
      opts.body = JSON.stringify(json);
    }

    let res = await fetch(url, opts);
    if (res.status === 401 && auth && state.refresh && !path.includes('/auth/token')) {
      try {
        const refreshed = await request('POST', '/auth/token/refresh/', {
          json: { refresh: state.refresh },
          auth: false,
        });
        setState({ access: refreshed.access });
        headers.set('Authorization', `Bearer ${refreshed.access}`);
        res = await fetch(url, opts);
      } catch (_) {
        clearSession();
      }
    }

    if (res.status === 204) return null;
    let data = null;
    const text = await res.text();
    if (text) {
      try {
        data = JSON.parse(text);
      } catch (_) {
        data = { detail: text };
      }
    }
    if (!res.ok) {
      const err = new Error('Request failed');
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  }

  global.API = {
    getState,
    setState,
    clearSession,
    request,
    register: (payload) => request('POST', '/auth/register/', { json: payload, auth: false }),
    login: (payload) => request('POST', '/auth/token/', { json: payload, auth: false }),
    health: () => request('GET', '/health/', { auth: false }),
    listCategories: () => request('GET', '/categories/'),
    createCategory: (payload) => request('POST', '/categories/', { json: payload }),
    updateCategory: (id, payload) => request('PATCH', `/categories/${id}/`, { json: payload }),
    deleteCategory: (id) => request('DELETE', `/categories/${id}/`),
    listExpenses: (query = '') => request('GET', `/expenses/${query}`),
    createExpense: (payload, formData) =>
      formData
        ? request('POST', '/expenses/', { formData })
        : request('POST', '/expenses/', { json: payload }),
    updateExpense: (id, payload, formData) =>
      formData
        ? request('PATCH', `/expenses/${id}/`, { formData })
        : request('PATCH', `/expenses/${id}/`, { json: payload }),
    deleteExpense: (id) => request('DELETE', `/expenses/${id}/`),
    total: (query = '') => request('GET', `/expenses/total/${query}`),
    summary: (query = '') => request('GET', `/expenses/summary/${query}`),
    listBudgets: (query = '') => request('GET', `/budgets/${query}`),
    createBudget: (payload) => request('POST', '/budgets/', { json: payload }),
    updateBudget: (id, payload) => request('PATCH', `/budgets/${id}/`, { json: payload }),
    deleteBudget: (id) => request('DELETE', `/budgets/${id}/`),
  };
})(window);
