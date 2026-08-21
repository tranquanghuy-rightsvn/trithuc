#!/usr/bin/env python3
"""
Chuyen du lieu 1 lan tu CMS Flask/pywebview cu (html/data/*.json trong repo goc) sang
schema moi cua remake/ (data/website.json, data/posts.json + data/posts/<id>.json,
data/pages.json). Chi chay 1 lan luc migrate; sau khi da chuyen sang GAS, moi thay doi
di qua GAS (ghi thang vao remake/data qua GitHub Contents API), khong chay lai script nay.

Chay:
    python3 remake/scripts/migrate_from_flask_cms.py
(gia dinh chay tu thu muc goc cua repo trithucworld, canh remake/ va html/ cu)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # remake/
OLD_DATA = ROOT.parent / "html" / "data"  # html/data/ cua CMS Flask cu
NEW_DATA = ROOT / "data"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    website = load(OLD_DATA / "website.json")
    posts = load(OLD_DATA / "posts.json")
    pages = load(OLD_DATA / "pages.json")

    # them next_category_id de cap phat id bat bien cho category (fix bug renumber-khi-xoa
    # cua ban goc - xem README.md muc "Category ID bat bien")
    max_cat_id = max((c.get("id", 0) for c in website.get("categories", [])), default=0)
    website["next_category_id"] = max_cat_id + 1
    dump(NEW_DATA / "website.json", website)

    index = []
    for p in posts:
        index.append({
            "id": p["id"],
            "title": p["title"],
            "url": p["url"],
            "description": p.get("description", ""),
            "keywords": p.get("keywords", ""),
            "category": p.get("category"),
            "image": p.get("image", {}),
            "created_at": p.get("created_at", ""),
        })
        dump(NEW_DATA / "posts" / ("%s.json" % p["id"]), {"id": p["id"], "content": p.get("content", "")})
    dump(NEW_DATA / "posts.json", index)

    dump(NEW_DATA / "pages.json", pages)

    print("Migrated: %d posts, %d pages, %d categories -> %s"
          % (len(posts), len(pages), len(website.get("categories", [])), NEW_DATA))


if __name__ == "__main__":
    main()
