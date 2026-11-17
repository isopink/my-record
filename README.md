# My record

A record of things I have built. The site is one static page, `index.html`, served with GitHub Pages.

- Opening screen: a turning tree set in the names of the projects and tools.
- Main page: skills, one sentence, and the list of projects by field.

No build step. Open `index.html` in a browser to preview.

## Case pages

Each project with a write-up has a page under `projects/<name>/`. They are generated from the `entry.md` files in the portfolio source folder by `tools/build.py`, which also rewrites the project list in `index.html`:

```
python tools/build.py <path to portfoli-src>
```
