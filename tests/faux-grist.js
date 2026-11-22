// Fausse API Grist : le test envoie les lignes et les options avec window.__envoyer(...).
(function () {
  const g = window.__grist = { pret: null, options: null, sauvegardes: [], curseur: null, actions: null, refuserOptions: false };
  let cbLignes = null, cbOptions = null;
  window.__FAUX_GRIST__ = true;
  window.grist = {
    ready(cfg) { g.pret = cfg; },
    onRecords(cb) { cbLignes = cb; },
    onOptions(cb) { cbOptions = cb; },
    setOptions(o) { if (g.refuserOptions) return Promise.reject(new Error('lecture seule')); g.sauvegardes.push(o); g.options = o; return Promise.resolve(); },
    setCursorPos(p) { g.curseur = p; return Promise.resolve(); },
    getSelectedTableId() { return Promise.resolve('Profs_maths_26_27'); },
    docApi: { applyUserActions(a) { g.actions = a; return Promise.resolve(); } }
  };
  window.__optionsSeules = (options, acces) => { if (cbOptions) cbOptions(options, { accessLevel: acces }); };
  window.__envoyer = (lignes, options = null, acces = 'read table', mappings = null) => {
    if (cbOptions) cbOptions(options, { accessLevel: acces });
    if (cbLignes) cbLignes(lignes, mappings);
  };
})();
