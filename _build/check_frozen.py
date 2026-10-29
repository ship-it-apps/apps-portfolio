#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Garde-fou : les URL embarquées dans les apps ne doivent JAMAIS changer.

  python3 _build/check_frozen.py              # compare les fichiers figés à la branche main (git)
  python3 _build/check_frozen.py --live       # vérifie aussi que chaque URL figée répond 200 en ligne

Fichiers figés : <app>/support.html, <app>/legal/{index,privacy,terms}.html (zen24, scalequest,
mijo, ik, pip, first), css/style.css (utilisé par ces pages), assets/icons/*, ik/bareme.json (lu par l'app IK),
CNAME, .nojekyll. Plus le miroir GitHub Pages cité dans la fiche App Store de Guitar Scale Quest.
"""
import subprocess, sys, urllib.request, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS = ['zen24', 'scalequest', 'mijo', 'ik', 'pip', 'first']
FILES = [f'{a}/{p}' for a in APPS for p in ('support.html', 'legal/index.html', 'legal/privacy.html', 'legal/terms.html')]
FILES += ['css/style.css', 'ik/bareme.json', 'CNAME', '.nojekyll'] + [f'assets/icons/{a}.png' for a in APPS]
LIVE = [f'https://apps.shipit.group/{f}' for f in FILES if f not in ('CNAME', '.nojekyll')]
LIVE += ['https://ship-it-apps.github.io/apps-portfolio/scalequest/legal/terms.html',
         'https://ship-it-apps.github.io/apps-portfolio/scalequest/legal/privacy.html']

def git(*a):
    return subprocess.run(['git', *a], cwd=ROOT, capture_output=True, text=True)

def main():
    base = 'origin/main' if git('rev-parse', '--verify', 'origin/main').returncode == 0 else 'main'
    bad = []
    for f in FILES:
        if not os.path.exists(os.path.join(ROOT, f)):
            bad.append(f'SUPPRIMÉ : {f}'); continue
        if git('diff', '--quiet', base, '--', f).returncode != 0:
            bad.append(f'MODIFIÉ  : {f}')
    print(f'{len(FILES)} fichiers figés comparés à {base}.')
    if '--live' in sys.argv:
        for url in LIVE:
            try:
                req = urllib.request.Request(url, method='GET', headers={'User-Agent': 'shipit-frozen-check'})
                code = urllib.request.urlopen(req, timeout=15).status
            except Exception as ex:
                code = getattr(ex, 'code', str(ex))
            if code != 200:
                bad.append(f'EN LIGNE {code} : {url}')
        print(f'{len(LIVE)} URL vérifiées en ligne.')
    if bad:
        print('\nÉCHEC — URL figées touchées :'); [print('  ' + b) for b in bad]; sys.exit(1)
    print('OK — aucune URL figée n’a changé.')

if __name__ == '__main__':
    main()
