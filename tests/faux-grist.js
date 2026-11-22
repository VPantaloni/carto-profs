// Fausse API Grist : le test envoie les lignes et les options avec window.__envoyer(...).
(function () {
  const g = window.__grist = { pret: null, options: null, sauvegardes: [], curseur: null, actions: null, refuserOptions: false, tables: {}, journal: [] };
  let cbLignes = null, cbOptions = null;
  window.__FAUX_GRIST__ = true;
  window.grist = {
    ready(cfg) { g.pret = cfg; },
    onRecords(cb) { cbLignes = cb; },
    onOptions(cb) { cbOptions = cb; },
    setOptions(o) { if (g.refuserOptions) return Promise.reject(new Error('lecture seule')); g.sauvegardes.push(o); g.options = o; return Promise.resolve(); },
    setCursorPos(p) { g.curseur = p; return Promise.resolve(); },
    getSelectedTableId() { return Promise.resolve('Profs_maths_26_27'); },
    docApi: {
      // document en mémoire : seulement les tables créées par le widget (les groupes)
      listTables() { return Promise.resolve(['Profs_maths_26_27', ...Object.keys(g.tables)]); },
      fetchTable(t) {
        const l = g.tables[t]; if (!l) return Promise.reject(new Error('table inconnue ' + t));
        const cols = { id: l.lignes.map(r => r.id) };
        for (const c of l.cols) cols[c] = l.lignes.map(r => r[c] ?? '');
        return Promise.resolve(cols);
      },
      applyUserActions(actions) {
        g.actions = actions; g.journal.push(...actions);
        const ret = [];
        for (const [type, table, ...a] of actions) {
          if (type === 'AddTable') { g.tables[table] = { cols: a[0].map(c => c.id), lignes: [], n: 0 }; ret.push(null); continue; }
          const t = g.tables[table];
          if (!t) { ret.push(null); continue; }      // AddColumn / BulkUpdateRecord sur la table des personnes
          if (type === 'AddRecord') { const id = ++t.n; t.lignes.push({ id, ...a[1] }); ret.push(id); }
          if (type === 'BulkAddRecord') { const ids = a[0].map(() => ++t.n); ids.forEach((id, i) => { const r = { id }; for (const k in a[1]) r[k] = a[1][k][i]; t.lignes.push(r); }); ret.push(ids); }
          if (type === 'UpdateRecord') { Object.assign(t.lignes.find(r => r.id === a[0]), a[1]); ret.push(null); }
          if (type === 'RemoveRecord' || type === 'BulkRemoveRecord') { const ids = new Set(type === 'RemoveRecord' ? [a[0]] : a[0]); t.lignes = t.lignes.filter(r => !ids.has(r.id)); ret.push(null); }
        }
        return Promise.resolve({ retValues: ret });
      }
    }
  };
  window.__optionsSeules = (options, acces) => { if (cbOptions) cbOptions(options, { accessLevel: acces }); };
  window.__envoyer = (lignes, options = null, acces = 'read table', mappings = null) => {
    if (cbOptions) cbOptions(options, { accessLevel: acces });
    if (cbLignes) cbLignes(lignes, mappings);
  };
})();
