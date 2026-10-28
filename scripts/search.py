#!/usr/bin/env python3
"""Search the authored skill and its source navigation; offline, stdlib only."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('query', nargs='?', default='')
    p.add_argument('--chapter', type=int, choices=range(1, 23))
    p.add_argument('--limit', type=int, default=5)
    p.add_argument('--json', action='store_true')
    a = p.parse_args()
    if not a.query.strip() and a.chapter is None:
        p.error('请输入关键词，或使用 --chapter 1..22')
    if not 1 <= a.limit <= 30:
        p.error('--limit 必须在 1..30 之间')
    aliases = {'综评': '综合评价', '中外合办': '中外合作', '三一': '三位一体',
               '定向士官': '定向培养军士', '士官': '军士', '港澳留学': '港澳'}
    terms = [aliases.get(term, term) for term in a.query.casefold().split()]
    index = json.loads((ROOT / 'references/section-index.json').read_text(encoding='utf-8'))
    results = []
    files = sorted((ROOT / 'chapters').glob('ch*.md'))
    files += [ROOT / 'references/appendices.md']
    for path in files:
        chapter = int(path.name[2:4]) if path.parent.name == 'chapters' else 0
        if a.chapter is not None and chapter != a.chapter:
            continue
        body = path.read_text(encoding='utf-8')
        title = body.splitlines()[0].lstrip('# ')
        sections = [s for s in index if s['chapter'] == chapter]
        matched = [s for s in sections if terms and all(t in s['title'].casefold() for t in terms)]
        folded = body.casefold()
        if terms and not all(t in folded or any(t in s['title'].casefold() for s in sections) for t in terms):
            continue
        score = sum(folded.count(t) + 15 * title.casefold().count(t) for t in terms) + 30 * len(matched)
        pos = min((folded.find(t) for t in terms if t in folded), default=0)
        snippet = body[max(0, pos - 55):pos + 220].replace('\n', ' ')
        results.append(dict(chapter=chapter, title=title, file=str(path.relative_to(ROOT)), score=score,
                            excerpt=snippet, matched_sections=[{k: s[k] for k in ('id','title','source_path','original_chapter')} for s in matched]))
    results.sort(key=lambda r: (-r['score'], r['chapter']))
    results = results[:a.limit]
    if a.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            print(f"[{r['chapter']:02}] {r['title']}\n  {r['file']}\n  {r['excerpt']}")
            for s in r['matched_sections']:
                print(f"  原书 {s['id']}：{s['title']} → {s['source_path']}")
        if not results:
            print('没有匹配内容；本书可能未覆盖此主题，可尝试更短的关键词。')
    return 0 if results else 1

if __name__ == '__main__':
    raise SystemExit(main())
