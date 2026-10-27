#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère le site statique apps.shipit.group (pages app, blogs, accueil) en EN/FR.

Usage :  python3 _build/build.py            # génère
         python3 _build/build.py --strict   # échoue s'il reste des TODO

Règle absolue : le build n'écrit JAMAIS dans les chemins figés (support, légal, css/style.css,
assets/icons, ik/bareme.json, pip/...). Voir FROZEN ci-dessous et _build/check_frozen.py.
"""
import fnmatch, html, json, os, re, sys, datetime
from xml.sax.saxutils import escape as xesc

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from content_apps import APPS
from content_posts import POSTS, AUTHOR

SITE = 'https://apps.shipit.group'
DEFAULT_LANG = 'en'
LANGS = ['en', 'fr']
APP_ORDER = ['zen24', 'scalequest', 'mijo', 'ik']   # Pip volontairement absente
TODAY = datetime.date.today().isoformat()

FROZEN = ['*/support.html', '*/legal/*', 'css/style.css', 'assets/icons/*', 'ik/bareme.json',
          'CNAME', '.nojekyll', 'pip/*', '_template/*']

WARNINGS = []
WRITTEN = []
e = lambda s: html.escape(str(s), quote=True)

# ------------------------------------------------------------------ UI strings
UI = {
 'en': dict(apps='Apps', journal='Journal', studio='Studio', write='Contact us', features='Features', pricing='Pricing', blog='Blog', faq='FAQ',
            download='Download', dl_on='Download on the', appstore='App Store', all_apps='All our apps', the_app='The app', articles='Articles',
            support='Support', privacy='Privacy', terms='Terms of use', legal_notice='Legal notice', in_images='{} in pictures', scroll='Swipe through the App Store screenshots',
            start_free='Start for free.', try_it='Try it', blog_of='The {} blog', all_posts='All articles', faq_t='Frequently asked questions',
            other_q='Another question? Visit <a href="{}">{} support</a>.', read_more='Read the article', reading='{} read', updated='Updated', by='By',
            summary='Contents', tldr='In short', table='Summary table', related='Read next', author_bio='We design and build the SHIP IT apps, and write these guides from what we learn along the way.',
            lang_name='English', skip='Skip to content', crumbs='Breadcrumb', home='Home', french_only='App in French',
            not_found='Page not found', not_found_t='This page doesn’t exist (anymore).', back_home='Back to the apps'),
 'fr': dict(apps='Apps', journal='Journal', studio='Studio', write='Nous écrire', features='Fonctionnalités', pricing='Tarifs', blog='Blog', faq='FAQ',
            download='Télécharger', dl_on='Télécharger dans', appstore='l’App Store', all_apps='Toutes nos apps', the_app='L’app', articles='Articles',
            support='Support', privacy='Confidentialité', terms='Conditions d’utilisation', legal_notice='Mentions légales', in_images='{} en images', scroll='Faites défiler les captures de l’App Store',
            start_free='Commencez gratuitement.', try_it='Essayer', blog_of='Le blog {}', all_posts='Tous les articles', faq_t='Questions fréquentes',
            other_q='Une autre question ? Consultez <a href="{}">le support {}</a>.', read_more='Lire l’article', reading='{} de lecture', updated='Mis à jour le', by='Par',
            summary='Sommaire', tldr='En bref', table='Tableau récapitulatif', related='À lire aussi', author_bio='Nous concevons et développons les apps SHIP IT, et écrivons ces guides à partir de ce que nous apprenons en chemin.',
            lang_name='Français', skip='Aller au contenu', crumbs='Fil d’Ariane', home='Accueil', french_only='App en français',
            not_found='Page introuvable', not_found_t='Cette page n’existe pas (ou plus).', back_home='Retour aux apps'),
}
MONTHS = {'fr': ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'],
          'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']}
def human_date(d, lang):
    y, m, dd = map(int, d.split('-'))
    return f'{dd} {MONTHS[lang][m-1]} {y}' if lang == 'fr' else f'{dd} {MONTHS[lang][m-1]} {y}'

HOME = {
 'en': dict(title='SHIP IT — iOS apps for everyday life', desc='SHIP IT builds focused iPhone apps: Zen24 for Beds24 hosts, Riffo guitar lessons, Mijo meal planner and IK mileage allowances.',
            label='Independent studio · iOS apps', h1='Apps that do one thing. Really well.',
            lead='Run your Beds24 rentals, learn guitar scales, plan the week’s dinners, claim your mileage. iPhone apps, each built for a single job.',
            cta1='See our apps', cta2='Read the journal', apps_t='Our apps', apps_meta='iPhone · iOS 18 or later',
            journal_eyebrow='The journal', journal_t='Guides, comparisons, alternatives', journal_lead='Every app has its own blog. The latest articles, across all apps.',
            studio_eyebrow='The studio', studio_t='Small apps, big attention to detail.',
            principles=[('One job, one app', 'No catch-all suite: each app solves one specific problem, from the first screen to the last.'), ('Made for iPhone', 'Built for iOS 18 and later, with the gestures and conventions you already know.'), ('A human replies', 'A question, a bug, an idea: write to contact@shipit.group — we read every message.')]),
 'fr': dict(title='SHIP IT — Apps iOS pour le quotidien', desc='SHIP IT conçoit des apps iPhone utiles : Zen24 pour les hôtes Beds24, Riffo pour apprendre la guitare, Mijo pour les menus de la semaine et IK pour les indemnités kilométriques.',
            label='Studio indépendant · apps iOS', h1='Des apps qui font une chose. Très bien.',
            lead='Gérer ses locations Beds24, apprendre ses gammes, planifier les dîners, déclarer ses kilomètres. Des apps iPhone pensées chacune pour un seul usage.',
            cta1='Voir nos apps', cta2='Lire le journal', apps_t='Nos apps', apps_meta='iPhone · iOS 18 et plus',
            journal_eyebrow='Le journal', journal_t='Guides, comparatifs, alternatives', journal_lead='Chaque app a son propre blog. Les derniers articles, toutes apps confondues.',
            studio_eyebrow='Le studio', studio_t='Petites apps, grand soin du détail.',
            principles=[('Un usage, une app', 'Pas de suite fourre-tout : chaque app résout un problème précis, du premier écran au dernier.'), ('Faites pour l’iPhone', 'Conçues pour iOS 18 et plus, avec les gestes et conventions que vous connaissez déjà.'), ('Un humain répond', 'Une question, un bug, une idée : écrivez à contact@shipit.group, c’est nous qui lisons.')]),
}
HOME_APPS = {
 'en': {'zen24': ('Property management · Beds24', 'Arrivals, calendar, messages and KPIs for your Beds24 properties, in your pocket.', 'Free · Premium', '5 languages'),
        'scalequest': ('Music · Learning', 'Learn guitar step by step: you play, the app listens.', 'Subscription · 7-day trial', '3 languages'),
        'mijo': ('Food · Meal planning', 'The week’s dinners and the grocery list, ready in 30 seconds.', 'Free · Subscription', '5 languages'),
        'ik': ('Finance · French tax', 'Business trips tracked by GPS and computed with the official French mileage scale.', 'Free · Subscription', 'French')},
 'fr': {'zen24': ('Gestion locative · Beds24', 'Arrivées, calendrier, messages et KPI de vos propriétés Beds24, dans votre poche.', 'Gratuit · Premium', '5 langues'),
        'scalequest': ('Musique · Apprentissage', 'Apprenez la guitare pas à pas : vous jouez, l’app écoute.', 'Abonnement · essai 7 jours', '3 langues'),
        'mijo': ('Cuisine · Menus de la semaine', 'Les dîners de la semaine et la liste de courses, prêts en 30 secondes.', 'Gratuit · Abonnement', '5 langues'),
        'ik': ('Finances · Frais réels', 'Vos trajets pros suivis au GPS et calculés au barème officiel, export PDF compris.', 'Gratuit · Abonnement', 'Français')},
}
CARD_ART = {'zen24-vs': 'vs', 'zen24-alt': 'alt.', 'sq-pentatonique': '5×', 'mijo-menu': '30 s', 'ik-bareme': 'km'}

LEGAL_NOTICE = {
 'fr': ('mentions-legales', 'Mentions légales', [
    ('Éditeur', 'SHIP IT, SAS au capital de TODO €, immatriculée au RCS de TODO sous le numéro TODO. Siège social : TODO. Directeur de la publication : TODO. Contact : contact@shipit.group.'),
    ('Hébergement', 'GitHub, Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, États-Unis (GitHub Pages).'),
    ('Données personnelles', 'Ce site ne dépose pas de cookie et n’utilise pas d’outil de mesure d’audience. Votre choix de langue est mémorisé dans votre navigateur (stockage local) pour vous afficher la bonne version du site. Les politiques de confidentialité propres à chaque app sont disponibles depuis la page de l’app.'),
    ('Marques', 'Beds24, App Store et iPhone sont des marques de leurs propriétaires respectifs. Les apps SHIP IT ne sont ni affiliées ni approuvées par ces sociétés, sauf mention contraire.')]),
 'en': ('legal-notice', 'Legal notice', [
    ('Publisher', 'SHIP IT, SAS with a share capital of €TODO, registered with the TODO Trade and Companies Register under number TODO. Registered office: TODO. Publication director: TODO. Contact: contact@shipit.group.'),
    ('Hosting', 'GitHub, Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, USA (GitHub Pages).'),
    ('Personal data', 'This website sets no cookies and uses no analytics. Your language choice is saved in your browser (local storage) so we can show you the right version of the site. Each app’s own privacy policy is linked from its page.'),
    ('Trademarks', 'Beds24, App Store and iPhone are trademarks of their respective owners. SHIP IT apps are not affiliated with or endorsed by these companies unless stated otherwise.')]),
}

# ------------------------------------------------------------------ URLs
def root_lang(app):
    return DEFAULT_LANG if DEFAULT_LANG in APPS[app]['langs'] else APPS[app]['langs'][0]
def prefix(lang, app=None):
    if app is not None:
        return '/' if lang == root_lang(app) else f'/{lang}/'
    return '/' if lang == DEFAULT_LANG else f'/{lang}/'
def u_home(lang): return prefix(lang)
def u_app(app, lang): return f'{prefix(lang, app)}{app}/'
def u_blog(app, lang): return f'{u_app(app, lang)}blog/'
def u_post(p): return f'{u_blog(p["app"], p["lang"])}{p["slug"]}/'
def u_legal(lang): return f'{prefix(lang)}{LEGAL_NOTICE[lang][0]}/'
def u_frozen(app, page): return f'{SITE}/{app}/{page}'   # support.html, legal/privacy.html, legal/terms.html
def abs_(path): return SITE + path
def shot(app, name, lang):
    a = APPS[app]
    d = lang
    p = os.path.join(ROOT, f'assets/site/img/{d}/{a["shot_prefix"]}{name}.webp')
    if not os.path.exists(p):
        d = a.get('shot_lang_fallback', 'fr')
        WARNINGS.append(f'TODO capture {app}/{name} absente en {lang}, repli sur {d}')
    return f'/assets/site/img/{d}/{a["shot_prefix"]}{name}.webp'

def posts_for(app=None, lang=None):
    r = [p for p in POSTS if (app is None or p['app'] == app) and (lang is None or p['lang'] == lang)]
    return sorted(r, key=lambda p: p['date'], reverse=True)
def post_alts(p):
    return {q['lang']: u_post(q) for q in POSTS if q['key'] == p['key']}

# ------------------------------------------------------------------ head / chrome
LANG_SCRIPT = """<script>(function(){var d=document.documentElement,L=d.lang,A=%s,S=['en','fr'];function g(){try{return localStorage.getItem('lang')}catch(e){return null}}function s(v){try{localStorage.setItem('lang',v)}catch(e){}}var q=(new URLSearchParams(location.search).get('lang')||'').slice(0,2).toLowerCase();if(q&&A[q]){s(q);if(q!==L)location.replace(A[q]);return}if(/bot|crawl|spider|slurp|lighthouse|preview/i.test(navigator.userAgent))return;var p=g();if(p){if(p!==L&&A[p])location.replace(A[p]);return}var n=(navigator.languages&&navigator.languages.length?navigator.languages:[navigator.language||'en']).map(function(x){return String(x).slice(0,2).toLowerCase()});var w='en';for(var i=0;i<n.length;i++){if(S.indexOf(n[i])>-1){w=n[i];break}}if(w!==L&&A[w])location.replace(A[w]);document.addEventListener('click',function(ev){var a=ev.target.closest&&ev.target.closest('a[data-lang]');if(a)s(a.getAttribute('data-lang'))})})();</script>"""

def head(lang, title, desc, path, alts, jsonld, og_image, colors=None, extra=''):
    alts = alts or {lang: path}
    links = ''.join(f'<link rel="alternate" hreflang="{l}" href="{abs_(u)}">' for l, u in sorted(alts.items()))
    xdef = alts.get(DEFAULT_LANG) or alts[sorted(alts)[0]]
    links += f'<link rel="alternate" hreflang="x-default" href="{abs_(xdef)}">'
    style = ''
    if colors:
        style = '<style>:root{' + ';'.join(f'--{k}:{v}' for k, v in colors.items()) + '}</style>'
    ld = ''.join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in jsonld)
    ogl = {'en': 'en_US', 'fr': 'fr_FR'}
    return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{abs_(path)}">
{links}
{LANG_SCRIPT % json.dumps(alts)}
<meta name="theme-color" content="#F6F5F1">
<meta property="og:type" content="{'article' if '/blog/' in path and path.rstrip('/').split('/')[-1] != 'blog' else 'website'}">
<meta property="og:site_name" content="SHIP IT">
<meta property="og:locale" content="{ogl[lang]}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{abs_(path)}">
<meta property="og:image" content="{abs_(og_image)}">
<meta name="twitter:card" content="summary_large_image">
{extra}<link rel="preload" href="/assets/site/fonts/bricolage-grotesque-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/site/fonts/geist-sans-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/site/site.css">
{style}
<link rel="icon" href="/assets/site/favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="SHIP IT" href="{SITE}{prefix(lang)}feed.xml">
{ld}
</head>
<body>
<a class="skip" href="#main">{UI[lang]['skip']}</a>
'''

ARROW = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
DL = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 3v12m0 0l-5-5m5 5l5-5M5 20h14" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'

def lang_switch(lang, alts):
    if not alts or len(alts) < 2:
        return ''
    items = ''.join(f'<a href="{alts[l]}" hreflang="{l}" lang="{l}" data-lang="{l}"{" aria-current=\"true\"" if l == lang else ""}>{l.upper()}</a>' for l in LANGS if l in alts)
    return f'<div class="lang" role="group" aria-label="Language">{items}</div>'

def header_studio(lang, alts):
    t = UI[lang]
    return f'''<header class="site-header"><div class="wrap site-header__in">
<a class="brand" href="{u_home(lang)}" aria-label="SHIP IT"><span class="brand__mark" aria-hidden="true"></span><span class="brand__name">SHIP IT</span></a>
<nav class="nav" aria-label="Navigation"><a href="{u_home(lang)}#apps">{t['apps']}</a><a href="{u_home(lang)}#journal">{t['journal']}</a><a href="{u_home(lang)}#studio">{t['studio']}</a><a class="btn-store" href="mailto:contact@shipit.group">{t['write']}</a>{lang_switch(lang, alts)}</nav>
</div></header>'''

def header_app(app, lang, alts, blog=False):
    a = APPS[app]; t = UI[lang]
    if blog:
        brand = f'<a class="brand" href="{u_app(app, lang)}"><img class="icon" src="{a["icon"]}" alt="" width="36" height="36"><span class="brand__name">{e(a["name"])} <small>{t["blog"]}</small></span></a>'
        nav = f'<a href="{u_app(app, lang)}">{t["the_app"]}</a><a href="{u_blog(app, lang)}">{t["articles"]}</a>'
    else:
        brand = f'<a class="brand" href="{u_home(lang)}" aria-label="SHIP IT"><span class="brand__mark" aria-hidden="true"></span><span class="brand__name">SHIP IT</span></a>'
        nav = f'<a href="#features">{t["features"]}</a>' + (f'<a href="#pricing">{t["pricing"]}</a>' if a['i18n'][lang].get('plans') else '') + f'<a href="{u_blog(app, lang)}">{t["blog"]}</a><a href="#faq">{t["faq"]}</a>'
    return f'''<header class="site-header"><div class="wrap site-header__in">
{brand}
<nav class="nav" aria-label="{e(a["name"])}">{nav}<a class="btn-store" href="{a["store"][lang]}">{t["download"]}</a>{lang_switch(lang, alts)}</nav>
</div></header>'''

def legal_links(app, lang):
    t = UI[lang]
    return (f'<a href="{u_frozen(app, "support.html")}">{t["support"]}</a>'
            f'<a href="{u_frozen(app, "legal/privacy.html")}">{t["privacy"]}</a>'
            f'<a href="{u_frozen(app, "legal/terms.html")}">{t["terms"]}</a>')

def footer_app(app, lang):
    a = APPS[app]; t = UI[lang]
    return f'''<footer class="site-footer"><div class="wrap footer-compact">
<span>© 2026 SHIP IT · <a href="{u_home(lang)}">{t["all_apps"]}</a> · <a href="{u_blog(app, lang)}">{t["blog"]} {e(a["name"])}</a></span>
<nav aria-label="{e(a["name"])}">{legal_links(app, lang)}<a href="{u_legal(lang)}">{t["legal_notice"]}</a><a href="mailto:contact@shipit.group">contact@shipit.group</a></nav>
</div></footer>
</body>
</html>
'''

def crumbs(lang, items):
    li = []
    for i, (label, href) in enumerate(items):
        li.append(f'<li><a href="{href}">{e(label)}</a></li>' if href else f'<li aria-current="page">{e(label)}</li>')
    return f'<nav class="wrap crumbs" aria-label="{UI[lang]["crumbs"]}"><ol>{"".join(li)}</ol></nav>'

def ld_breadcrumbs(items):
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': abs_(h)} for i, (n, h) in enumerate(items)]}
def ld_faq(faq):
    return {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': r}} for q, r in faq]}
ORG = {'@type': 'Organization', 'name': 'SHIP IT', 'url': SITE + '/', 'email': 'contact@shipit.group', 'logo': SITE + '/assets/site/favicon.svg'}

def faq_html(lang, faq):
    return ''.join(f'<details><summary>{e(q)}</summary><p>{e(r)}</p></details>' for q, r in faq)

def appstore_btn(app, lang):
    t = UI[lang]
    return f'<a class="btn-appstore" href="{APPS[app]["store"][lang]}">{DL}<span><small>{t["dl_on"]}</small><strong>{t["appstore"]}</strong></span></a>'

# ------------------------------------------------------------------ writers
def is_frozen(rel):
    return any(fnmatch.fnmatch(rel, pat) for pat in FROZEN)

def write(rel, content):
    rel = rel.lstrip('/')
    if rel.endswith('/') or rel == '':
        rel += 'index.html'
    if is_frozen(rel):
        raise SystemExit(f'REFUS : le build a tenté d’écrire un fichier figé : {rel}')
    full = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    WRITTEN.append(rel)
    for m in re.finditer(r'TODO[^<"]{0,60}', content):
        WARNINGS.append(f'{rel}: {m.group(0)}')

# ------------------------------------------------------------------ OG images
def og_image(key, title, sub, colors, icon):
    rel = f'assets/site/og/{key}.png'
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return '/' + rel if os.path.exists(os.path.join(ROOT, rel)) else (icon or '/assets/icons/zen24.png')
    W, H = 1200, 630
    def hexc(h): h = h.lstrip('#'); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    img = Image.new('RGB', (W, H), hexc(colors.get('deep', '#111110')))
    d = ImageDraw.Draw(img)
    fb = '/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf'
    fr = '/usr/share/fonts/opentype/inter/Inter-Medium.otf'
    try:
        big = ImageFont.truetype(fb, 64); small = ImageFont.truetype(fr, 30)
    except Exception:
        big = small = ImageFont.load_default()
    x = 80
    if icon and os.path.exists(os.path.join(ROOT, icon.lstrip('/'))):
        ic = Image.open(os.path.join(ROOT, icon.lstrip('/'))).convert('RGBA').resize((120, 120))
        mask = Image.new('L', (120, 120), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, 119, 119), 30, fill=255)
        img.paste(ic, (x, 80), mask)
    words, lines, cur = title.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=big) > W - 2 * x: lines.append(cur); cur = w
        else: cur = t
    lines.append(cur)
    y = 250
    for ln in lines[:4]:
        d.text((x, y), ln, font=big, fill=(255, 255, 255)); y += 76
    d.text((x, H - 80), sub, font=small, fill=hexc(colors.get('ondark', '#FF7A4D')))
    d.rectangle((0, H - 12, W, H), fill=hexc(colors.get('bright', '#FF4F1A')))
    os.makedirs(os.path.dirname(os.path.join(ROOT, rel)), exist_ok=True)
    img.save(os.path.join(ROOT, rel), optimize=True)
    return '/' + rel

# ------------------------------------------------------------------ pages
STUDIO_COLORS = dict(deep='#111110', ondark='#FF7A4D', bright='#FF4F1A')

def page_home(lang):
    t = UI[lang]; h = HOME[lang]
    alts = {l: u_home(l) for l in LANGS}
    path = u_home(lang)
    apps = [a for a in APP_ORDER]
    ld = [{'@context': 'https://schema.org', **ORG}, {'@context': 'https://schema.org', '@type': 'WebSite', 'name': 'SHIP IT', 'url': abs_(path), 'inLanguage': lang},
          {'@context': 'https://schema.org', '@type': 'ItemList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'url': abs_(u_app(a, lang if lang in APPS[a]['langs'] else root_lang(a))), 'name': APPS[a]['name']} for i, a in enumerate(apps)]}]
    og = og_image(f'home-{lang}', h['h1'], 'apps.shipit.group', STUDIO_COLORS, None)
    icons = ''.join(f'<img class="icon" src="{APPS[a]["icon"]}" alt="" width="120" height="120">' for a in apps)
    rows = []
    for i, a in enumerate(apps):
        al = lang if lang in APPS[a]['langs'] else root_lang(a)
        cat, line, price, langs = HOME_APPS[lang][a]
        extra = f'<span class="pill-dark">{t["french_only"]}</span>' if al != lang else ''
        rows.append(f'''<li><a class="app-row" href="{u_app(a, al)}"{f' hreflang="{al}"' if al != lang else ''}>
<div class="app-row__id"><span class="app-row__num">{i+1:02d}</span><img class="icon" src="{APPS[a]['icon']}" alt="" width="64" height="64"><span><span class="app-row__name">{e(({'en':'IK — French mileage allowances','fr':'IK — Indemnités kilométriques'}[lang]) if a == 'ik' else APPS[a]['name'])}</span><span class="app-row__cat">{e(cat)}</span></span></div>
<p class="app-row__line">{e(line)}</p>
<div class="app-row__meta"><span style="display:flex;flex-wrap:wrap;gap:8px"><span class="pill-dark">{e(price)}</span><span class="pill-dark">{e(langs)}</span>{extra}</span><span class="app-row__go">{'Discover' if lang == 'en' else 'Découvrir'} {ARROW}</span></div>
</a></li>''')
    cards = []
    lp = [p for p in posts_for(lang=lang)]
    seen = set(); chosen = []
    for p in lp:
        if p['app'] not in seen: chosen.append(p); seen.add(p['app'])
    if lang == 'en':
        chosen += [p for p in posts_for(lang='fr') if p['app'] not in seen]
    for p in chosen[:4]:
        c = APPS[p['app']]['colors']
        cards.append(f'''<article class="post-card"><div class="post-card__art" style="background:{c['panel']};color:#fff" aria-hidden="true"><span>{e(CARD_ART.get(p['key'], ''))}</span><img class="icon" src="{APPS[p['app']]['icon']}" alt="" width="48" height="48"></div>
<div class="post-card__body"><div class="post-card__meta"><span class="chip">{e(APPS[p['app']]['name'])}</span><span>{e(p['cat'])}</span><span aria-hidden="true">·</span><span>{e(p['read'])}</span></div>
<h3 class="h3"><a href="{u_post(p)}"{f' hreflang="{p["lang"]}"' if p['lang'] != lang else ''}>{e(p['title'])}</a></h3><p class="muted" style="margin:0;font-size:15px;line-height:1.55">{e(p['desc'])}</p></div></article>''')
    princ = ''.join(f'<div><h3>{e(a)}</h3><p>{e(b)}</p></div>' for a, b in h['principles'])
    foot_cols = ''.join(f'''<div><p class="t">{e(APPS[a]['name'])}</p><a href="{u_app(a, lang if lang in APPS[a]['langs'] else root_lang(a))}">{'Overview' if lang == 'en' else 'Présentation'}</a><a href="{u_blog(a, lang if lang in APPS[a]['langs'] else root_lang(a))}">{t['blog']}</a>{legal_links(a, lang)}</div>''' for a in apps)
    body = f'''{header_studio(lang, alts)}
<main id="main">
<section class="wrap home-hero" aria-labelledby="hero-t">
<p class="dot-label">{e(h['label'])}</p>
<h1 id="hero-t" class="h-display">{e(h['h1'])}</h1>
<div class="home-hero__row"><p class="lead">{e(h['lead'])}</p><div style="display:flex;flex-wrap:wrap;gap:12px"><a class="btn btn--ink" href="#apps">{e(h['cta1'])} {ARROW}</a><a class="btn btn--ghost" href="#journal">{e(h['cta2'])}</a></div></div>
<div class="icon-row" aria-hidden="true">{icons}</div>
</section>
<section id="apps" class="apps" aria-labelledby="apps-t"><div class="wrap sect">
<div class="apps__head"><h2 id="apps-t" class="h2">{e(h['apps_t'])}</h2><p class="eyebrow" style="color:var(--dark-muted)">{e(h['apps_meta'])}</p></div>
<ul class="apps__list">{''.join(rows)}</ul>
</div></section>
<section id="journal" class="wrap sect" aria-labelledby="journal-t">
<div class="sect-head"><div style="display:flex;flex-direction:column;gap:12px"><p class="eyebrow" style="color:var(--signal-text)">{e(h['journal_eyebrow'])}</p><h2 id="journal-t" class="h2">{e(h['journal_t'])}</h2></div><p class="muted" style="margin:0;max-width:420px;font-size:17px">{e(h['journal_lead'])}</p></div>
<div class="cards">{''.join(cards)}</div>
</section>
<section id="studio" class="sect" style="border-top:1px solid var(--line)" aria-labelledby="studio-t"><div class="wrap split">
<div style="display:flex;flex-direction:column;gap:16px"><p class="eyebrow" style="color:var(--signal-text)">{e(h['studio_eyebrow'])}</p><h2 id="studio-t" class="h2" style="font-size:clamp(32px,3.6vw,48px)">{e(h['studio_t'])}</h2></div>
<div class="principles">{princ}</div>
</div></section>
</main>
<footer class="site-footer"><div class="wrap">
<div class="footer-grid">{foot_cols}</div>
<p class="wordmark" aria-hidden="true">SHIP IT<span>.</span></p>
<div class="footer-bottom"><span>© 2026 SHIP IT</span><nav aria-label="SHIP IT"><a href="mailto:contact@shipit.group">contact@shipit.group</a><a href="{u_legal(lang)}">{t['legal_notice']}</a>{''.join(f'<a href="{u_home(l)}" hreflang="{l}" lang="{l}" data-lang="{l}">{UI[l]["lang_name"]}</a>' for l in LANGS if l != lang)}</nav></div>
</div></footer>
</body>
</html>
'''
    write(path, head(lang, h['title'], h['desc'], path, alts, ld, og) + body)

def page_app(app, lang):
    a = APPS[app]; c = a['colors']; x = a['i18n'][lang]; t = UI[lang]
    alts = {l: u_app(app, l) for l in a['langs']}
    path = u_app(app, lang)
    items = [(t['home'], u_home(lang)), (a['name'], path)]
    offers = [{'@type': 'Offer', 'price': p, 'priceCurrency': cur} for p, cur in a['offers']]
    ld = [{'@context': 'https://schema.org', '@type': 'MobileApplication', 'name': x['full_name'], 'operatingSystem': 'iOS 18.0', 'applicationCategory': a['category'],
           'description': x['desc'], 'url': abs_(path), 'downloadUrl': a['store'][lang], 'image': abs_(a['icon']), 'inLanguage': lang, 'offers': offers if len(offers) > 1 else offers[0], 'publisher': ORG},
          ld_breadcrumbs(items), ld_faq(x['faq'])]
    og = og_image(f'{app}-{lang}', x['h1'], x['full_name'], c, a['icon'])
    store_id = re.search(r'id(\d+)', a['store'][lang]).group(1)
    extra = f'<meta name="apple-itunes-app" content="app-id={store_id}">\n'
    if a.get('video') and lang in a['video']:
        v, poster, *size = a['video'][lang]
        w, h = size[0] if size else (320, 569)
        ratio = f' style="aspect-ratio:{w}/{h}"' if size else ''
        media = f'<video src="{v}" poster="{poster}" autoplay muted loop playsinline preload="metadata" width="{w}" height="{h}"{ratio} aria-label="{e(x["video_label"])}"></video>'
    else:
        media = f'<img src="{shot(app, a["hero_shot"], lang)}" alt="{e(x["shot_alts"][a["shots"].index(a["hero_shot"])])}" width="660" height="1434" fetchpriority="high">'
    shots = ''.join(f'<li><img src="{shot(app, s, lang)}" alt="{e(x["shot_alts"][i])}" width="660" height="1434" loading="lazy"></li>' for i, s in enumerate(a['shots']))
    feats = ''.join(f'<div class="feature"><span class="feature__n" aria-hidden="true">{i+1:02d}</span><h3 class="h3">{e(ti)}</h3><p>{e(tx)}</p></div>' for i, (ti, tx) in enumerate(x['features']))
    hl = x['hl']
    stats = ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in hl[3])
    plans = ''
    if x.get('plans'):
        ps = []
        for name, price, text, pro, badge in x['plans']:
            if pro:
                ps.append(f'<div class="plan plan--pro"><div class="plan__head"><h3>{e(name)}</h3>{f"<span class=badge-white>{e(badge)}</span>" if badge else ""}</div><p class="plan__price">{e(price)}</p><p>{e(text)}</p><a class="btn btn--white" href="{a["store"][lang]}">{t["try_it"]}</a></div>')
            else:
                ps.append(f'<div class="plan"><h3>{e(name)}</h3><p class="plan__price">{e(price)}</p><p class="muted">{e(text)}</p><a class="btn btn--ghost" href="{a["store"][lang]}">{t["download"]}</a></div>')
        plans = f'''<section id="pricing" class="wrap sect" aria-labelledby="price-t"><div style="display:flex;flex-direction:column;gap:12px;align-items:center;text-align:center"><p class="eyebrow">{t["pricing"]}</p><h2 id="price-t" class="h2">{t["start_free"]}</h2></div><div class="plans">{"".join(ps)}</div></section>'''
    ap = posts_for(app, lang)
    mini = ''.join(f'<article class="mini-post"><span class="kind">{e(p["cat"])}</span><h3 class="h3"><a href="{u_post(p)}">{e(p["title"])}</a></h3><p>{e(p["desc"])}</p></article>' for p in ap[:3])
    blog_sec = f'''<section class="sect" style="border-top:1px solid var(--line)" aria-labelledby="blog-t"><div class="wrap"><div class="sect-head"><h2 id="blog-t" class="h2" style="font-size:clamp(32px,3.8vw,52px)">{t["blog_of"].format(e(a["name"]))}</h2><a class="link-arrow" href="{u_blog(app, lang)}">{t["all_posts"]} {ARROW}</a></div><div class="mini-posts">{mini}</div></div></section>''' if ap else ''
    body = f'''{header_app(app, lang, alts)}
<main id="main">
{crumbs(lang, [(t['home'], u_home(lang)), (a['name'], None)])}
<section class="wrap app-hero" aria-labelledby="hero-t">
<div class="app-hero__copy">
<div class="app-hero__id"><img class="icon" src="{a['icon']}" alt="" width="72" height="72"><div><strong>{e(x['full_name'])}</strong><span>{e(x['sub'])}</span></div></div>
<h1 id="hero-t" class="h-display">{e(x['h1'])}</h1>
<p class="lead">{e(x['lead'])}</p>
<div class="app-hero__cta">{appstore_btn(app, lang)}<span class="app-hero__price">{e(x['price_line'])}</span></div>
</div>
<figure class="device">{media}</figure>
</section>
<section class="sect" style="padding-top:0;overflow:hidden" aria-labelledby="shots-t"><div class="wrap">
<div class="sect-head" style="margin-bottom:28px"><h2 id="shots-t" class="h3" style="font-size:clamp(28px,3vw,40px)">{t['in_images'].format(e(a['name']))}</h2><p class="muted" style="margin:0;font-size:15px">{t['scroll']}</p></div>
<ul class="shots">{shots}</ul>
</div></section>
<section id="features" class="sect sect--paper" aria-labelledby="feat-t"><div class="wrap">
<p class="eyebrow">{t['features']}</p>
<h2 id="feat-t" class="h2" style="margin-top:12px;max-width:18ch">{e(x['feat_title'])}</h2>
<div class="features">{feats}</div>
</div></section>
<section class="sect sect--deep" aria-labelledby="hl-t"><div class="wrap split">
<div style="display:flex;flex-direction:column;gap:20px"><p class="eyebrow">{e(hl[0])}</p><h2 id="hl-t" class="h2">{e(hl[1])}</h2><p style="margin:0;max-width:480px;font-size:18px;line-height:1.55;color:var(--mutedd)">{e(hl[2])}</p></div>
<dl class="stats">{stats}</dl>
</div></section>
{plans}
{blog_sec}
<section id="faq" class="sect sect--paper" aria-labelledby="faq-t"><div class="wrap faq">
<h2 id="faq-t" class="h2" style="font-size:clamp(32px,3.8vw,52px);margin-bottom:32px">{t['faq_t']}</h2>
{faq_html(lang, x['faq'])}
<p class="muted" style="margin:24px 0 0;font-size:15px">{t['other_q'].format(u_frozen(app, 'support.html'), e(a['name']))}</p>
</div></section>
<section class="wrap sect" aria-labelledby="cta-t">
<div class="cta-panel"><h2 id="cta-t">{e(x['cta'])}</h2><a class="btn btn--white" href="{a['store'][lang]}">{t['download']} {e(a['name'])}</a></div>
<p class="fineprint">{e(x['disclaimer'])}</p>
</section>
</main>
{footer_app(app, lang)}'''
    write(path, head(lang, x['title'], x['desc'], path, alts, ld, og, c, extra) + body)

def page_blog(app, lang):
    a = APPS[app]; c = a['colors']; x = a['i18n'][lang]; t = UI[lang]
    alts = {l: u_blog(app, l) for l in a['langs']}
    path = u_blog(app, lang)
    ps = posts_for(app, lang)
    items = [(t['home'], u_home(lang)), (a['name'], u_app(app, lang)), (t['blog'], path)]
    ld = [{'@context': 'https://schema.org', '@type': 'Blog', 'name': x['blog_title'], 'url': abs_(path), 'inLanguage': lang, 'publisher': ORG,
           'blogPost': [{'@type': 'BlogPosting', 'headline': p['title'], 'url': abs_(u_post(p)), 'datePublished': p['date'], 'dateModified': p.get('updated', p['date'])} for p in ps]},
          ld_breadcrumbs(items)]
    og = og_image(f'{app}-blog-{lang}', x['blog_h1'], x['blog_title'], c, a['icon'])
    feat = ''
    rest = ps
    if ps:
        p = ps[0]; rest = ps[1:]
        fig = next((s[3] for s in p['sections'] if s[3]), None)
        art = f'<img src="{shot(app, fig[0], lang)}" alt="" width="660" height="1434" loading="lazy">' if fig else ''
        feat = f'''<article class="feature-post"><div class="feature-post__art">{art}</div><div class="feature-post__body">
<div class="post-card__meta" style="font-size:14px"><span class="chip chip--tint">{e(p['cat'])}</span><span>{t['reading'].format(e(p['read']))}</span></div>
<h2><a href="{u_post(p)}">{e(p['title'])}</a></h2><p class="muted" style="margin:0;font-size:17px;line-height:1.55">{e(p['desc'])}</p>
<a class="link-arrow" href="{u_post(p)}">{t['read_more']} {ARROW}</a></div></article>'''
    tiles = ''.join(f'''<article class="post-tile"><div class="post-card__meta"><span class="chip">{e(p['cat'])}</span><span>{e(p['read'])}</span></div><h2><a href="{u_post(p)}">{e(p['title'])}</a></h2><p>{e(p['desc'])}</p></article>''' for p in rest)
    body = f'''{header_app(app, lang, alts, blog=True)}
<main id="main">
{crumbs(lang, [(t['home'], u_home(lang)), (a['name'], u_app(app, lang)), (t['blog'], None)])}
<section class="wrap blog-hero" aria-labelledby="blog-t"><h1 id="blog-t" class="h-display">{e(x['blog_h1'])}</h1><p class="lead">{e(x['blog_lead'])}</p></section>
<div class="wrap">{feat}{f'<div class="post-list">{tiles}</div>' if tiles else '<div style="height:var(--sect)"></div>'}</div>
<section class="band" aria-labelledby="band-t"><div class="wrap band__in"><div class="band__id"><img class="icon" src="{a['icon']}" alt="" width="72" height="72"><h2 id="band-t">{e(x['cta'])}</h2></div><a class="btn btn--white" style="color:var(--ink)" href="{a['store'][lang]}">{t['download']} {e(a['name'])}</a></div></section>
</main>
{footer_app(app, lang)}'''
    write(path, head(lang, x['blog_title'], x['blog_lead'], path, alts, ld, og, c) + body)

def ik_bareme_table(lang):
    data = json.load(open(os.path.join(ROOT, 'ik/bareme.json'), encoding='utf-8'))
    n = lambda v: f'{v:.3f}'.replace('.', ',')
    eur = lambda v: f'{int(v):,}'.replace(',', '\u202f') + '\u00a0€'
    rows = []
    for kind, label in (('thermal', 'Thermique'), ('electric', '100 % électrique')):
        for cv, k in sorted(data[kind].items(), key=lambda kv: int(kv[0])):
            cvl = f'{cv} CV' if cv != '7' else '7 CV et plus'
            rows.append(f'<tr><th scope="row">{label} · {cvl}</th><td class="num">d × {n(k["a"])}</td><td class="num">(d × {n(k["b"])}) + {eur(k["c"])}</td><td class="num">d × {n(k["e"])}</td></tr>')
    cap = f'Barème des revenus {data["incomeYear"]} (déclaration 2026), tel qu’intégré à l’app IK, publié le {human_date(data["publishedOn"], "fr")}. d = distance parcourue à titre professionnel dans l’année. Vérifiez le barème officiel sur impots.gouv.fr.'
    return f'''<div class="table-box"><table><caption>{e(cap)}</caption><thead><tr><th scope="col">Véhicule</th><th scope="col">Jusqu’à 5 000 km</th><th scope="col">De 5 001 à 20 000 km</th><th scope="col">Au-delà de 20 000 km</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>'''

def page_post(p):
    app, lang = p['app'], p['lang']
    a = APPS[app]; c = a['colors']; x = a['i18n'][lang]; t = UI[lang]
    alts = post_alts(p)
    path = u_post(p)
    items = [(t['home'], u_home(lang)), (a['name'], u_app(app, lang)), (t['blog'], u_blog(app, lang)), (p['title'], path)]
    ld = [{'@context': 'https://schema.org', '@type': 'BlogPosting', 'headline': p['title'], 'description': p['desc'], 'inLanguage': lang,
           'datePublished': p['date'], 'dateModified': p.get('updated', p['date']), 'mainEntityOfPage': abs_(path),
           'author': {'@type': 'Organization', 'name': 'SHIP IT', 'url': SITE + '/'}, 'publisher': ORG,
           'image': abs_(og_image(f'post-{p["key"]}-{lang}', p['title'], a['i18n'][lang]['full_name'], c, a['icon'])),
           'about': {'@type': 'MobileApplication', 'name': x['full_name'], 'url': abs_(u_app(app, lang))}},
          ld_breadcrumbs(items), ld_faq(p['faq'])]
    og = f'/assets/site/og/post-{p["key"]}-{lang}.png'
    toc_items = [('tldr', t['tldr'])] + [(s[0], s[1]) for s in p['sections']] + [('table', t['table']), ('choose', p['choose'][0]), ('faq', t['faq_t'])]
    toc = ''.join(f'<li><a href="#{i}">{e(l)}</a></li>' for i, l in toc_items)
    secs = []
    for sid, h2, paras, fig in p['sections']:
        ps_ = [f'<p>{e(pp)}</p>' for pp in paras]
        if fig:
            ps_.insert(1, f'<figure class="figure"><img src="{shot(app, fig[0], lang)}" alt="{e(fig[1])}" width="660" height="1434" loading="lazy"><figcaption>{e(fig[2])}</figcaption></figure>')
        secs.append(f'<section id="{sid}" aria-labelledby="h-{sid}"><h2 id="h-{sid}">{e(h2)}</h2>{"".join(ps_)}</section>')
    if p['table'] == 'ik_bareme':
        table = ik_bareme_table(lang)
    else:
        tb = p['table']
        trs = ''.join(f'<tr><th scope="row">{e(r[0])}</th><td>{e(r[1])}</td><td>{e(r[2])}</td></tr>' for r in tb['rows'])
        table = f'<div class="table-box"><table><caption>{e(tb["caption"])}</caption><thead><tr>{"".join(f"<th scope=col>{e(h)}</th>" for h in tb["head"])}</tr></thead><tbody>{trs}</tbody></table></div>'
    ch = ''.join(f'<div{" class=on" if on else ""}><h3>{e(h)}</h3><p>{e(tx)}</p></div>' for h, tx, on in p['choose'][1])
    rel = [q for q in posts_for(app, lang) if q['key'] != p['key']]
    rel_html = ''.join(f'<article class="mini-post"><span class="kind">{e(q["cat"])}</span><h3 class="h3" style="font-size:22px"><a href="{u_post(q)}">{e(q["title"])}</a></h3></article>' for q in rel)
    rel_html += f'<article class="mini-post"><span class="kind">{t["the_app"]}</span><h3 class="h3" style="font-size:22px"><a href="{u_app(app, lang)}">{e(x["title"])}</a></h3></article>'
    body = f'''{header_app(app, lang, alts, blog=True)}
<main id="main">
<article>
{crumbs(lang, [(t['home'], u_home(lang)), (a['name'], u_app(app, lang)), (t['blog'], u_blog(app, lang)), (p['title'], None)])}
<header class="wrap article-head">
<span class="chip chip--tint" style="align-self:flex-start;font-size:14px;padding:6px 12px">{e(p['cat'])}</span>
<h1 class="h-display">{e(p['title'])}</h1>
<p class="chapo">{e(p['chapo'])}</p>
<div class="byline"><span>{t['by']} <strong>{e(AUTHOR[lang])}</strong></span><span aria-hidden="true">·</span><span>{t['updated']} <time datetime="{p.get('updated', p['date'])}">{human_date(p.get('updated', p['date']), lang)}</time></span><span aria-hidden="true">·</span><span>{t['reading'].format(e(p['read']))}</span></div>
</header>
<div class="wrap article-grid">
<aside class="toc-col" aria-label="{t['summary']}">
<nav class="toc" aria-labelledby="toc-t"><p id="toc-t">{t['summary']}</p><ol>{toc}</ol></nav>
<div class="side-cta"><img class="icon" src="{a['icon']}" alt="" width="48" height="48"><p class="t">{e(x['cta'])}</p><a class="btn btn--white" href="{a['store'][lang]}">App Store</a></div>
</aside>
<div class="prose">
<section id="tldr" class="tldr" aria-labelledby="h-tldr"><h2 id="h-tldr">{t['tldr']}</h2><ul>{''.join(f'<li>{b}</li>' for b in p['bref'])}</ul></section>
{''.join(secs)}
<section id="table" class="sans" aria-labelledby="h-table"><h2 id="h-table">{t['table']}</h2>{table}</section>
<section id="choose" aria-labelledby="h-choose"><h2 id="h-choose">{e(p['choose'][0])}</h2><div class="choose">{ch}</div></section>
<section id="faq" class="faq" aria-labelledby="h-faq"><h2 id="h-faq">{t['faq_t']}</h2>{faq_html(lang, p['faq'])}</section>
<section class="author" aria-label="{e(AUTHOR[lang])}"><img class="icon" src="/assets/site/favicon.svg" alt="" width="56" height="56" style="border-radius:50%"><div><p class="name">{e(AUTHOR[lang])}</p><p class="bio">{t['author_bio']}</p></div></section>
<p class="sources">{e(p['sources'])}</p>
</div>
</div>
</article>
<section class="sect sect--paper" aria-labelledby="rel-t"><div class="wrap"><h2 id="rel-t" class="h2" style="font-size:clamp(28px,3vw,40px);margin-bottom:32px">{t['related']}</h2><div class="mini-posts">{rel_html}</div></div></section>
</main>
{footer_app(app, lang)}'''
    write(path, head(lang, p['seo_title'], p['desc'], path, alts, ld, og, c) + body)

def page_legal(lang):
    slug, title, blocks = LEGAL_NOTICE[lang]
    alts = {l: u_legal(l) for l in LANGS}
    path = u_legal(lang)
    body = f'''{header_studio(lang, alts)}
<main id="main" class="wrap"><div class="legal"><h1 class="h-display">{e(title)}</h1>{''.join(f'<h2>{e(h)}</h2><p>{e(tx)}</p>' for h, tx in blocks)}</div></main>
<footer class="site-footer"><div class="wrap footer-compact"><span>© 2026 SHIP IT · <a href="{u_home(lang)}">{UI[lang]['all_apps']}</a></span><nav><a href="mailto:contact@shipit.group">contact@shipit.group</a></nav></div></footer>
</body></html>
'''
    write(path, head(lang, f'{title} — SHIP IT', title, path, alts, [], og_image(f'home-{lang}', HOME[lang]['h1'], 'apps.shipit.group', STUDIO_COLORS, None)) .replace('<meta name="viewport"', '<meta name="robots" content="noindex">\n<meta name="viewport"') + body)

def page_404():
    t = UI['en']; f = UI['fr']
    html_ = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex"><title>404 — SHIP IT</title><link rel="stylesheet" href="/assets/site/site.css"><link rel="icon" href="/assets/site/favicon.svg" type="image/svg+xml"></head>
<body><main class="wrap" style="min-height:80vh;display:flex;flex-direction:column;justify-content:center;gap:24px">
<p class="dot-label">404</p><h1 class="h-display" style="font-size:clamp(48px,8vw,104px)">{t['not_found']}</h1>
<p class="lead">{t['not_found_t']} <span lang="fr">— {f['not_found_t']}</span></p>
<div style="display:flex;gap:12px;flex-wrap:wrap"><a class="btn btn--ink" href="/">{t['back_home']}</a><a class="btn btn--ghost" href="/fr/" lang="fr" hreflang="fr">{f['back_home']}</a></div>
</main></body></html>'''
    write('404.html', html_)

def favicon():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="16" fill="#111110"/><circle cx="32" cy="32" r="9" fill="#FF4F1A"/></svg>'
    write('assets/site/favicon.svg', svg)

def feeds():
    for lang in LANGS:
        ps = posts_for(lang=lang)
        items = ''.join(f'<item><title>{xesc(p["title"])}</title><link>{abs_(u_post(p))}</link><guid>{abs_(u_post(p))}</guid><pubDate>{datetime.datetime.strptime(p["date"], "%Y-%m-%d").strftime("%a, %d %b %Y 08:00:00 +0000")}</pubDate><description>{xesc(p["desc"])}</description><category>{xesc(APPS[p["app"]]["name"])}</category></item>' for p in ps)
        write(f'{prefix(lang)}feed.xml', f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>SHIP IT</title><link>{abs_(u_home(lang))}</link><description>{xesc(HOME[lang]["journal_lead"])}</description><language>{lang}</language>{items}</channel></rss>')

def sitemap():
    entries = []  # (path, alts)
    for l in LANGS: entries.append((u_home(l), {x: u_home(x) for x in LANGS}))
    for app in APP_ORDER:
        for l in APPS[app]['langs']:
            entries.append((u_app(app, l), {x: u_app(app, x) for x in APPS[app]['langs']}))
            if posts_for(app, l): entries.append((u_blog(app, l), {x: u_blog(app, x) for x in APPS[app]['langs'] if posts_for(app, x)}))
    for p in POSTS: entries.append((u_post(p), post_alts(p)))
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for path, alts in entries:
        out.append(f'<url><loc>{abs_(path)}</loc><lastmod>{TODAY}</lastmod>')
        if len(alts) > 1:
            for l, u in sorted(alts.items()):
                out.append(f'<xhtml:link rel="alternate" hreflang="{l}" href="{abs_(u)}"/>')
            out.append(f'<xhtml:link rel="alternate" hreflang="x-default" href="{abs_(alts.get(DEFAULT_LANG, list(alts.values())[0]))}"/>')
        out.append('</url>')
    out.append('</urlset>')
    write('sitemap.xml', '\n'.join(out))
    write('robots.txt', f'User-agent: *\nAllow: /\nDisallow: /_build/\n\nSitemap: {SITE}/sitemap.xml\n')

def main():
    favicon()
    for l in LANGS:
        page_home(l); page_legal(l)
    for app in APP_ORDER:
        for l in APPS[app]['langs']:
            page_app(app, l)
            if posts_for(app, l): page_blog(app, l)
    for p in POSTS: page_post(p)
    page_404(); feeds(); sitemap()
    print(f'{len(WRITTEN)} fichiers générés.')
    if WARNINGS:
        print('\nÀ COMPLÉTER AVANT MISE EN LIGNE :')
        for w in sorted(set(WARNINGS)): print('  -', w)
        if '--strict' in sys.argv: sys.exit(1)

if __name__ == '__main__':
    main()
