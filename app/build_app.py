#!/usr/bin/env python3
"""
Build the final app: reference UI + HALYARD payload + a Routes tab.

The Routes tab is written against the app's own idioms — same `.spec`/table
classes, same `data-sel` wiring for drilling into a species, same filter chrome —
so it reads as part of the app rather than bolted on. It is read-only by
decision: which encounters appear where, no missable tracking, no completion
state.
"""
import re, sys, json

SRC  = "/mnt/user-data/uploads/emerald_imperium_survey_onefile.html"
B64  = "/home/claude/work/data.b64"
DEST = "/home/claude/work/index.html"


ABOUT_HTML = ("<div style=\"max-width:70ch\"><h2 style=\"font-size:32px\">About</h2>"
 "<p>Built from the HALYARD pipeline. 1,523 species forms, 1,020 scored across "
 "nineteen checkpoints, 90 boss fights. <b>4,248,276</b> one-on-one matchups "
 "computed from 152,865 candidate builds, themselves drawn from 2,414,290 "
 "enumerated builds. Damage engine: RadicalRedShowdown/damage-calc on a custom "
 "data layer built from this hack&rsquo;s own species table &mdash; its bundled data "
 "layer is never used. <b>Generation 8 mechanics are pinned</b>, so every damage "
 "figure is <b>Derived</b>, never Measured.</p>"

 "<h3>Reading a species page</h3>"
 "<p>Roles first, and gates come before scores: a wall without recovery is not a "
 "wall at any bulk. Every build is scored inside a role rather than on one global "
 "ladder, because a single list collapses into a base-stat sort &mdash; measurably so. "
 "Role fit is <code>w_stat&middot;S + w_tool&middot;T + w_type&middot;Y + w_fight&middot;F</code>, "
 "each reported separately. <b>Floor</b> is zero investment. <b>Ceiling</b> is the best "
 "build using only reliably obtainable items. <b>VORP</b> subtracts the third-best "
 "floor build in the same role; where fewer than three exist the row is marked NR "
 "and left unranked rather than given a flattering number.</p>"

 "<h3>Tiers</h3>"
 "<p>Cut at fixed values of mean VORP and <b>recut against this distribution</b>, not "
 "inherited from any earlier build &mdash; badges are not comparable to a previous run. "
 "The curve is not forced: if the hack genuinely has many strong options, that is "
 "the finding.</p>"

 "<h3>Sustain</h3>"
 "<p>The turn dimension the damage axes cannot see. The roster is walked "
 "sequentially on one lifebar with per-turn recovery, the bar resetting at each "
 "trainer because the player heals between fights. The published figure is the "
 "<b>kit delta</b> &mdash; this species minus the identical species with no kit &mdash; "
 "because raw sweep depth measures size rather than kit. Here raw depth correlates "
 "+0.37 with BST and the delta correlates &minus;0.17.</p>"

 "<h3>Where the timing comes from</h3>"
 "<p>All 127 encounter maps carry a gate, but only 7 come from item placements in "
 "source. The other 120 are <b>Asserted</b> &mdash; read from the creator&rsquo;s published "
 "route order, because the game files encode which flag gates each checkpoint but "
 "not which map is reachable when. Confidence is carried on every row.</p>"

 "<h3>Checks</h3>"
 "<p>The damage engine was verified against an independent reimplementation of the "
 "generation 8 formula: <b>99.7% agreement over 600 cells spanning 18 move types</b>, "
 "with both discrepancies traced to the checker rather than the engine. Of seven "
 "release invariants, three pass and four fail. I3 (rank is not a base-stat sort) "
 "passes at 0.502 against a 0.60 ceiling; I6 (stats drive the build) at 0.856 "
 "against a 0.20 floor; I7 at 0.129. I1 and I2 fail as single-item and "
 "single-nature concentration inside the wall and support builds; I4 fails on 117 "
 "checkpoint-role cells that are mostly genuine role scarcity; I5 fails on one "
 "item-copy conflict.</p>"

 "<h3>Known limits</h3>"
 "<p><b>Move priority is scored but does not move first.</b> It gates the revenge "
 "killer and priority abuser roles and feeds the tool term, but the matchup matrix "
 "orders turns on raw Speed alone, so Sucker Punch earns role credit without "
 "actually striking first. 655 published ceilings carry a damaging priority move. "
 "Level-scaled rival battles carry no fixed roster and are excluded entirely &mdash; "
 "153 boss slots. Checkpoints 2 and 4 have no roster of their own and are scored "
 "against the next fight ahead. Nine hack-custom boss forms are missing from the "
 "species table. Gift creatures and in-game trades were never parsed. 58 alternate "
 "forms inherit their base form&rsquo;s timing. Investment cost, lineage value and "
 "per-checkpoint EV spread are not computed and show as em dashes rather than "
 "invented numbers.</p>"

 "<h3>Interface</h3>"
 "<p>The survey interface is reused wholesale from the Emerald Imperium analysis "
 "app by the same author &mdash; layout, dossier, party and boss views unchanged. Only "
 "the data underneath is swapped and a Routes tab added. Sprite art ships with it, "
 "from the Radical Red dex set (ydarissep/JwowSquared.github.io); 1,522 of 1,523 "
 "forms match.</p></div>")

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

    # 6. the About tab described the reference build, not this one. Left as it
    #    was, the page whose job is to say what to trust was the page lying.
    h, n = re.subn(r"function rAbout\(\)\{return `[\s\S]*?`;\}",
                   lambda m: "function rAbout(){return " + json.dumps(ABOUT_HTML) + ";}",
                   h, count=1)
    assert n == 1, "rAbout not found"

    open(DEST, "w", encoding="utf-8").write(h)
    print(f"built {DEST}  {len(h)/1e6:.2f} MB")
    for probe, label in [("['routes','Routes']", "tab registered"),
                         ("routes:rRoutes", "dispatch hooked"),
                         ("function rRoutes()", "view defined"),
                         ("#rq", "filter wired"),
                         ("4,248,276", "About rewritten")]:
        print(f"  {label:<18} {'ok' if probe in h else 'MISSING'}")


if __name__ == "__main__":
    main()
