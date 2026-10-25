"""Пересобирает набор SVG-иконок внутри страниц.

Страница ссылается на иконку как <svg class="i"><use href="#i-ИМЯ"/></svg>, сами рисунки лежат в одном
скрытом <svg> между метками <!--icons--> и <!--/icons-->. Скрипт кладёт туда ровно те иконки, что
используются (из tools/icons/ИМЯ.svg), — лишних байт нет, недостающих тоже.

Новая иконка: скачать из Font Awesome Free 6.4.0 (CC BY 4.0) в tools/icons, напр.
  curl -o tools/icons/house.svg https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.4.0/svgs/solid/house.svg
(regular/ и brands/ — так же), затем: python tools/icons.py            (все .html в корне)
                                   python tools/icons.py "файл.html"   (одна страница)
"""
import glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, 'tools', 'icons')
BLOCK = re.compile(r'<!--icons-->.*?<!--/icons-->', re.S)


def symbol(name):
    path = os.path.join(LIB, name + '.svg')
    if not os.path.exists(path):
        sys.exit('нет иконки: ' + path)
    s = open(path, encoding='utf-8').read()
    vb = re.search(r'viewBox="([^"]+)"', s).group(1)
    d = ''.join(re.findall(r'<path d="([^"]+)"', s))
    return '<symbol id="i-%s" viewBox="%s"><path d="%s"/></symbol>' % (name, vb, d)


def sync(page):
    raw = open(page, 'rb').read()
    text = raw.decode('utf-8')
    if not BLOCK.search(text):
        print('%s: нет меток <!--icons-->, пропуск' % os.path.basename(page))
        return
    body = BLOCK.sub('', text)
    names = sorted(set(re.findall(r'href="#i-([a-z0-9-]+)"', body)))
    nl = '\r\n' if '\r\n' in text else '\n'
    block = ('<!--icons--><svg xmlns="http://www.w3.org/2000/svg" style="display:none">' + nl
             + '<!-- Font Awesome Free 6.4.0 by @fontawesome, CC BY 4.0 -->' + nl
             + nl.join(symbol(n) for n in names) + nl + '</svg><!--/icons-->')
    out = BLOCK.sub(lambda m: block, text)
    if out != text:
        open(page, 'wb').write(out.encode('utf-8'))
    print('%s: %d иконок, %d байт' % (os.path.basename(page), len(names), len(out.encode('utf-8'))))


pages = sys.argv[1:] or glob.glob(os.path.join(ROOT, '*.html'))
for p in pages:
    sync(p)
