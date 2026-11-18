"""Build the case pages and the project list of the record site from the entry.md files.

Usage: python -I build.py <portfoli-src folder>
"""
import html
import os
import re
import sys

SRC = sys.argv[1]
SITE = os.path.join(SRC, 'site')

# Projects that get a case page: (folder, slug, picture files allowed on the public page or None for all).
CASES = [
    ('LLM agents/interview-prep-agent', None),
    ('LLM agents/sigma-engine', None),
    ('LLM agents/deep-report-pipeline', None),
    ('LLM agents/paper-review-deck', None),
    ('LLM agents/career-log', None),
    ('Data/steps-before-crashes', None),
    ('Data/disaster-library-whitepaper', None),
    ('Robotics/open-duck-mini-v2', None),
    ('Robotics/object-finder-bot', None),
    ('Robotics/3ddsg-drone-navigation', None),
    ('Architecture/branding-in-seongsu', None),
    ('Architecture/gangil-evacuation-simulation', None),
    ('Architecture/digital-media-ii', None),
    ('Architecture/thank-you-plaque', None),
    ('Startup/first-wrong-step', None),
    ('Startup/ibul-anbu', None),
    # Photos show a third party's workplace; consent is still open, so the page goes out without them.
    ('Startup/impact-bridge', []),
    ('Startup/pm-decision-making', None),
    ('Data/data-engineering-fundamentals', None),
]
ORDER = ['Overview', 'Problem define', 'Solution', 'Process', 'Lesson', 'Next']
ALIAS = {'Problem': 'Problem define'}
GH = 'https://github.com/isopink/'


def esc(s):
    return html.escape(s, quote=True)


def parse(path):
    text = open(path, encoding='utf-8').read()
    m = re.match(r'---\n(.*?)\n---\n', text, re.S)
    front = {}
    for line in m.group(1).split('\n'):
        if ':' in line:
            k, v = line.split(':', 1)
            front[k.strip()] = v.strip()
    body = text[m.end():]
    sections, cur = {}, None
    for line in body.split('\n'):
        h = re.match(r'## (.+)', line)
        if h:
            cur = ALIAS.get(h.group(1).strip(), h.group(1).strip())
            sections[cur] = []
        elif cur:
            sections[cur].append(line)
    return front, {k: '\n'.join(v).strip() for k, v in sections.items()}


def clean(s):
    """Remove working notes that do not belong on a public page."""
    s = re.sub(r'\s*\((?:[^()]|\([^()]*\))*`[^()]*\)', '', s)        # parenthetical file references
    s = re.sub(r'\s*\((?:source|Source)[^)]*\)', '', s)
    s = re.sub(r'\s*\([^()]*\.(?:md|py|json|csv|txt|pdf|xlsx|fds|out|gh|sql|ipynb)[^()]*\)', '', s)
    s = re.sub(r'\s*\((?:commit|row|page|p\.|section|slide)[^)]*\)', '', s)
    s = re.sub(r'(?:Source|Sources|Figure|Figures): [^\n]*', '', s)
    sents = re.split(r'(?<=[.!?])\s+', s)
    s = ' '.join(x for x in sents if 'MISSING' not in x and not re.match(r'\s*(?:Source|Figure)s?\b', x)
                 and not re.search(r'\b(?:the|in the) (?:files|folder|source folder|source)\b|\bfiles hold\b|\bthe recordings\b', x))
    s = re.sub(r'\s*\((?:same|see) [^)]*\)', '', s)
    s = re.sub(r'\s+`[^`]+`\s*$', '', s.rstrip())                         # trailing file reference
    s = re.sub(r'\s{2,}', ' ', s).strip()
    return s


def inline(s):
    s = esc(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    return s


def render(block, keep_sources=False):
    out, lines, i = [], block.split('\n'), 0
    tidy = (lambda x: x) if keep_sources else clean
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            head, body = rows[0], [r for r in rows[2:] if keep_sources or not any('MISSING' in c for c in r)]
            keep = [j for j, h in enumerate(head) if keep_sources or h not in ('Source', 'Date')]
            if body:
                out.append('<div class="tablebox"><table><thead><tr>' + ''.join('<th scope="col">%s</th>' % inline(head[j]) for j in keep) + '</tr></thead><tbody>'
                           + ''.join('<tr>' + ''.join('<td>%s</td>' % inline(tidy(r[j]) if j < len(r) else '') for j in keep) + '</tr>' for r in body) + '</tbody></table></div>')
            continue
        if re.match(r'\d+\. ', line) or line.startswith('- '):
            tag = 'ol' if re.match(r'\d+\. ', line) else 'ul'
            items = []
            while i < len(lines) and (re.match(r'\d+\. ', lines[i]) or lines[i].startswith('- ')):
                t = tidy(re.sub(r'^(\d+\. |- )', '', lines[i]))
                if t:
                    items.append(t)
                i += 1
            if items:
                out.append('<%s>%s</%s>' % (tag, ''.join('<li>%s</li>' % inline(t) for t in items), tag))
            continue
        if line.startswith('> '):
            q = []
            while i < len(lines) and lines[i].startswith('>'):
                q.append(lines[i][1:].strip())
                i += 1
            out.append('<blockquote lang="ko">%s</blockquote>' % '<br>'.join(inline(x) for x in q))
            continue
        h = re.match(r'(#{3,4}) (.+)', line)
        if h:
            out.append('<h3>%s</h3>' % inline(h.group(2)))
            i += 1
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r'(\||\d+\. |- |> |#)', lines[i]):
            para.append(lines[i].strip())
            i += 1
        kv = [re.match(r'([A-Z][A-Za-z ]{1,24}): (.+)', x) for x in para]
        if len(para) > 1 and all(kv):
            rows = [(k.group(1), tidy(k.group(2))) for k in kv]
            rows = [r for r in rows if r[1] and 'MISSING' not in r[1]]
            if rows:
                out.append('<dl class="kv">%s</dl>' % ''.join('<div><dt>%s</dt><dd>%s</dd></div>' % (inline(a), inline(b)) for a, b in rows))
            continue
        t = tidy(' '.join(para))
        if t:
            out.append('<p>%s</p>' % inline(t))
    return '\n'.join(out)


def images_by_part(folder, allowed):
    """Read the Images table: file, caption, alt text, part."""
    front, sec = parse(os.path.join(SRC, folder, 'entry.md'))
    rows = [l for l in sec.get('Images', '').split('\n') if l.startswith('|')][2:]
    found = []
    for r in rows:
        c = [x.strip() for x in r.strip().strip('|').split('|')]
        if len(c) < 5:
            continue
        name = os.path.basename(c[0].strip('`'))
        base = os.path.splitext(name)[0] + '.jpg'
        if allowed is not None and base not in allowed:
            continue
        part = ALIAS.get(c[4], c[4])
        found.append({'src': 'img/' + base, 'cap': c[2], 'alt': c[3], 'part': part})
    return found


import subprocess


def copy_images(folder, dest, allowed):
    src = os.path.join(SRC, folder, 'images')
    if not os.path.isdir(src) or allowed == []:
        return
    os.makedirs(dest, exist_ok=True)
    tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resize.ps1')
    for name in sorted(os.listdir(src)):
        if os.path.splitext(name)[1].lower() not in ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'):
            continue
        target = os.path.join(dest, os.path.splitext(name)[0] + '.jpg')
        if allowed is not None and os.path.basename(target) not in allowed:
            continue
        if os.path.exists(target) and os.path.getmtime(target) >= os.path.getmtime(os.path.join(src, name)):
            continue
        subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', tool, os.path.join(src, name), target],
                       check=True, capture_output=True)


PAGE_CSS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'case.css'), encoding='utf-8').read()


def page(title, desc, body):
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap">\n'
            '<style>\n%s</style>\n</head>\n<body>\n%s\n</body>\n</html>\n') % (esc(title), esc(desc), PAGE_CSS, body)


def figure(img, lead=False):
    return ('<figure class="%s"><img src="%s" alt="%s" loading="%s"><figcaption>%s</figcaption></figure>'
            % ('fig lead' if lead else 'fig', esc(img['src']), esc(img['alt']), 'eager' if lead else 'lazy', inline(img['cap'])))


# Field names as the site shows them.
FIELD_NAME = {'LLM agents': 'Agents', 'Architecture': 'Design', 'Startup': 'Business'}
# Projects shown under a different field from the one in their entry.md.
FIELD_OVERRIDE = {'gangil-evacuation-simulation': 'Data'}
# Projects shown under a different name from the one in their entry.md.
TITLE_OVERRIDE = {
    'interview-prep-agent': 'Job Interview Prep',
    'first-wrong-step': 'Pathfinder',
    'gangil-evacuation-simulation': 'Evacuation Simulation',
    'object-finder-bot': 'Object Finder Bot',
    '3ddsg-drone-navigation': '3DDSG Drone Navigation',
    'deep-report-pipeline': 'Deep Report Pipeline',
    'paper-review-deck': 'Paper Review Deck',
    'career-log': 'Career Log',
    'disaster-library-whitepaper': 'Disaster Library Whitepaper',
    'data-engineering-fundamentals': 'Data Engineering Fundamentals',
    'pm-decision-making': 'PM Decision Making',
    'thank-you-plaque': 'Thank-You Plaque',
    'branding-in-seongsu': 'Branding In Seongsu',
}


def build_case(folder, allowed):
    front, sec = parse(os.path.join(SRC, folder, 'entry.md'))
    slug = os.path.basename(folder)
    front['field'] = FIELD_OVERRIDE.get(slug, front.get('field'))
    front['title'] = TITLE_OVERRIDE.get(slug, front.get('title'))
    out = os.path.join(SITE, 'projects', slug)
    os.makedirs(out, exist_ok=True)
    copy_images(folder, os.path.join(out, 'img'), allowed)
    imgs = images_by_part(folder, allowed)
    lead = next((x for x in imgs if x['part'] == 'Lead'), None)

    facts = []
    for key, label in (('shown_at', 'Shown at'), ('role', 'Role'), ('built_with', 'Built with')):
        v = clean(front.get(key, ''))
        if v and v.lower() != 'none':
            facts.append('<div><dt>%s</dt><dd>%s</dd></div>' % (label, inline(v)))
    head_text = open(os.path.join(SRC, folder, 'entry.md'), encoding='utf-8').read().split('\n---', 2)[0]
    links = list(dict.fromkeys(re.findall(r'https?://github\.com/isopink/[\w.-]+', head_text)))
    paper = os.path.exists(os.path.join(SRC, folder, 'paper.md')) and front.get('public', '').startswith('yes')
    actions = ''.join('<a class="btn" href="%s">View on GitHub</a>' % esc(l) for l in links if 'github.com' in l)
    if paper:
        actions = '<a class="btn" href="paper.html">Read the full write-up</a>' + actions
    kind = ''
    status = '<span class="kind">In progress</span>' if front.get('status') == 'ongoing' else ''

    parts = []
    for name in ORDER:
        if name not in sec or not sec[name].strip():
            continue
        html_part = render(sec[name])
        if not html_part.strip():
            continue
        figs = ''.join(figure(x) for x in imgs if x['part'] == name)
        parts.append('<section class="part" id="%s"><h2>%s</h2><div class="part-body">%s%s</div></section>'
                     % (name.lower().replace(' ', '-'), esc(name), html_part, figs))

    nav = ''.join('<a href="#%s">%s</a>' % (n.lower().replace(' ', '-'), esc(n)) for n in ORDER if n in sec and render(sec[n]).strip())
    title = front['title']
    body = '''<header class="wrap top">
<a class="back" href="../../index.html#work">All work</a>
<p class="field">{field}{kind}{status}</p>
<h1>{title}</h1>
<p class="lead">{lead}</p>
<dl class="facts">{facts}</dl>
<div class="actions">{actions}</div>
</header>
{leadfig}
<nav class="wrap toc" aria-label="Sections">{nav}</nav>
<main class="wrap">
{parts}
</main>
<footer class="wrap foot"><a class="back" href="../../index.html#work">All work</a></footer>'''.format(
        field=esc(FIELD_NAME.get(front.get('field', ''), front.get('field', ''))), kind=kind, status=status, title=esc(title), lead=inline(sec.get('Lead', '')),
        facts=''.join(facts), actions=actions, nav=nav, parts='\n'.join(parts),
        leadfig=('<div class="wrap">%s</div>' % figure(lead, True)) if lead else '')
    open(os.path.join(out, 'index.html'), 'w', encoding='utf-8', newline='\n').write(page(title, sec.get('One line', ''), body))

    if paper:
        md = open(os.path.join(SRC, folder, 'paper.md'), encoding='utf-8').read()
        h1 = re.match(r'# (.+)\n', md)
        rest = md[h1.end():] if h1 else md
        chunks = re.split(r'\n(?=## )', rest)
        html_parts = []
        for ch in chunks:
            hm = re.match(r'## (.+)\n', ch)
            if hm:
                html_parts.append('<section class="part"><h2>%s</h2><div class="part-body">%s</div></section>' % (inline(hm.group(1)), render(re.sub(r'\s*\(MISSING\)', '', ch[hm.end():]), keep_sources=True)))
            elif ch.strip():
                html_parts.append('<div class="intro">%s</div>' % render(re.sub(r'\s*\(MISSING\)', '', ch), keep_sources=True))
        pbody = '''<header class="wrap top">
<a class="back" href="index.html">{short}</a>
<p class="field">Full write-up</p>
<h1 class="paper-title">{title}</h1>
</header>
<main class="wrap paper">
{parts}
</main>
<footer class="wrap foot"><a class="back" href="index.html">{short}</a></footer>'''.format(short=esc(title), title=inline(h1.group(1) if h1 else title), parts='\n'.join(html_parts))
        pbody = pbody.replace('images/', 'img/').replace('.png</code>', '.jpg</code>')
        open(os.path.join(out, 'paper.html'), 'w', encoding='utf-8', newline='\n').write(page(title + ', full write-up', sec.get('One line', ''), pbody))

    return {'slug': slug, 'title': title, 'field': front.get('field'), 'line': sec.get('One line', ''),
            'kind': front.get('kind', ''), 'built_with': front.get('built_with', '')}


built = {c[0]: build_case(*c) for c in CASES if os.path.exists(os.path.join(SRC, c[0], 'entry.md'))}
# Badges shown next to a project's name, as in the GitHub profile README: (label, value, background, text colour),
# or a list of them for more than one badge.
BADGES = {
    'sigma-engine': ('', 'LIVE', '#E5534B', '#fff'),
    'open-duck-mini-v2': ('', 'LIVE', '#E5534B', '#fff'),
    'object-finder-bot': ('', 'LIVE', '#E5534B', '#fff'),
    '3ddsg-drone-navigation': ('', 'LIVE', '#E5534B', '#fff'),
    'interview-prep-agent': ('Awarded by', 'Upstage', '#D4A72C', '#1b1b1b'),
    'paper-review-deck': ('Under review by', 'Anthropic', '#D97757', '#fff'),
    'deep-report-pipeline': ('Under review by', 'Anthropic', '#D97757', '#fff'),
    'impact-bridge': ('', 'LIVE', '#E5534B', '#fff'),
    'ibul-anbu': ('Awarded by', 'UOS', '#D4A72C', '#1b1b1b'),
    'first-wrong-step': [('', 'ON SALE', '#2DA44E', '#fff'), ('', 'Top 0.01%', '#8957E5', '#fff')],
}


# Short lines for the main list; the full story is on each case page.
LINE_OVERRIDE = {
    'open-duck-mini-v2': 'A 3D-printed robot, taught to walk.',
    'object-finder-bot': 'Ask where it is. It drives there.',
    '3ddsg-drone-navigation': 'Room to room by scene graph.',
    'sigma-engine': 'AI agents trade. Code holds the risk.',
    'interview-prep-agent': 'Filings in, checked interview questions out.',
    'deep-report-pipeline': 'Any topic to a checked A4 report.',
    'paper-review-deck': 'Papers to a reproduced review talk.',
    'career-log': 'Daily notes into career insight.',
    'steps-before-crashes': "Where Seoul's older pedestrians get hit.",
    'disaster-library-whitepaper': 'Old disaster news, new library handbooks.',
    'data-engineering-fundamentals': '16 weeks, Python to Databricks.',
    'gangil-evacuation-simulation': 'Smoke arrival vs. escape time.',
    'impact-bridge': 'Student marketers for social enterprises.',
    'first-wrong-step': 'Homework checks and problem picks, automated for teachers.',
    'ibul-anbu': 'Fresh bedding for parents, paid by children.',
    'pm-decision-making': 'Problem framing and MVP scoping.',
    'branding-in-seongsu': "A home for Seongsu's vanishing leather craft.",
    'digital-media-ii': 'Rhino Python to a Seoul game board.',
    'thank-you-plaque': "Students' thanks, set in a plaque.",
}


def P(folder):
    b = built[folder]
    return (FIELD_NAME.get(b['field'], b['field']), 'projects/%s/' % b['slug'], b['title'], LINE_OVERRIDE.get(b['slug'], b['line']), b['kind'] == 'coursework')


ROWS = [P(c[0]) for c in CASES if os.path.exists(os.path.join(SRC, c[0], 'entry.md'))]
FIELD_ORDER = ['Robotics', 'Agents', 'Data', 'Business', 'Design']
def is_live(href):
    badges = BADGES.get(href.split('/')[1]) or []
    return any(b[1] == 'LIVE' for b in ([badges] if isinstance(badges, tuple) else badges))


# Fields in their set order; within a field, LIVE projects come first.
ROWS.sort(key=lambda r: (FIELD_ORDER.index(r[0]) if r[0] in FIELD_ORDER else 99, not is_live(r[1])))

out = ['<ul class="groups">']
current = None
for field, href, title, line, course in ROWS:
    if field != current:
        if current:
            out.append('</ul></li>')
        out.append('<li class="group"><span class="field">%s</span><ul class="items">' % esc(field))
        current = field
    tag = ''
    name = '<a class="name" href="%s">%s</a>' % (esc(href), esc(title))
    badges = BADGES.get(href.split('/')[1]) or []
    if isinstance(badges, tuple):
        badges = [badges]
    if badges:
        pills = ''.join('<span class="pill" style="--p:%s;--pi:%s">%s%s</span>' % (bg, fg, '<span class="pk">%s</span>' % esc(k) if k else '', esc(v)) for k, v, bg, fg in badges)
        name = '<span class="title">%s%s</span>' % (name, pills)
    out.append('<li>%s<span class="line">%s%s</span></li>' % (name, esc(line), tag))
out += ['</ul></li>', '</ul>']

idx_path = os.path.join(SITE, 'index.html')
idx = open(idx_path, encoding='utf-8').read()
a = idx.index('<ul class="groups">')
b = idx.index('</ul>\n</div>\n</section>', a)
idx = idx[:a] + '\n'.join(out) + idx[b + len('</ul>'):]
if 'id="work"' not in idx:
    idx = idx.replace('<section class="sec fade" aria-label="Projects">', '<section class="sec fade" id="work" aria-label="Projects">', 1)
if '.tag{' not in idx:
    idx = idx.replace('.items .line{color:var(--color-ink-2)}',
                      '.items .line{color:var(--color-ink-2)}\n.tag{display:inline-block;margin-left:var(--space-sm);padding:0 0.375rem;border:var(--rule-hair) solid var(--color-rule-2);font-size:0.75rem;color:var(--color-muted);vertical-align:0.1em;white-space:nowrap}', 1)

# Words the opening tree and the sentence are set in: every project title and the tools in its entry.
NEW_WORDS = ['BrandingInSeongsu', 'Revit', 'Pathfinder', 'FDS', 'EvacuationSimulation', 'DigitalMedia', 'Grasshopper', 'Rhino',
             'QGIS', 'ThankYouPlaque', 'Illustrator', 'FirstWrongStep', 'FewShot', 'SymPy', 'SQLite', 'IbulAnbu', 'ImpactBridge',
             'Enactus', 'PMDecisionMaking', 'PRD', 'DataEngineering', 'Docker', 'PostgreSQL']
for m in list(re.finditer(r"var WORDS = \[(.*?)\];", idx)):
    have = re.findall(r"'([^']+)'", m.group(1))
    add = [w for w in NEW_WORDS if w not in have]
    if add:
        new = m.group(0)[:-2] + ', ' + ', '.join("'%s'" % w for w in add) + '];'
        idx = idx.replace(m.group(0), new, 1)
open(idx_path, 'w', encoding='utf-8', newline='\n').write(idx)
print('built', len(built), 'case pages;', len(ROWS), 'rows')
