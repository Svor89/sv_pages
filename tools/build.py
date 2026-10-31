"""Собирает общие части страниц: стили, скрипты и набор SVG-иконок (система — design.md).

1. Между <!--base-->…<!--/base--> (в <head>) кладёт <script> из tools/head.js (тема до отрисовки)
   и <style> из tools/base.css; между <!--base-js-->…<!--/base-js--> (в конце <body>) — <script> из tools/base.js.
   Стили конкретной страницы — свой <style> после <!--/base-->, только на токенах.
2. Иконки: страница ссылается как <svg class="i"><use href="#i-ИМЯ"/></svg>, рисунки — в скрытом <svg> между
   <!--icons--> и <!--/icons-->. Кладёт туда ровно используемые иконки из tools/icons/ИМЯ.svg (+ i-check: его
   подставляет скрипт копирования).

Новая иконка: скачать из Font Awesome Free 6.4.0 (CC BY 4.0) в tools/icons, напр.
  curl -o tools/icons/house.svg https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.4.0/svgs/solid/house.svg
(regular/ и brands/ — так же), затем: python tools/build.py            (все .html в корне)
                                   python tools/build.py "файл.html"   (одна страница)
"""
import glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, 'tools')
LIB = os.path.join(TOOLS, 'icons')
ICONS = re.compile(r'<!--icons-->.*?<!--/icons-->', re.S)
BASE = re.compile(r'<!--base-->.*?<!--/base-->', re.S)
BASE_JS = re.compile(r'<!--base-js-->.*?<!--/base-js-->', re.S)
SKIP = {'index.html'}   # заглушка корня GitHub Pages


def read(name):
    return open(os.path.join(TOOLS, name), encoding='utf-8').read().strip().replace('\r\n', '\n')


def symbol(name):
    path = os.path.join(LIB, name + '.svg')
    if not os.path.exists(path):
        sys.exit('нет иконки: ' + path)
    s = open(path, encoding='utf-8').read()
    vb = re.search(r'viewBox="([^"]+)"', s).group(1)
    d = ''.join(re.findall(r'<path d="([^"]+)"', s))
    return '<symbol id="i-%s" viewBox="%s"><path d="%s"/></symbol>' % (name, vb, d)


def sync(page):
    text = open(page, 'rb').read().decode('utf-8')
    name = os.path.basename(page)
    if not (BASE.search(text) and BASE_JS.search(text) and ICONS.search(text)):
        print('%s: нет меток <!--base-->, <!--base-js--> или <!--icons-->, пропуск' % name)
        return
    nl = '\r\n' if '\r\n' in text else '\n'
    head = '<!--base--><script>%s</script>\n<style>\n%s\n</style><!--/base-->' % (read('head.js'), read('base.css'))
    js = '<!--base-js--><script>\n%s\n</script><!--/base-js-->' % read('base.js')
    out = BASE.sub(lambda m: head.replace('\n', nl), text)
    out = BASE_JS.sub(lambda m: js.replace('\n', nl), out)
    body = BASE_JS.sub('', ICONS.sub('', out))
    names = sorted(set(re.findall(r'href="#i-([a-z0-9-]+)"', body)) | ({'check'} if 'data-copy' in body else set()))
    block = ('<!--icons--><svg xmlns="http://www.w3.org/2000/svg" style="display:none">' + nl
             + '<!-- Font Awesome Free 6.4.0 by @fontawesome, CC BY 4.0 -->' + nl
             + nl.join(symbol(n) for n in names) + nl + '</svg><!--/icons-->')
    out = ICONS.sub(lambda m: block, out)
    if out != text:
        open(page, 'wb').write(out.encode('utf-8'))
    print('%s: %d иконок, %d байт' % (name, len(names), len(out.encode('utf-8'))))


pages = sys.argv[1:] or [p for p in glob.glob(os.path.join(ROOT, '*.html')) if os.path.basename(p) not in SKIP]
for p in pages:
    sync(p)
