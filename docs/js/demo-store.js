(function (global) {
  const KEY = 'expenseTracker.demo.v1';

  function todayISO() {
    return new Date().toISOString();
  }

  function periodBounds(period, now = new Date()) {
    const d = new Date(now);
    let start;
    let end;
    if (period === 'weekly') {
      const day = (d.getDay() + 6) % 7; // Monday=0
      start = new Date(d);
      start.setHours(0, 0, 0, 0);
      start.setDate(d.getDate() - day);
      end = new Date(start);
      end.setDate(start.getDate() + 6);
      end.setHours(23, 59, 59, 999);
    } else if (period === 'yearly') {
      start = new Date(d.getFullYear(), 0, 1);
      end = new Date(d.getFullYear(), 11, 31, 23, 59, 59, 999);
    } else {
      start = new Date(d.getFullYear(), d.getMonth(), 1);
      end = new Date(d.getFullYear(), d.getMonth() + 1, 0, 23, 59, 59, 999);
    }
    return {
      period_start: start.toISOString().slice(0, 10),
      period_end: end.toISOString().slice(0, 10),
      start,
      end,
    };
  }

  function load() {
    const raw = localStorage.getItem(KEY);
    if (raw) return JSON.parse(raw);
    const seed = {
      users: [{ id: 1, username: 'demo', email: 'demo@example.com', password: 'demopass1' }],
      nextIds: { user: 2, category: 5, expense: 1, budget: 1 },
      categories: [
        { id: 1, slug: 'food', name: 'Food', is_system: true, user: null, created_at: todayISO() },
        { id: 2, slug: 'transport', name: 'Transport', is_system: true, user: null, created_at: todayISO() },
        { id: 3, slug: 'entertainment', name: 'Entertainment', is_system: true, user: null, created_at: todayISO() },
        { id: 4, slug: 'other', name: 'Other', is_system: true, user: null, created_at: todayISO() },
      ],
      expenses: [],
      budgets: [],
      sessions: {},
    };
    save(seed);
    return seed;
  }

  function save(db) {
    localStorage.setItem(KEY, JSON.stringify(db));
  }

  function slugify(name) {
    return String(name)
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
  }

  function token() {
    return 'demo-' + Math.random().toString(36).slice(2) + Date.now().toString(36);
  }

  function parseQuery(url) {
    const u = new URL(url, 'http://local');
    return Object.fromEntries(u.searchParams.entries());
  }

  function matchPath(pathname, pattern) {
    const pp = pattern.replace(/\{(\w+)\}/g, '([^/]+)');
    const re = new RegExp('^' + pp + '$');
    const m = pathname.match(re);
    if (!m) return null;
    const keys = [...pattern.matchAll(/\{(\w+)\}/g)].map((x) => x[1]);
    const params = {};
    keys.forEach((k, i) => {
      params[k] = m[i + 1];
    });
    return params;
  }

  function authUser(db, headers) {
    const h = headers.get ? headers.get('Authorization') : headers.Authorization;
    if (!h || !h.startsWith('Bearer ')) return null;
    const t = h.slice(7);
    const userId = db.sessions[t];
    return db.users.find((u) => u.id === userId) || null;
  }

  function visibleCategories(db, user) {
    return db.categories.filter((c) => c.user == null || c.user === user.id);
  }

  function findCategory(db, user, slug) {
    return visibleCategories(db, user).find((c) => c.slug === slug);
  }

  function filterExpenses(db, user, query) {
    let items = db.expenses.filter((e) => e.user === user.id);
    if (query.category) items = items.filter((e) => e.category === query.category);
    if (query.currency) items = items.filter((e) => e.currency === query.currency.toUpperCase());
    if (query.start_date) {
      const start = new Date(query.start_date + 'T00:00:00');
      items = items.filter((e) => new Date(e.timestamp) >= start);
    }
    if (query.end_date) {
      const end = new Date(query.end_date + 'T23:59:59.999');
      items = items.filter((e) => new Date(e.timestamp) <= end);
    }
    return items.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  }

  function expenseOut(db, e) {
    const cat = db.categories.find((c) => c.slug === e.category);
    const user = db.users.find((u) => u.id === e.user);
    return {
      id: e.id,
      username: user ? user.username : '',
      category: e.category,
      category_name: cat ? cat.name : e.category,
      amount: e.amount,
      currency: e.currency,
      description: e.description || '',
      receipt: e.receipt || null,
      timestamp: e.timestamp,
    };
  }

  function budgetUsage(db, budget) {
    const bounds = periodBounds(budget.period);
    const spent = db.expenses
      .filter(
        (e) =>
          e.user === budget.user &&
          e.category === budget.category &&
          new Date(e.timestamp) >= bounds.start &&
          new Date(e.timestamp) <= bounds.end
      )
      .reduce((sum, e) => sum + Number(e.amount), 0);
    const amount = Number(budget.amount);
    return {
      spent: spent.toFixed(2),
      remaining: (amount - spent).toFixed(2),
      period_start: bounds.period_start,
      period_end: bounds.period_end,
    };
  }

  function budgetOut(db, b) {
    const cat = db.categories.find((c) => c.slug === b.category);
    const usage = budgetUsage(db, b);
    return {
      id: b.id,
      category: b.category,
      category_name: cat ? cat.name : b.category,
      amount: b.amount,
      period: b.period,
      ...usage,
      created_at: b.created_at,
      updated_at: b.updated_at,
    };
  }

  async function handle(method, pathWithQuery, { headers, body, formData } = {}) {
    const db = load();
    const url = new URL(pathWithQuery, 'http://demo.local');
    let path = url.pathname.replace(/\/+$/, '') || '/';
    if (!path.startsWith('/')) path = '/' + path;
    // normalize /api prefix optional
    if (path.startsWith('/api/')) path = path.slice(4);
    if (path === '/api') path = '/';

    const query = Object.fromEntries(url.searchParams.entries());
    const jsonBody = formData
      ? Object.fromEntries([...formData.entries()].filter(([k]) => k !== 'receipt'))
      : body;

    const respond = (status, data) => ({ status, data });

    if (path === '/health' && method === 'GET') {
      return respond(200, { status: 'ok' });
    }

    if (path === '/auth/register/' || path === '/auth/register') {
      if (method !== 'POST') return respond(405, { detail: 'Method not allowed' });
      const { username, email = '', password } = jsonBody || {};
      if (!username || !password || String(password).length < 8) {
        return respond(400, { detail: 'Invalid registration data' });
      }
      if (db.users.some((u) => u.username === username)) {
        return respond(400, { username: ['A user with that username already exists.'] });
      }
      const user = {
        id: db.nextIds.user++,
        username,
        email,
        password: String(password),
      };
      db.users.push(user);
      save(db);
      return respond(201, { id: user.id, username, email });
    }

    if (path === '/auth/token/' || path === '/auth/token') {
      if (method !== 'POST') return respond(405, { detail: 'Method not allowed' });
      const { username, password } = jsonBody || {};
      const user = db.users.find((u) => u.username === username && u.password === password);
      if (!user) return respond(401, { detail: 'No active account found with the given credentials' });
      const access = token();
      const refresh = token();
      db.sessions[access] = user.id;
      db.sessions[refresh] = user.id;
      save(db);
      return respond(200, { access, refresh });
    }

    if (path === '/auth/token/refresh/' || path === '/auth/token/refresh') {
      if (method !== 'POST') return respond(405, { detail: 'Method not allowed' });
      const { refresh } = jsonBody || {};
      const userId = db.sessions[refresh];
      if (!userId) return respond(401, { detail: 'Token is invalid or expired' });
      const access = token();
      db.sessions[access] = userId;
      save(db);
      return respond(200, { access });
    }

    const user = authUser(db, headers || new Headers());
    if (!user) return respond(401, { detail: 'Authentication credentials were not provided.' });

    // Categories list/create
    if (path === '/categories' || path === '/categories/') {
      if (method === 'GET') {
        return respond(
          200,
          visibleCategories(db, user).map((c) => ({
            id: c.id,
            slug: c.slug,
            name: c.name,
            is_system: !!c.is_system,
            created_at: c.created_at,
          }))
        );
      }
      if (method === 'POST') {
        const name = (jsonBody && jsonBody.name) || '';
        const slug = (jsonBody && jsonBody.slug) || slugify(name);
        if (!name) return respond(400, { name: ['This field is required.'] });
        if (db.categories.some((c) => c.user == null && c.slug === slug)) {
          return respond(400, { slug: ['This slug is reserved by a system category.'] });
        }
        if (db.categories.some((c) => c.user === user.id && c.slug === slug)) {
          return respond(400, { slug: ['You already have a category with this slug.'] });
        }
        const cat = {
          id: db.nextIds.category++,
          slug,
          name,
          is_system: false,
          user: user.id,
          created_at: todayISO(),
        };
        db.categories.push(cat);
        save(db);
        return respond(201, {
          id: cat.id,
          slug: cat.slug,
          name: cat.name,
          is_system: false,
          created_at: cat.created_at,
        });
      }
    }

    const catDetail = matchPath(path, '/categories/{id}') || matchPath(path, '/categories/{id}/');
    if (catDetail) {
      const id = Number(catDetail.id);
      const cat = db.categories.find((c) => c.id === id);
      if (!cat || (cat.user != null && cat.user !== user.id)) return respond(404, { detail: 'Not found.' });
      if (method === 'GET') {
        return respond(200, {
          id: cat.id,
          slug: cat.slug,
          name: cat.name,
          is_system: !!cat.is_system,
          created_at: cat.created_at,
        });
      }
      if (method === 'PUT' || method === 'PATCH') {
        if (cat.is_system || cat.user == null) return respond(403, { detail: 'System categories are read-only.' });
        if (jsonBody.name) cat.name = jsonBody.name;
        if (jsonBody.slug) cat.slug = jsonBody.slug;
        save(db);
        return respond(200, {
          id: cat.id,
          slug: cat.slug,
          name: cat.name,
          is_system: false,
          created_at: cat.created_at,
        });
      }
      if (method === 'DELETE') {
        if (cat.is_system || cat.user == null) return respond(403, { detail: 'System categories are read-only.' });
        if (db.expenses.some((e) => e.user === user.id && e.category === cat.slug)) {
          return respond(400, { detail: 'Category is in use by expenses.' });
        }
        db.categories = db.categories.filter((c) => c.id !== id);
        save(db);
        return respond(204, null);
      }
    }

    if (path === '/expenses' || path === '/expenses/') {
      if (method === 'GET') {
        const items = filterExpenses(db, user, query).map((e) => expenseOut(db, e));
        return respond(200, { count: items.length, next: null, previous: null, results: items });
      }
      if (method === 'POST') {
        const category = jsonBody.category;
        const amount = jsonBody.amount;
        const currency = (jsonBody.currency || 'USD').toUpperCase();
        if (!findCategory(db, user, category)) return respond(400, { category: ['Invalid category slug.'] });
        if (!(Number(amount) > 0)) return respond(400, { amount: ['Amount must be greater than zero.'] });
        if (!/^[A-Z]{3}$/.test(currency)) {
          return respond(400, { currency: ['Currency must be a 3-letter uppercase ISO 4217 code.'] });
        }
        let receipt = null;
        if (formData && formData.get('receipt') && formData.get('receipt').name) {
          receipt = 'demo://receipt/' + formData.get('receipt').name;
        }
        const exp = {
          id: db.nextIds.expense++,
          user: user.id,
          category,
          amount: Number(amount).toFixed(2),
          currency,
          description: jsonBody.description || '',
          receipt,
          timestamp: todayISO(),
        };
        db.expenses.push(exp);
        save(db);
        return respond(201, expenseOut(db, exp));
      }
    }

    if (path === '/expenses/total' || path === '/expenses/total/') {
      const items = filterExpenses(db, user, query);
      const byCurrency = {};
      items.forEach((e) => {
        byCurrency[e.currency] = (byCurrency[e.currency] || 0) + Number(e.amount);
      });
      const currencies = Object.keys(byCurrency);
      if (currencies.length <= 1) {
        const currency = currencies[0] || query.currency || 'USD';
        return respond(200, {
          total_expenses: Number((byCurrency[currency] || 0).toFixed(2)),
          currency,
        });
      }
      return respond(200, {
        by_currency: currencies.map((c) => ({ currency: c, total: Number(byCurrency[c].toFixed(2)) })),
      });
    }

    if (path === '/expenses/summary' || path === '/expenses/summary/') {
      const items = filterExpenses(db, user, query);
      const group = {};
      items.forEach((e) => {
        const key = e.currency + '|' + e.category;
        if (!group[key]) {
          group[key] = { currency: e.currency, category: e.category, total: 0, count: 0 };
        }
        group[key].total += Number(e.amount);
        group[key].count += 1;
      });
      const rows = Object.values(group).map((r) => {
        const cat = db.categories.find((c) => c.slug === r.category);
        return {
          currency: r.currency,
          category: r.category,
          category_name: cat ? cat.name : r.category,
          total: Number(r.total.toFixed(2)),
          count: r.count,
        };
      });
      const currencies = [...new Set(rows.map((r) => r.currency))];
      if (currencies.length <= 1) {
        return respond(200, {
          currency: currencies[0] || query.currency || 'USD',
          by_category: rows.map(({ category, category_name, total, count }) => ({
            category,
            category_name,
            total,
            count,
          })),
        });
      }
      return respond(200, {
        by_currency: currencies.map((currency) => ({
          currency,
          by_category: rows
            .filter((r) => r.currency === currency)
            .map(({ category, category_name, total, count }) => ({
              category,
              category_name,
              total,
              count,
            })),
        })),
      });
    }

    const expDetail = matchPath(path, '/expenses/{id}') || matchPath(path, '/expenses/{id}/');
    if (expDetail) {
      const id = Number(expDetail.id);
      const exp = db.expenses.find((e) => e.id === id && e.user === user.id);
      if (!exp) return respond(404, { detail: 'Not found.' });
      if (method === 'GET') return respond(200, expenseOut(db, exp));
      if (method === 'PUT' || method === 'PATCH') {
        if (jsonBody.category) {
          if (!findCategory(db, user, jsonBody.category)) {
            return respond(400, { category: ['Invalid category slug.'] });
          }
          exp.category = jsonBody.category;
        }
        if (jsonBody.amount != null) {
          if (!(Number(jsonBody.amount) > 0)) {
            return respond(400, { amount: ['Amount must be greater than zero.'] });
          }
          exp.amount = Number(jsonBody.amount).toFixed(2);
        }
        if (jsonBody.currency) {
          const currency = String(jsonBody.currency).toUpperCase();
          if (!/^[A-Z]{3}$/.test(currency)) {
            return respond(400, { currency: ['Invalid currency.'] });
          }
          exp.currency = currency;
        }
        if (jsonBody.description != null) exp.description = jsonBody.description;
        if (formData && formData.get('receipt') && formData.get('receipt').name) {
          exp.receipt = 'demo://receipt/' + formData.get('receipt').name;
        }
        save(db);
        return respond(200, expenseOut(db, exp));
      }
      if (method === 'DELETE') {
        db.expenses = db.expenses.filter((e) => e.id !== id);
        save(db);
        return respond(204, null);
      }
    }

    if (path === '/budgets' || path === '/budgets/') {
      if (method === 'GET') {
        let items = db.budgets.filter((b) => b.user === user.id);
        if (query.category) items = items.filter((b) => b.category === query.category);
        if (query.period) items = items.filter((b) => b.period === query.period);
        return respond(200, {
          count: items.length,
          next: null,
          previous: null,
          results: items.map((b) => budgetOut(db, b)),
        });
      }
      if (method === 'POST') {
        const category = jsonBody.category;
        const amount = jsonBody.amount;
        const period = jsonBody.period || 'monthly';
        if (!findCategory(db, user, category)) return respond(400, { category: ['Invalid category.'] });
        if (!(Number(amount) > 0)) return respond(400, { amount: ['Amount must be greater than zero.'] });
        if (!['weekly', 'monthly', 'yearly'].includes(period)) {
          return respond(400, { period: ['Invalid period.'] });
        }
        if (db.budgets.some((b) => b.user === user.id && b.category === category && b.period === period)) {
          return respond(400, { non_field_errors: ['You already have a budget for this category and period.'] });
        }
        const now = todayISO();
        const budget = {
          id: db.nextIds.budget++,
          user: user.id,
          category,
          amount: Number(amount).toFixed(2),
          period,
          created_at: now,
          updated_at: now,
        };
        db.budgets.push(budget);
        save(db);
        return respond(201, budgetOut(db, budget));
      }
    }

    const budDetail = matchPath(path, '/budgets/{id}') || matchPath(path, '/budgets/{id}/');
    if (budDetail) {
      const id = Number(budDetail.id);
      const budget = db.budgets.find((b) => b.id === id && b.user === user.id);
      if (!budget) return respond(404, { detail: 'Not found.' });
      if (method === 'GET') return respond(200, budgetOut(db, budget));
      if (method === 'PUT' || method === 'PATCH') {
        if (jsonBody.category) {
          if (!findCategory(db, user, jsonBody.category)) {
            return respond(400, { category: ['Invalid category.'] });
          }
          budget.category = jsonBody.category;
        }
        if (jsonBody.amount != null) {
          if (!(Number(jsonBody.amount) > 0)) {
            return respond(400, { amount: ['Amount must be greater than zero.'] });
          }
          budget.amount = Number(jsonBody.amount).toFixed(2);
        }
        if (jsonBody.period) {
          if (!['weekly', 'monthly', 'yearly'].includes(jsonBody.period)) {
            return respond(400, { period: ['Invalid period.'] });
          }
          budget.period = jsonBody.period;
        }
        budget.updated_at = todayISO();
        save(db);
        return respond(200, budgetOut(db, budget));
      }
      if (method === 'DELETE') {
        db.budgets = db.budgets.filter((b) => b.id !== id);
        save(db);
        return respond(204, null);
      }
    }

    return respond(404, { detail: 'Not found.' });
  }

  global.DemoStore = { handle, load, save, KEY };
})(window);
