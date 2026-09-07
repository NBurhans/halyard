# Publishing to GitHub Pages

The survey is a single `index.html` at the repository root, so Pages needs no build
step, no workflow file and no Jekyll configuration.

## 1. Create the repository

On GitHub: **New repository** → name it `halyard` → **Public** → create it without a
README, since this bundle has one.

Description, exactly:

> A data-driven planning framework for turn-based RPG progression.

**Add no topics or tags**, and do not link to it from any forum, Discord or wiki.
See `VISION.md` section 1.

Pages only works on public repositories for free accounts. If you would rather the
repo stay private, the survey still opens by downloading `index.html` and opening it
in a browser — Pages is only for having a URL.

## 2. Push

```
cd halyard
git init
git add .
git commit -m "Analysis bundle: 4.2M matchup cells, 19,215 scored rows, survey app"
git branch -M main
git remote add origin https://github.com/<username>/halyard.git
git push -u origin main
```

Uploading through the web UI works too — drag the unzipped folder's *contents* onto
the empty repository page. Drag the contents, not the folder itself, or `index.html`
lands one directory down and Pages will not find it.

Commit messages carry no target-identifying words. Describe changes in framework
terms — "fix map gate merge order", not the target's name.

## 3. Turn Pages on

**Settings → Pages**

- **Source:** Deploy from a branch
- **Branch:** `main`
- **Folder:** `/ (root)`
- **Save**

The first build takes one to two minutes. The banner at the top of the Pages settings
turns into a link when it is live.

## 4. Open it

```
https://<username>.github.io/halyard/
```

Update the link at the top of `README.md` to match.

## Before you push, confirm

- [ ] `git status` shows no `04_matchups_cp*.tsv`, no `04_builds.tsv`, no `INT_*`
      files, no ROM or save files
- [ ] `docs/RUNBOOK.md` section 0 still contains `<CODENAME>` and the INTERNAL
      placeholders, not a filled-in target block
- [ ] the repo description and `git log` contain no target-identifying words

```
grep -c "CODENAME" docs/RUNBOOK.md    # expect 1 or more

# Put the target's public name, source repo handle and site into TERMS, then:
TERMS='yourhackname|yourgithubhandle|yourhacksite'
grep -riE "$TERMS" --exclude-dir=data --exclude=PUBLISHING.md . ; echo "exit $?"
```

Exit status 1 from the second command means clean. The pattern is left blank so this
file does not trip its own check.

## Notes

**`.nojekyll` is already here.** Without it, Pages runs the files through Jekyll,
which silently skips anything beginning with an underscore. Nothing here starts with
one today, but the file costs nothing and removes a category of confusing failure.

**The page is ~2.2 MB**, almost all of it embedded data. It loads in a second or two
and is cached afterwards. No server, no database, no build.

**Two external requests, both optional.** Google Fonts, and PokeAPI for sprites. If
either is blocked the page still works — fonts fall back to Georgia and Helvetica,
sprite boxes render empty, and every number is still there because the data is
embedded. This is a deliberate departure from `VISION.md` section 6, which calls for
no CDN dependency; strip the `<link>` tag and the `art()` function for a fully offline
build.

**Updating.** Rebuild with `python3 app/build_index.py`, then commit and push. Pages
redeploys on every push to `main`.

## If the page is blank

Almost always one of three things:

1. **Pages is pointed at the wrong folder.** It must be `/ (root)`, and `index.html`
   must be at the top level of the repository.
2. **The deploy has not finished.** Check **Actions** for a running `pages build and
   deployment` job.
3. **You are looking at a preview, not a browser.** In-app file previews inside chat
   and messaging apps commonly block scripts. Open the URL in Safari, Chrome, Firefox
   or Edge.

The app detects its own failures and prints an explanation rather than showing a blank
page — so a genuinely blank white screen points at 1 or 2, while a message on screen
tells you what went wrong.
