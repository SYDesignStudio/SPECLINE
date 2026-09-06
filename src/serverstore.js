/* ================= Server-backed store =================
   The app persists through a small interface — db.doc(path).get/set/delete and
   db.collection("jobs").limit(n).get() — which in the Claude artifact is the artifact's own
   db capability. This provides the same interface over specline.co.uk, so the hosted build
   stores jobs against the signed-in practice instead, and NOT ONE LINE of the app's own
   save, load or delete logic changes.

   It only exists when the page was served by site/app.php, which injects window.SPECLINE with
   the session's CSRF token. Opened any other way there is no SPECLINE object, no store, and
   the app falls back to localStorage exactly as before.

   Every call is scoped server-side by the practice on the session. Nothing here sends a
   practice id, because a client must never be able to name whose jobs it wants. */

function serverStore(cfg){
  const post = async (op, payload) => {
    const r = await fetch(cfg.api, {
      method: "POST",
      credentials: "same-origin",
      headers: {"Content-Type": "application/json", "X-CSRF": cfg.csrf},
      body: JSON.stringify({op, ...payload})
    });
    let j = null;
    try{ j = await r.json(); }catch(e){}
    if(!r.ok || !j || j.ok !== true){
      const msg = (j && j.error) || ("Server returned " + r.status);
      if(r.status === 401 || r.status === 403) window.SPECLINE_SIGNED_OUT = true;
      throw new Error(msg);
    }
    return j;
  };

  /* A document reference. Only two paths are ever asked for — jobs/<id> and practice/profile —
     and the server accepts only those two, so a path cannot be used to reach anything else. */
  const doc = path => ({
    async get(){
      const j = await post("doc.get", {path});
      const data = j.data;
      return {exists: !!data, data: () => data};
    },
    async set(obj){ await post("doc.set", {path, data: obj}); },
    async delete(){ await post("doc.del", {path}); }
  });

  const collection = name => {
    let cap = 100;
    const api = {
      limit(n){ cap = n; return api; },
      async get(){
        const j = await post("coll.get", {name, limit: cap});
        const docs = (j.docs || []).map(d => ({id: d.id, data: () => d.data}));
        return {docs};
      }
    };
    return api;
  };

  return {doc, collection, hosted: true};
}
