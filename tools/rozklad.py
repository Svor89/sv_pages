"""Розклад занять з Excel (форма ІПОЗН: Тиждень | День | Пара | групи…) → дані сторінки Rozklad.html.

Новий розклад:  python tools/rozklad.py "C:\\шлях\\Розклад_….xlsx"  [сторінка.html]
Дані кладе між <!--data-->…<!--/data--> як JSON у <script type="application/json" id="data">.
Скрипт сторінки сам рахує «сьогодні / минуло / зараз / далі» — правити HTML не треба.

Формат JSON (компактно, щоб сторінка важила мало):
  groups — назви груп (стовпці з рядка заголовка), days — [дата ISO, тиждень],
  subj / teach — довідники назв і викладачів,
  L — заняття: [день, початок, кінець, № пари, маска груп (+32 — об'єднана клітинка: весь потік),
                 предмет, тип, викладач, примітка або ""].
Типи: pz практичне, sem семінар, lek лекція, kons консультація, zal залік, ekz екзамен.
"""
import json, os, re, sys
import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = re.compile(r'<!--data-->.*?<!--/data-->', re.S)
TYPES = {'пз': 'pz', 'сем': 'sem', 'лекція': 'lek', 'консультація': 'kons', 'залік': 'zal', 'екзамен': 'ekz'}
ROMAN = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8}
FIX = {'інстурменти': 'інструменти'}          # явні описки в назвах
CELL = re.compile(r'^(.*?)\s+(\S+),\s*СУДН\s*"?Moodle"?\s*,\s*(.*?)\s*(?:\(\s*з\s*(\d{1,2})[.:](\d\d)\s*\)?)?$')


def clean(s):
    return ' '.join(str(s).split())


def main(xlsx, page):
    ws = openpyxl.load_workbook(xlsx, data_only=True).active
    rows = list(ws.iter_rows(values_only=True))
    hdr = next(i for i, r in enumerate(rows) if r and clean(r[2] or '') == 'Пара')
    groups = [clean(v) for v in rows[hdr][3:] if v]
    ng = len(groups)
    merged = {}                                   # (рядок, стовпець) → ширина об'єднання по групах
    for m in ws.merged_cells.ranges:
        if m.min_row > hdr + 1 and m.min_col >= 4:
            merged[(m.min_row, m.min_col)] = m.max_col - m.min_col + 1

    days, subj, teach, L, warn = [], [], [], [], []
    week = None

    def idx(lst, v):
        if v not in lst:
            lst.append(v)
        return lst.index(v)

    for ri in range(hdr + 1, len(rows)):
        r = rows[ri]
        if r[0] is not None and str(r[0]).strip().isdigit():
            week = int(str(r[0]).strip())
        if r[1]:
            m = re.match(r'(\d\d)\.(\d\d)\.(\d{4})', clean(r[1]))
            if not m:
                break                              # підписи під таблицею
            days.append(['%s-%s-%s' % (m.group(3), m.group(2), m.group(1)), week])
        if not r[2] or not days:
            continue
        slot = clean(r[2])
        t = re.search(r'(\d{1,2})[.:](\d\d)\s+(\d{1,2})[.:](\d\d)', slot)
        if not t:
            warn.append('рядок %d: не розібрано час «%s»' % (ri + 1, slot)); continue
        start, end = '%d:%s' % (int(t.group(1)), t.group(2)), '%d:%s' % (int(t.group(3)), t.group(4))
        pair = ROMAN.get(slot.split()[0], 0)
        for gi in range(ng):
            v = r[3 + gi]
            if v is None or not clean(v):
                continue
            text = clean(v)
            for a, b in FIX.items():
                text = text.replace(a, b)
            span = merged.get((ri + 1, 4 + gi), 1)
            mask = sum(1 << k for k in range(gi, min(ng, gi + span)))
            if span >= ng:
                mask |= 32
            m = CELL.match(text)
            if m and m.group(2).lower() in TYPES:
                name, kind, who = m.group(1), TYPES[m.group(2).lower()], m.group(3)
                note = 'початок о %d:%s' % (int(m.group(4)), m.group(5)) if m.group(4) else ''
            else:
                warn.append('рядок %d, %s: формат не розпізнано — «%s»' % (ri + 1, groups[gi], text))
                name, kind, who, note = text, '', '', ''
            L.append([len(days) - 1, start, end, pair, mask, idx(subj, name), kind, idx(teach, who), note])

    # сторінка показує лише свої групи: <main data-groups="1,3"> (номери стовпців груп, з 1; перша — основна)
    text = open(page, 'rb').read().decode('utf-8')
    g = re.search(r'data-groups="([\d,\s]+)"', text)
    keep = [int(x) - 1 for x in g.group(1).split(',')] if g else list(range(ng))
    L2 = []
    for l in L:
        mask = sum(1 << j for j, gi in enumerate(keep) if l[4] >> gi & 1)
        if mask:
            L2.append(l[:4] + [mask | (l[4] & 32)] + l[5:])
    used_s = sorted({l[5] for l in L2}); used_t = sorted({l[7] for l in L2})
    for l in L2:
        l[5], l[7] = used_s.index(l[5]), used_t.index(l[7])
    data = {'groups': [groups[i] for i in keep], 'days': days, 'subj': [subj[i] for i in used_s],
            'teach': [teach[i] for i in used_t], 'L': L2}
    L = L2
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    if not DATA.search(text):
        sys.exit('%s: немає міток <!--data-->…<!--/data-->' % page)
    block = '<!--data--><script type="application/json" id="data">%s</script><!--/data-->' % js
    open(page, 'wb').write(DATA.sub(lambda m: block, text).encode('utf-8'))
    for w in warn:
        print('увага:', w)
    print('%s: %d днів, %d занять, групи: %s' % (os.path.basename(page), len(days), len(L), ', '.join(data['groups'])))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'Rozklad.html'))
