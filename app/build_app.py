#!/usr/bin/env python3
"""
Build the final app: reference UI + HALYARD payload + a Routes tab.

The Routes tab is written against the app's own idioms — same `.spec`/table
classes, same `data-sel` wiring for drilling into a species, same filter chrome —
so it reads as part of the app rather than bolted on. It is read-only by
decision: which encounters appear where, no missable tracking, no completion
state.
"""
import re, sys

SRC  = "/mnt/user-data/uploads/emerald_imperium_survey_onefile.html"
B64  = "/home/claude/work/data.b64"
DEST = "/home/claude/work/index.html"

ROUTES_JS = r"""
// ---------- Routes: read-only encounter listing ----------
// Which species appear on which map, with method, level band and slot rate.
// Deliberately not a checklist: no missable tracking, no completion state.
//
// One row per SPECIES, not per encounter slot. A species commonly appears three
// or four times on one map across surf, old rod and super rod; listing each was
// noise. Rates are NOT summed — 5% on the surf table and 30% on a fishing table
// are probabilities in different tables, and adding them would state something
// false. Each method keeps its own rate, and the level band spans the merged
// slots.
function rRoutes(){
  const q=(S.rq||'').toLowerCase();
  const maps=(D.rt||[]).filter(([mp,enc])=>!q||mp.toLowerCase().includes(q)||
    enc.some(e=>{const sp=byIdx.get(e[0]);return sp&&disp(sp).toLowerCase().includes(q);}));
  let h=`<h2>Routes</h2>
    <div class="filters">
      <input id="rq" value="${esc(S.rq||'')}" placeholder="Filter maps or species"
        style="background:var(--ground2);color:var(--paper);border:1px solid var(--line2);
               border-radius:6px;padding:7px 10px;min-width:260px">
      <span class="count">${maps.length} of ${(D.rt||[]).length} maps</span>
    </div>
    <p class="note">Encounter tables as the game files record them, one row per species.
    Rates stay separate per method because they come from different tables. Value and tier
    are this species' best across the run, so a common early encounter can still carry a
    high badge.</p>`;
  if(!maps.length)return h+`<div class="empty">No map matches that.</div>`;
  const num=x=>{const n=parseInt(x,10);return isNaN(n)?null:n;};
  for(const [mp,enc] of maps.slice(0,40)){
    // merge slots of the same species
    const byMon=new Map();
    for(const [ii,meth,lv,rate] of enc){
      let g=byMon.get(ii);
      if(!g){g={ii,meth:new Map(),lo:null,hi:null,slots:0};byMon.set(ii,g);}
      g.slots++;
      const r=num(rate);
      const prev=g.meth.get(meth);
      if(prev===undefined||(r!==null&&(prev===null||r>prev)))g.meth.set(meth,r);
      const parts=String(lv||'').split('-').map(num).filter(x=>x!==null);
      for(const p of parts){
        if(g.lo===null||p<g.lo)g.lo=p;
        if(g.hi===null||p>g.hi)g.hi=p;
      }
    }
    const rows=[...byMon.values()].sort((a,b)=>{
      const va=val(byIdx.get(a.ii)),vb=val(byIdx.get(b.ii));
      return ((vb?vb[K.v]:-1)-(va?va[K.v]:-1));
    });
    h+=`<h3>${esc(mp)} <span class="note">· ${rows.length} species${
      rows.length!==enc.length?` from ${enc.length} slots`:''}</span></h3>
      <table><thead><tr><th>species</th><th>types</th><th>how</th>
      <th class="n">levels</th><th class="n">value</th>
      <th class="n">caught by</th><th>tier</th></tr></thead><tbody>`;
    for(const g of rows){
      const sp=byIdx.get(g.ii); if(!sp)continue;
      const v=val(sp);
      const how=[...g.meth.entries()].map(([m,r])=>{
        const label=String(m).replace(/_mons$/,'').replace(/_/g,' ');
        return `<span class="mv">${esc(label)}${r!==null?` <span class="note">${r}%</span>`:''}</span>`;
      }).join('');
      const band=g.lo===null?'—':(g.lo===g.hi?g.lo:`${g.lo}–${g.hi}`);
      h+=`<tr class="clk" data-sel="${g.ii}">
        <td>${art(sp,'rostart')}${disp(sp)}</td>
        <td>${types(sp).map(tyTag).join('')}</td>
        <td>${how}</td>
        <td class="n">${band}</td>
        <td class="n">${v?f4(v[K.v]):'—'}</td>
        <td class="n">${v?v[K.ec]:'—'}</td>
        <td>${tierTag(v)}</td></tr>`;
    }
    h+=`</tbody></table>`;
  }
  if(maps.length>40)h+=`<p class="note">Showing 40 of ${maps.length} maps. Narrow with the filter.</p>`;
  return h;
}
"""


def main():
    h = open(SRC, encoding="utf-8").read()
    b64 = open(B64).read().strip()

    # 1. swap the payload
    h, n = re.subn(r'(<script id="gz" type="text/plain">)[\s\S]*?(</script>)',
                   lambda m: m.group(1) + b64 + m.group(2), h, count=1)
    assert n == 1, "payload block not found"

    # 2. register the tab, between Bosses and Party
    h, n = re.subn(r"\['boss','Bosses'\],", "['boss','Bosses'],['routes','Routes'],", h, count=1)
    assert n == 1, "TABS not found"

    # 3. hook the renderer into the dispatch map
    h, n = re.subn(r"boss:rBoss,party:rParty", "boss:rBoss,routes:rRoutes,party:rParty", h, count=1)
    assert n == 1, "render dispatch not found"

    # 4. define the view alongside the others
    h, n = re.subn(r"\nfunction render\(\)\{", ROUTES_JS + "\nfunction render(){", h, count=1)
    assert n == 1, "render() anchor not found"

    # 5. wire the filter input, following the app's own wire() pattern
    h, n = re.subn(r"(function wire\(root\)\{)",
                   r"""\1
  const rq=root.querySelector('#rq');
  if(rq)rq.oninput=e=>{S.rq=e.target.value;render();
    const el=document.getElementById('rq');
    if(el){el.focus();try{el.setSelectionRange(el.value.length,el.value.length);}catch(x){}}};""",
                   h, count=1)
    assert n == 1, "wire() not found"

    open(DEST, "w", encoding="utf-8").write(h)
    print(f"built {DEST}  {len(h)/1e6:.2f} MB")
    for probe, label in [("['routes','Routes']", "tab registered"),
                         ("routes:rRoutes", "dispatch hooked"),
                         ("function rRoutes()", "view defined"),
                         ("#rq", "filter wired")]:
        print(f"  {label:<18} {'ok' if probe in h else 'MISSING'}")


if __name__ == "__main__":
    main()
