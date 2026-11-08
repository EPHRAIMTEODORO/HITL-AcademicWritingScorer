# HITL AES — desktop field guide

A buildless, static explanatory website for linguistic researchers and technical readers. It covers **only the HITL Electron desktop app**, its Python backend, and the shared linguistic extractor imported by that app.

## Open locally

Open `index.html` directly in a browser. The guide, exact prompts, navigation, search, and diagrams need no backend, API keys, npm install, or internet connection. Clipboard access depends on browser policy; a selection fallback is provided.

For an HTTP preview, open a terminal **inside this website folder** (the folder containing `index.html`) and run:

```powershell
python -m http.server 8080 --bind 127.0.0.1 --directory .
```

Then visit `http://127.0.0.1:8080`.

From any other working directory, supply the website folder's full path:

```powershell
python -m http.server 8080 --bind 127.0.0.1 --directory "C:\path\to\HITL AES"
```

Replace the example path with this folder's location. The static site can be moved or renamed independently of the desktop app repository.

## GitHub Pages

All website files live in this folder. Asset links are relative, so the site works at a GitHub Pages project subpath as well as the domain root.

For a standalone website repository with `index.html` at its root, publish the repository root through GitHub Pages. Alternatively, choose **GitHub Actions** as the Pages source and put the following workflow in `.github/workflows/hitl-aes-pages.yml`:

```yaml
name: Deploy HITL AES guide
on:
  push:
    branches: [main]
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write
concurrency:
  group: pages
  cancel-in-progress: true
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: '.'
      - name: Deploy
        id: deployment
        uses: actions/deploy-pages@v4
```

If the website is still nested inside an app repository, change the upload artifact's `path` to `'HITL AES'` (or its actual relative folder name). If that repository already publishes its entire root, the nested site is available beneath `/HITL%20AES/`. Integrate with an existing Pages deployment rather than replacing it unintentionally.

The website has been created locally. No repository settings, remote commits, or deployments are performed by creating these files.

## Files and content maintenance

- `index.html`: all explanatory content, semantic tables, exact prompt blocks, and source register. It remains readable without JavaScript.
- `assets/styles.css`: responsive layout and print styles.
- `assets/site.js`: navigation, progress, feature search, prompt expansion, copying, and print preparation. No network requests or analytics.
- `assets/prompts.txt`: downloadable exact prompt definitions, including all anchors.
- `assets/source-manifest.json`: reviewed source paths, base commit, workspace modification flags, prompt line locations, and full SHA-256 hashes.
- `scripts/sync_reference.py`: refreshes exact prompts and provenance using Python's standard library. It parses the prompt module with `ast` rather than importing the app or starting inference.
- `.nojekyll`: allows direct static serving.

### Refresh prompts and source hashes after moving the folder

The website already contains everything needed to read and print it. **Refreshing references requires a separate copy of the app's source code.** From inside the website folder, point the script at the app repository:

```powershell
python scripts/sync_reference.py --source-root "C:\path\to\Rule-Based-AES"
```

The source path must contain `HITL/`, `aes_feature_extractor.py`, `docs/`, and `data/`; it is not the standalone website folder. Relative source paths are resolved from the terminal's working directory. The script always updates the website next to itself, regardless of where it is launched. No machine-specific path is stored in the script or published files.

If the website folder sits directly inside the app repository, the original automatic parent-directory lookup still works:

```powershell
python scripts/sync_reference.py
```

If source files are missing, the script prints instructions and leaves the existing website untouched. A source export without Git history still supports prompts and hashes; its commit and modification-status fields are recorded as unavailable instead of inferred.

**This does not update explanatory prose automatically.** Review scoring behavior, UI thresholds, defaults, rubric interpretation, and limitations against the current source, then update the review date in the page and script. Source links track GitHub `main`; they may differ from the source snapshot recorded in the manifest.

The published site contains the app's calibration anchors, but no input-workbook student records. It is documentation, not a browser version of the scorer. The Print / Save PDF button expands technical details and prompts before printing. Printing includes all feature rows even after a search; the on-screen search and its filtered rows are preserved afterward.
