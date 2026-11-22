// Faux MapLibre pour les tests sans affichage : garde la forme de l'API utilisée par Carto-profs.
// Projection simple : 1 degré = 100 px, centre de la carte au milieu du conteneur.
(function () {
  const journal = window.__carte = { styles: [], sources: {}, appels: [] };
  class Evenements {
    constructor() { this._ec = {}; }
    on(type, couche, cb) { if (typeof couche === 'function') { cb = couche; couche = null; } (this._ec[type] = this._ec[type] || []).push({ couche, cb }); return this; }
    _emettre(type, e = {}) { for (const x of this._ec[type] || []) if (!x.couche) x.cb(e); }
  }
  class Source {
    constructor(carte, def) { this.carte = carte; this.def = def; this.data = def.data; }
    setData(d) { this.data = d; setTimeout(() => this.carte._emettre('render'), 0); return this; }
    getClusterExpansionZoom() { return Promise.resolve(10); }
  }
  class Map extends Evenements {
    constructor(o) {
      super();
      this.conteneur = typeof o.container === 'string' ? document.getElementById(o.container) : o.container;
      this.canvas = document.createElement('canvas'); this.canvas.width = this.conteneur.clientWidth || 800; this.canvas.height = this.conteneur.clientHeight || 600;
      this.cc = document.createElement('div'); this.cc.className = 'maplibregl-canvas-container'; this.cc.style.cssText = 'position:absolute;inset:0';
      this.cc.appendChild(this.canvas); this.conteneur.appendChild(this.cc);
      this.centre = o.center; this.zoom = o.zoom; this.sources = {}; this.couches = {};
      this.dragPan = { actif: true, enable() { this.actif = true; }, disable() { this.actif = false; } };
      journal.carte = this; journal.styles.push(o.style);
      setTimeout(() => { this._emettre('styledata'); this._emettre('load'); this._emettre('render'); }, 10);
    }
    addControl(c) { if (c && c.onAdd) this.conteneur.appendChild(c.onAdd(this)); return this; }
    addSource(id, def) { if (this.sources[id]) throw new Error('source existe : ' + id); this.sources[id] = new Source(this, def); journal.sources[id] = def; setTimeout(() => this._emettre('render'), 0); }
    getSource(id) { return this.sources[id]; }
    removeSource(id) { delete this.sources[id]; }
    addLayer(c) { this.couches[c.id] = c; }
    getLayer(id) { return this.couches[id]; }
    removeLayer(id) { delete this.couches[id]; }
    isSourceLoaded(id) { return !!this.sources[id]; }
    isStyleLoaded() { return true; }
    querySourceFeatures(id) { const s = this.sources[id]; return s ? (s.data.features || []).map(f => ({ ...f, properties: { ...f.properties } })) : []; }
    project(ll) {
      const [lon, lat] = Array.isArray(ll) ? ll : [ll.lng, ll.lat];
      const w = this.conteneur.clientWidth || 800, h = this.conteneur.clientHeight || 600;
      return { x: w / 2 + (lon - this.centre[0]) * 100, y: h / 2 - (lat - this.centre[1]) * 100 };
    }
    getCanvas() { return this.canvas; }
    getCanvasContainer() { return this.cc; }
    getZoom() { return this.zoom; }
    fitBounds(b) { journal.appels.push(['fitBounds', b.pts.length]); if (b.pts.length) { const lo = b.pts.map(p => p[0]), la = b.pts.map(p => p[1]); this.centre = [(Math.min(...lo) + Math.max(...lo)) / 2, (Math.min(...la) + Math.max(...la)) / 2]; } this._emettre('render'); }
    flyTo(o) { journal.appels.push(['flyTo', o.center]); this.centre = o.center; this._emettre('render'); }
    easeTo(o) { journal.appels.push(['easeTo', o.center]); }
    resize() {}
    getBearing() { return 0; }
    setStyle(url) {
      journal.styles.push(url); this.sources = {}; this.couches = {};
      setTimeout(() => { this._emettre('styledata'); this._emettre('render'); }, 10);
    }
  }
  class Marker {
    constructor(o = {}) { this.el = o.element || document.createElement('div'); this.el.classList.add('maplibregl-marker'); this.el.style.position = 'absolute'; }
    setLngLat(ll) { this.ll = Array.isArray(ll) ? { lng: ll[0], lat: ll[1] } : ll; this._placer(); return this; }
    getLngLat() { return this.ll; }
    getElement() { return this.el; }
    addTo(carte) { this.carte = carte; carte.cc.appendChild(this.el); this._placer(); return this; }
    _placer() { if (!this.carte || !this.ll) return; const p = this.carte.project(this.ll); this.el.style.left = (p.x - 8) + 'px'; this.el.style.top = (p.y - 8) + 'px'; }
    remove() { this.el.remove(); return this; }
  }
  class Popup {
    constructor(o = {}) { this.el = document.createElement('div'); this.el.className = 'maplibregl-popup ' + (o.className || ''); this.el.style.position = 'absolute'; }
    setLngLat(ll) { this.ll = ll; return this; }
    setHTML(h) { this.el.innerHTML = '<div class="maplibregl-popup-content">' + h + '</div>'; return this; }
    addTo(carte) { carte.cc.appendChild(this.el); return this; }
    remove() { this.el.remove(); return this; }
  }
  class LngLatBounds { constructor() { this.pts = []; } extend(p) { this.pts.push(p); return this; } }
  class NavigationControl {}
  window.maplibregl = { Map, Marker, Popup, LngLatBounds, NavigationControl };
})();
