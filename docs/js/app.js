(function () {
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  function toast(message, isError = false) {
    const el = $('#toast');
    el.textContent = message;
    el.classList.toggle('error', isError);
    el.classList.remove('hidden');
    clearTimeout(toast._t);
    toast._t = setTimeout(() => el.classList.add('hidden'), 3200);
  }

  function errMsg(err) {
    if (!err || !err.data) return err?.message || 'Something went wrong';
    const d = err.data;
    if (typeof d.detail === 'string') return d.detail;
    if (Array.isArray(d.detail)) return d.detail.map((x) => x.msg || JSON.stringify(x)).join('; ');
    return Object.entries(d)
      .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
      .join('; ');
  }

  function qsFromForm(form) {
    const data = new FormData(form);
    const params = new URLSearchParams();
    for (const [k, v] of data.entries()) {
      if (String(v).trim()) params.set(k, String(v).trim());
    }
    const s = params.toString();
    return s ? `?${s}` : '';
  }

  function money(amount, currency = 'USD') {
    const n = Number(amount);
    try {
      return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(n);
    } catch (_) {
      return `${currency} ${n.toFixed(2)}`;
    }
  }

  async function fillCategorySelects(selected) {
    const cats = await API.listCategories();
    const options = cats
      .map((c) => `<option value="${c.slug}">${c.name}${c.is_system ? '' : ' (custom)'}</option>`)
      .join('');
    $$('select[name="category"]').forEach((sel) => {
      const keepAll = sel.closest('form')?.id === 'expenseFilters' || sel.closest('form')?.id === 'reportFilters';
      sel.innerHTML = (keepAll ? '<option value="">All</option>' : '') + options;
      if (selected) sel.value = selected;
    });
  }

  function showAuth(show) {
    $('#authView').classList.toggle('hidden', !show);
    $('#appView').classList.toggle('hidden', show);
    $('#logoutBtn').classList.toggle('hidden', show);
  }

  function setView(name) {
    $$('.pill').forEach((p) => p.classList.toggle('active', p.dataset.view === name));
    $$('.view').forEach((v) => v.classList.toggle('hidden', v.id !== `view-${name}`));
    if (name === 'dashboard') refreshDashboard();
    if (name === 'expenses') refreshExpenses();
    if (name === 'categories') refreshCategories();
    if (name === 'budgets') refreshBudgets();
    if (name === 'reports') refreshReports();
  }

  async function refreshDashboard() {
    try {
      const [expenses, total, summary, budgets, categories] = await Promise.all([
        API.listExpenses(),
        API.total(),
        API.summary(),
        API.listBudgets(),
        API.listCategories(),
      ]);
      const results = expenses.results || expenses;
      $('#dashCount').textContent = String(expenses.count ?? results.length);
      $('#dashBudgets').textContent = String(budgets.count ?? (budgets.results || budgets).length);
      $('#dashCategories').textContent = String(categories.length);

      if (total.by_currency) {
        $('#dashTotal').textContent = total.by_currency
          .map((x) => money(x.total, x.currency))
          .join(' · ');
      } else {
        $('#dashTotal').textContent = money(total.total_expenses || 0, total.currency || 'USD');
      }

      $('#dashRecent').innerHTML = results.slice(0, 6).map((e) => `
        <li>
          <span><strong>${e.category_name}</strong><br /><small>${e.description || e.timestamp.slice(0, 10)}</small></span>
          <span>${money(e.amount, e.currency)}</span>
        </li>
      `).join('') || '<li>No expenses yet</li>';

      const rows = summary.by_category ||
        (summary.by_currency || []).flatMap((g) =>
          (g.by_category || []).map((r) => ({ ...r, currency: g.currency }))
        );
      $('#dashSummary').innerHTML = (rows || []).slice(0, 8).map((r) => `
        <li>
          <span>${r.category_name}</span>
          <span>${money(r.total, r.currency || summary.currency || 'USD')} · ${r.count}</span>
        </li>
      `).join('') || '<li>No summary data</li>';
    } catch (err) {
      toast(errMsg(err), true);
    }
  }

  async function refreshExpenses() {
    try {
      await fillCategorySelects();
      const q = qsFromForm($('#expenseFilters'));
      const data = await API.listExpenses(q);
      const rows = data.results || data;
      $('#expenseList').innerHTML = `
        <table>
          <thead>
            <tr>
              <th>When</th><th>Category</th><th>Amount</th><th>Description</th><th>Receipt</th><th></th>
            </tr>
          </thead>
          <tbody>
            ${rows.map((e) => `
              <tr>
                <td>${e.timestamp.slice(0, 10)}</td>
                <td>${e.category_name}</td>
                <td>${money(e.amount, e.currency)}</td>
                <td>${e.description || '—'}</td>
                <td>${e.receipt ? 'Yes' : '—'}</td>
                <td class="row-actions">
                  <button type="button" class="btn ghost" data-edit-expense="${e.id}">Edit</button>
                  <button type="button" class="btn danger" data-del-expense="${e.id}">Delete</button>
                </td>
              </tr>
            `).join('') || '<tr><td colspan="6">No expenses match these filters.</td></tr>'}
          </tbody>
        </table>
      `;
      window.__expensesCache = rows;
    } catch (err) {
      toast(errMsg(err), true);
    }
  }

  async function refreshCategories() {
    try {
      const cats = await API.listCategories();
      $('#categoryList').innerHTML = `
        <table>
          <thead><tr><th>Name</th><th>Slug</th><th>Type</th><th></th></tr></thead>
          <tbody>
            ${cats.map((c) => `
              <tr>
                <td>${c.name}</td>
                <td><code>${c.slug}</code></td>
                <td>${c.is_system ? 'System' : 'Custom'}</td>
                <td class="row-actions">
                  ${c.is_system ? '—' : `
                    <button type="button" class="btn ghost" data-edit-category='${JSON.stringify(c)}'>Edit</button>
                    <button type="button" class="btn danger" data-del-category="${c.id}">Delete</button>
                  `}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    } catch (err) {
      toast(errMsg(err), true);
    }
  }

  async function refreshBudgets() {
    try {
      await fillCategorySelects();
      const data = await API.listBudgets();
      const rows = data.results || data;
      window.__budgetsCache = rows;
      $('#budgetList').innerHTML = `
        <table>
          <thead>
            <tr><th>Category</th><th>Period</th><th>Budget</th><th>Spent</th><th>Remaining</th><th></th></tr>
          </thead>
          <tbody>
            ${rows.map((b) => {
              const pct = Math.min(100, Math.round((Number(b.spent) / Number(b.amount)) * 100)) || 0;
              return `
              <tr>
                <td>${b.category_name}</td>
                <td>${b.period}<br /><small>${b.period_start} → ${b.period_end}</small></td>
                <td>${money(b.amount)}</td>
                <td>${money(b.spent)}
                  <div class="progress"><span style="width:${pct}%"></span></div>
                </td>
                <td>${money(b.remaining)}</td>
                <td class="row-actions">
                  <button type="button" class="btn ghost" data-edit-budget="${b.id}">Edit</button>
                  <button type="button" class="btn danger" data-del-budget="${b.id}">Delete</button>
                </td>
              </tr>`;
            }).join('') || '<tr><td colspan="6">No budgets yet.</td></tr>'}
          </tbody>
        </table>
      `;
    } catch (err) {
      toast(errMsg(err), true);
    }
  }

  async function refreshReports() {
    try {
      await fillCategorySelects();
      const q = qsFromForm($('#reportFilters'));
      const [total, summary] = await Promise.all([API.total(q), API.summary(q)]);
      $('#reportTotal').textContent = JSON.stringify(total, null, 2);
      $('#reportSummary').textContent = JSON.stringify(summary, null, 2);
    } catch (err) {
      toast(errMsg(err), true);
    }
  }

  function openExpenseDialog(expense) {
    const form = $('#expenseForm');
    form.reset();
    form.id.value = expense?.id || '';
    $('#expenseDialogTitle').textContent = expense ? 'Edit expense' : 'Add expense';
    fillCategorySelects(expense?.category).then(() => {
      if (expense) {
        form.amount.value = expense.amount;
        form.currency.value = expense.currency;
        form.description.value = expense.description || '';
      }
      $('#expenseDialog').showModal();
    });
  }

  function openBudgetDialog(budget) {
    const form = $('#budgetForm');
    form.reset();
    form.id.value = budget?.id || '';
    $('#budgetDialogTitle').textContent = budget ? 'Edit budget' : 'Add budget';
    fillCategorySelects(budget?.category).then(() => {
      if (budget) {
        form.amount.value = budget.amount;
        form.period.value = budget.period;
      }
      $('#budgetDialog').showModal();
    });
  }

  function syncModeUI() {
    const state = API.getState();
    $('#demoMode').checked = !!state.demoMode;
    $('#authHint').textContent = state.demoMode
      ? 'Demo mode is on — try username demo / demopass1, or register a new account (stored in this browser).'
      : `Live API mode — talking to ${state.apiBase}`;
    $('#settingsForm').apiBase.value = state.apiBase;
  }

  async function boot() {
    syncModeUI();
    const state = API.getState();
    if (state.access) {
      showAuth(false);
      setView('dashboard');
    } else {
      showAuth(true);
    }
  }

  // Auth tabs
  $$('[data-auth-tab]').forEach((btn) => {
    btn.addEventListener('click', () => {
      $$('[data-auth-tab]').forEach((b) => b.classList.toggle('active', b === btn));
      $('#loginForm').classList.toggle('hidden', btn.dataset.authTab !== 'login');
      $('#registerForm').classList.toggle('hidden', btn.dataset.authTab !== 'register');
    });
  });

  $('#loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      const tokens = await API.login({
        username: fd.get('username'),
        password: fd.get('password'),
      });
      API.setState({
        access: tokens.access,
        refresh: tokens.refresh,
        username: fd.get('username'),
      });
      toast('Signed in');
      showAuth(false);
      setView('dashboard');
    } catch (err) {
      toast(errMsg(err), true);
    }
  });

  $('#registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await API.register({
        username: fd.get('username'),
        email: fd.get('email') || '',
        password: fd.get('password'),
      });
      const tokens = await API.login({
        username: fd.get('username'),
        password: fd.get('password'),
      });
      API.setState({
        access: tokens.access,
        refresh: tokens.refresh,
        username: fd.get('username'),
      });
      toast('Account created');
      showAuth(false);
      setView('dashboard');
    } catch (err) {
      toast(errMsg(err), true);
    }
  });

  $('#logoutBtn').addEventListener('click', () => {
    API.clearSession();
    showAuth(true);
    toast('Logged out');
  });

  $('#demoMode').addEventListener('change', (e) => {
    API.setState({ demoMode: e.target.checked });
    API.clearSession();
    syncModeUI();
    showAuth(true);
    toast(e.target.checked ? 'Demo mode enabled' : 'Live API mode enabled');
  });

  $('#settingsBtn').addEventListener('click', () => {
    syncModeUI();
    $('#settingsDialog').showModal();
  });
  $('#closeSettings').addEventListener('click', () => $('#settingsDialog').close());
  $('#settingsForm').addEventListener('submit', (e) => {
    e.preventDefault();
    API.setState({ apiBase: e.target.apiBase.value.trim() || APP_CONFIG.defaultApiBase });
    $('#settingsDialog').close();
    syncModeUI();
    toast('Settings saved');
  });

  $$('.pill').forEach((btn) => btn.addEventListener('click', () => setView(btn.dataset.view)));

  $('#expenseFilters').addEventListener('submit', (e) => {
    e.preventDefault();
    refreshExpenses();
  });
  $('#reportFilters').addEventListener('submit', (e) => {
    e.preventDefault();
    refreshReports();
  });

  $('#addExpenseBtn').addEventListener('click', () => openExpenseDialog(null));
  $('#addBudgetBtn').addEventListener('click', () => openBudgetDialog(null));

  $$('[data-close]').forEach((btn) => {
    btn.addEventListener('click', () => document.getElementById(btn.dataset.close).close());
  });

  $('#expenseForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const id = form.id.value;
    const file = form.receipt.files[0];
    try {
      if (file) {
        const fd = new FormData(form);
        fd.delete('id');
        if (id) await API.updateExpense(id, null, fd);
        else await API.createExpense(null, fd);
      } else {
        const payload = {
          category: form.category.value,
          amount: form.amount.value,
          currency: form.currency.value,
          description: form.description.value,
        };
        if (id) await API.updateExpense(id, payload);
        else await API.createExpense(payload);
      }
      $('#expenseDialog').close();
      toast(id ? 'Expense updated' : 'Expense created');
      refreshExpenses();
      refreshDashboard();
    } catch (err) {
      toast(errMsg(err), true);
    }
  });

  $('#budgetForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const id = form.id.value;
    const payload = {
      category: form.category.value,
      amount: form.amount.value,
      period: form.period.value,
    };
    try {
      if (id) await API.updateBudget(id, payload);
      else await API.createBudget(payload);
      $('#budgetDialog').close();
      toast(id ? 'Budget updated' : 'Budget created');
      refreshBudgets();
      refreshDashboard();
    } catch (err) {
      toast(errMsg(err), true);
    }
  });

  $('#categoryForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const payload = { name: fd.get('name') };
    if (fd.get('slug')) payload.slug = fd.get('slug');
    try {
      await API.createCategory(payload);
      e.target.reset();
      toast('Category created');
      refreshCategories();
    } catch (err) {
      toast(errMsg(err), true);
    }
  });

  document.addEventListener('click', async (e) => {
    const delE = e.target.closest('[data-del-expense]');
    if (delE) {
      if (!confirm('Delete this expense?')) return;
      try {
        await API.deleteExpense(delE.dataset.delExpense);
        toast('Expense deleted');
        refreshExpenses();
        refreshDashboard();
      } catch (err) {
        toast(errMsg(err), true);
      }
    }
    const editE = e.target.closest('[data-edit-expense]');
    if (editE) {
      const exp = (window.__expensesCache || []).find((x) => String(x.id) === editE.dataset.editExpense);
      if (exp) openExpenseDialog(exp);
    }
    const delC = e.target.closest('[data-del-category]');
    if (delC) {
      if (!confirm('Delete this category?')) return;
      try {
        await API.deleteCategory(delC.dataset.delCategory);
        toast('Category deleted');
        refreshCategories();
      } catch (err) {
        toast(errMsg(err), true);
      }
    }
    const editC = e.target.closest('[data-edit-category]');
    if (editC) {
      const cat = JSON.parse(editC.dataset.editCategory);
      const name = prompt('Category name', cat.name);
      if (!name) return;
      try {
        await API.updateCategory(cat.id, { name });
        toast('Category updated');
        refreshCategories();
      } catch (err) {
        toast(errMsg(err), true);
      }
    }
    const delB = e.target.closest('[data-del-budget]');
    if (delB) {
      if (!confirm('Delete this budget?')) return;
      try {
        await API.deleteBudget(delB.dataset.delBudget);
        toast('Budget deleted');
        refreshBudgets();
        refreshDashboard();
      } catch (err) {
        toast(errMsg(err), true);
      }
    }
    const editB = e.target.closest('[data-edit-budget]');
    if (editB) {
      const b = (window.__budgetsCache || []).find((x) => String(x.id) === editB.dataset.editBudget);
      if (b) openBudgetDialog(b);
    }
  });

  boot();
})();
