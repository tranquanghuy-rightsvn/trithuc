#!/usr/bin/env python3
"""
Build HTML tinh cho TrithucWorld tu data/ (chay boi GitHub Actions, chi dung Python stdlib).

Day la ban thay the cho myrender.py (Jinja2) trong CMS Flask/pywebview goc. Khong dung
templating engine - chi doc file trong templates/*.html (placeholder {{TOKEN}}) va thay
the bang string.replace(), cac phan lap lai (thanh nav, card bai viet, khoi category...)
duoc dung Python ghep chuoi truc tiep, giong het markup goc trong
templates/default/*.html cua du an Flask (xem README.md canh day de biet quy uoc).

Input:
  data/website.json          # cau hinh site + danh sach category (id bat bien)
  data/posts.json            # index nhe: moi bai KHONG kem content
  data/posts/<id>.json       # content day du tung bai (GAS ghi khi Luu)
  data/pages.json            # trang tinh, kem content (it trang, khong tach index/detail)
  templates/homepage.html, category.html, post.html, page.html
  html/images/**             # anh da duoc GAS day thang vao day

Output:
  html/<slug>.html            # 1 file phang cho MOI bai viet (dung slug lam ten file, KHONG
                               # nested folder - giong het cau truc goc html/<slug>.html)
  html/<category-slug>.html   # trang danh muc, moi trang chua TOAN BO bai trong category do
                               # (khong phan trang, dung y het ban goc)
  html/index.html             # trang chu (fully generated - khong co phan "va tai cho" vi
                               # trang chu ban goc khong co vung sua tay rieng, toan bo la
                               # slice du lieu)
  html/<page-slug>.html       # trang tinh
  html/sitemap.xml

Chay local de thu: python3 scripts/build.py
"""
import html as htmllib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "html"
DATA = ROOT / "data"
TEMPLATES = ROOT / "templates"


def esc(s):
    """Escape cho ngu canh HTML text/attribute (title, description, keywords...) - giong
    HET quy uoc escape cua MarkupSafe/Jinja2 (ban goc dung render_template mac dinh
    autoescape=True). KHONG dung html.escape() cua Python stdlib: no ma hoa nhay don
    thanh &#x27; trong khi MarkupSafe dung &#39; - lech byte that su, da phat hien khi
    doi chieu output that (xem README.md).
    KHONG dung ham nay cho 'content' bai viet/trang - noi dung do da la HTML that
    (TinyMCE xuat ra, kem entity san), phai ghi RAW giong het myrender.py dung
    Markup(...) (khong escape)."""
    s = s or ""
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&#34;").replace("'", "&#39;"))


def load_json(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def load_template(name):
    return (TEMPLATES / name).read_text(encoding="utf-8")


def render(tpl, mapping):
    out = tpl
    for key, value in mapping.items():
        out = out.replace("{{%s}}" % key, value if isinstance(value, str) else str(value))
    return out


# ---------- helpers dung chung ----------

def img(post, size):
    """post['image'] la dict {"120x80": "images/posts/<id>/thumbnails/xxx-120x80.webp", ...}
    - duong dan tuong doi, KHONG co dau / dau (giong het du lieu goc), vi moi trang deu nam
    o goc html/ (khong nested) nen khong can tinh do sau tuong doi nhu du an mau gas-mvngroup."""
    return (post.get("image") or {}).get(size, "")


def category_by_id(categories, cat_id):
    for c in categories:
        if str(c.get("id")) == str(cat_id):
            return c
    return None


def nav_categories(categories, mobile):
    if mobile:
        items = [
            '          <li>\n            <a href="./%s" title="%s">%s</a>\n          </li>'
            % (c["url"], esc(c["name"]), esc(c["name"]))
            for c in categories
        ]
    else:
        items = [
            '          <li class="parent">\n            <a href="./%s" title="%s">%s</a>\n          </li>'
            % (c["url"], esc(c["name"]), esc(c["name"]))
            for c in categories
        ]
    return "\n".join(items)


def footer_page_links(pages):
    return "\n".join(
        '            <li>\n              <a href="/%s">%s</a>\n            </li>' % (p["url"], esc(p["title"]))
        for p in pages
    )


# Free text - admin soan bang TinyMCE trong tab Cai dat website (website.footer_contact_html),
# RAW HTML khong escape (giong content bai viet). TinyMCE xuat moi dong thanh <p>, nen khung
# chua la <div class="footer-contact-list"> (KHONG phai <ul>) - xem CSS ".footer-contact-list"
# trong tung template. Gia tri mac dinh (neu field chua duoc set) dung <p>, khop dung khung.
DEFAULT_FOOTER_CONTACT = (
    '            <p>Email: <a href="mailto:contact@trithucworld.com">contact@trithucworld.com</a></p>\n'
    '            <p>Hotline: <a href="tel:0964074043">0964 074 043</a></p>\n'
    '            <p>Zalo: <a href="https://zalo.me/0964074043">Quang Huy</a></p>\n'
    '            <p>Địa chỉ: Rinky Home, 280/7 Trưng Nữ Vương, Đà Nẵng, Việt Nam</p>'
)


def footer_contact(website):
    return website.get("footer_contact_html") or DEFAULT_FOOTER_CONTACT


def article_tags(keywords):
    # KHONG strip tung tag - ban goc cung khong strip ({{ tag }} tren post.keywords.split(','))
    return "\n".join('    <meta property="article:tag" content="%s">' % esc(tag) for tag in (keywords or "").split(","))


# ---------- card renderers: giu nguyen tung ky tu markup so voi templates/default/*.html goc ----------

def home_col1_card(p):
    return ('          <article class="post">\n'
            '              <a href="/%s">\n'
            '                <img src="%s" alt="%s" fetchpriority="high" width="480" height="320">\n'
            '              </a>\n'
            '              <div class="body">\n'
            '              <h3><a href="/%s">%s</a></h3>\n'
            '              <p>%s</p>\n'
            '            </div>\n'
            '          </article>') % (p["url"], img(p, "480x320"), esc(p["title"]), p["url"], esc(p["title"]), esc(p.get("description", "")))


def home_col2_card(p):
    return ('          <article class="post">\n'
            '              <a href="/%s">\n'
            '                <img src="%s" alt="%s">\n'
            '              </a>\n'
            '              <div class="body">\n'
            '              <h3><a href="/%s">%s</a></h3>\n'
            '            </div>\n'
            '          </article>') % (p["url"], img(p, "240x160"), esc(p["title"]), p["url"], esc(p["title"]))


def home_col3_card(p):
    return ('        <article class="post">\n'
            '            <a href="/%s">\n'
            '              <img src="%s" alt="%s">\n'
            '            </a>\n'
            '            <div class="body">\n'
            '              <h3><a href="/%s">%s</a></h3>\n'
            '          </div>\n'
            '          </article>') % (p["url"], img(p, "120x80"), esc(p["title"]), p["url"], esc(p["title"]))


def slider_item(p):
    return ('            <div class="slide-4-item">\n'
            '                  <a href="/%s">\n'
            '                    <img src="%s" alt="%s">\n'
            '                  </a>\n'
            '                  <h3><a href="/%s">%s</a></h3>\n'
            '                  <p class="slide-desc">%s</p>\n'
            '                </div>') % (p["url"], img(p, "240x160"), esc(p["title"]), p["url"], esc(p["title"]), esc(p.get("description", "")))


def home_main_post(p):
    """posts[8:14] o trang chu - link boc ca article (giong category variant A)."""
    return ('          <a href="/%s">\n'
            '            <article class="main-post">\n'
            '              <img src="%s" alt="%s">\n'
            '              <div class="main-content">\n'
            '                <h3>%s</h3>\n'
            '                <p>%s</p>\n'
            '              </div>\n'
            '            </article>\n'
            '          </a>') % (p["url"], img(p, "240x160"), esc(p["title"]), esc(p["title"]), esc(p.get("description", "")))


def home_side_post(p):
    return ('              <article class="side-post">\n'
            '                <a href="/%s">\n'
            '                  <img src="%s" alt="%s">\n'
            '                  <h3>%s</h3>\n'
            '                </a>\n'
            '              </article>') % (p["url"], img(p, "120x80"), esc(p["title"]), esc(p["title"]))


def category_post_card(p):
    """Card dau tien cua 1 category-block o trang chu (.category-post)."""
    return ('              <a href="/%s">\n'
            '                  <div class="category-post">\n'
            '                    <img src="%s" alt="%s">\n'
            '                    <h3>%s</h3>\n'
            '                    <p>%s</p>\n'
            '                  </div>\n'
            '                </a>') % (p["url"], img(p, "240x160"), esc(p["title"]), esc(p["title"]), esc(p.get("description", "")))


def cate_side_post(p):
    return ('              <a href="/%s">\n'
            '                <article>\n'
            '                  <h3>%s</h3>\n'
            '                  <img src="%s" alt="%s">\n'
            '                </article>\n'
            '              </a>') % (p["url"], esc(p["title"]), img(p, "120x80"), esc(p["title"]))


def homepage_category_block(category, posts, even):
    """1 <section class="category ..."> - dung cho 6 khoi category[1..6] o trang chu."""
    if category is None:
        return ""
    cat_posts = [p for p in posts if str(p.get("category")) == str(category.get("id"))]
    first = cat_posts[:1]
    rest = cat_posts[1:5]  # loop.index > 1 and <= 5 => item thu 2..5
    first_html = category_post_card(first[0]) if first else ""
    side_html = "\n".join(cate_side_post(p) for p in rest)
    cls = "category cate-even" if even else "category"
    return ('        <section class="%s">\n'
            '          <div class="category-header">\n'
            '            <h2>\n'
            '              <a href="%s">%s</a>\n'
            '            </h2>\n'
            '          </div>\n'
            '          <div class="category-content">\n'
            '%s\n'
            '            <div class="cate-side-posts">\n'
            '%s\n'
            '            </div>\n'
            '          </div>\n'
            '        </section>') % (cls, category.get("url", ""), esc(category.get("name", "")), first_html, side_html)


def featured_item(p):
    """Sidebar 'Bai viet noi bat' trong trang bai viet (suggested_posts[:3])."""
    return ('            <article class="featured-item">\n'
            '                <a href="/%s">\n'
            '                  <img src="%s" alt="%s">\n'
            '                </a>\n'
            '                <div class="featured-body">\n'
            '                  <h4>\n'
            '                    <a href="/%s">%s</a>\n'
            '                  </h4>\n'
            '                  <p class="f-meta">• Admin</p>\n'
            '                </div>\n'
            '              </article>') % (p["url"], img(p, "120x80"), esc(p["title"]), p["url"], esc(p["title"]))


def related_item(p):
    """'Co the ban quan tam' trong trang bai viet (related_posts[:4])."""
    return ('            <article class="related-card">\n'
            '              <a href="/%s">\n'
            '                <img src="%s" alt="%s">\n'
            '              </a>\n'
            '              <h4>\n'
            '                <a href="/%s">%s</a>\n'
            '              </h4>\n'
            '            </article>') % (p["url"], img(p, "240x160"), esc(p["title"]), p["url"], esc(p["title"]))


# ---- category.html card renderers (khac homepage o vai cho - giu dung nguyen ban) ----

def cat_featured_col1(p):
    return ('          <article class="post">\n'
            '              <a href="/%s">\n'
            '                <img src="%s" alt="%s" fetchpriority="high" width="480" height="320">\n'
            '              </a>\n'
            '              <div class="body">\n'
            '              <a href="/%s">\n'
            '                <h3>%s</h3>\n'
            '              </a>\n'
            '              <p>%s</p>\n'
            '            </div>\n'
            '          </article>') % (p["url"], img(p, "480x320"), esc(p["title"]), p["url"], esc(p["title"]), esc(p.get("description", "")))


def cat_featured_col2(p):
    return ('          <article class="post">\n'
            '            <a href="/%s">\n'
            '              <img src="%s" alt="%s">\n'
            '            </a>\n'
            '            <div class="body">\n'
            '              <a href="/%s">\n'
            '                  <h3>%s</h3>\n'
            '              </a>\n'
            '            </div>\n'
            '          </article>') % (p["url"], img(p, "240x160"), esc(p["title"]), p["url"], esc(p["title"]))


def cat_featured_col3(p):
    return ('          <a href="/%s">\n'
            '            <article class="post">\n'
            '              <img src="%s" alt="%s">\n'
            '              <div class="body">\n'
            '                <h3>%s</h3>\n'
            '              </div>\n'
            '            </article>\n'
            '          </a>') % (p["url"], img(p, "120x80"), esc(p["title"]), esc(p["title"]))


def cat_main_post_a(p):
    """posts[8:12] - link boc ca article."""
    return ('          <a href="/%s">\n'
            '            <article class="main-post">\n'
            '              <img src="%s" alt="%s">\n'
            '              <div class="main-content">\n'
            '                <h3>%s</h3>\n'
            '                <p>%s</p>\n'
            '              </div>\n'
            '            </article>\n'
            '          </a>') % (p["url"], img(p, "240x160"), esc(p["title"]), esc(p["title"]), esc(p.get("description", "")))


def cat_main_post_b(p):
    """posts[18:] - link nam trong article, boc img + main-content (khac cat_main_post_a)."""
    return ('          <article class="main-post">\n'
            '            <a href="/%s">\n'
            '              <img src="%s" alt="%s">\n'
            '              <div class="main-content">\n'
            '                <h3>%s</h3>\n'
            '                <p>%s</p>\n'
            '              </div>\n'
            '            </a>\n'
            '          </article>') % (p["url"], img(p, "240x160"), esc(p["title"]), esc(p["title"]), esc(p.get("description", "")))


def cat_side_post(p):
    return ('          <a href="/%s">\n'
            '            <article class="side-post">\n'
            '              <img src="%s" alt="%s">\n'
            '              <h3>%s</h3>\n'
            '            </article>\n'
            '          </a>') % (p["url"], img(p, "120x80"), esc(p["title"]), esc(p["title"]))


# ---------- builders ----------

def safe_get(seq, index):
    return seq[index] if 0 <= index < len(seq) else None


def build_homepage(posts, pages, website):
    categories = website.get("categories", [])
    tpl = load_template("homepage.html")

    slider_cat = safe_get(categories, 0)
    if slider_cat is not None:
        slider_posts = [p for p in posts if str(p.get("category")) == str(slider_cat.get("id"))][:8]
        slider_items = "\n".join(slider_item(p) for p in slider_posts)
        slider_name, slider_url = esc(slider_cat.get("name", "")), slider_cat.get("url", "")
    else:
        print("WARN: website.categories rong - bo qua slide-4 tren trang chu")
        slider_items, slider_name, slider_url = "", "", "#"

    pairs = [(1, 2), (3, 4), (5, 6)]
    category_blocks = []
    for i, j in pairs:
        a = homepage_category_block(safe_get(categories, i), posts, even=True)
        b = homepage_category_block(safe_get(categories, j), posts, even=False)
        if a or b:
            category_blocks.append('      <div class="categories">\n%s\n\n%s\n      </div>' % (a, b))
    if len(categories) < 7:
        print("WARN: trang chu goc gia dinh DUNG 7 category (index 0..6) cho slide-4 + 6 khoi - hien co %d, mot so khoi se bi bo qua" % len(categories))

    html = render(tpl, {
        "GOOGLE_ANALYTICS_CODE": website.get("google_analytics_code", ""),
        "LANG": website.get("lang", "vi"),
        "SITE_NAME": esc(website.get("site_name", "")),
        "AUTHOR": esc(website.get("author", "")),
        "WEBSITE_NAME": esc(website.get("name", "")),
        # ban goc dung {{website.title}} - key nay KHONG ton tai trong website.json nen
        # Jinja render rong; giu nguyen (khong tu sua thanh website.name) de match dung
        # hanh vi that cua site dang chay, xem README.md "Quirk ke thua tu ban goc".
        "WEBSITE_TITLE": esc(website.get("title", "")),
        "WEBSITE_DESCRIPTION": esc(website.get("description", "")),
        "DOMAIN_URL": website.get("domain_url", ""),
        "NAV_CATEGORIES": nav_categories(categories, mobile=False),
        "MOBILE_NAV_CATEGORIES": nav_categories(categories, mobile=True),
        "COL_1": "\n".join(home_col1_card(p) for p in posts[0:1]),
        "COL_2": "\n\n".join(home_col2_card(p) for p in posts[1:3]),
        "COL_3": "\n".join(home_col3_card(p) for p in posts[3:8]),
        "SLIDER_CATEGORY_URL": slider_url,
        "SLIDER_CATEGORY_NAME": slider_name,
        "SLIDER_ITEMS": slider_items,
        "LEFT_COL_POSTS": "\n".join(home_main_post(p) for p in posts[8:14]),
        "SIDE_POSTS": "\n".join(home_side_post(p) for p in posts[14:20]),
        "CATEGORY_BLOCKS": "\n\n".join(category_blocks),
        "FOOTER_PAGE_LINKS": footer_page_links(pages),
        "FOOTER_CONTACT": footer_contact(website),
    })
    (HTML / "index.html").write_text(html, encoding="utf-8")
    print("built html/index.html")


def build_category_page(category, posts, pages, website):
    tpl = load_template("category.html")
    categories = website.get("categories", [])
    cat_posts = [p for p in posts if str(p.get("category")) == str(category.get("id"))]

    main_posts = "\n".join(cat_main_post_a(p) for p in cat_posts[8:12])
    tail_posts = "\n".join(cat_main_post_b(p) for p in cat_posts[18:])
    main_posts_html = "\n\n".join(x for x in [main_posts, tail_posts] if x)

    html = render(tpl, {
        "GOOGLE_ANALYTICS_CODE": website.get("google_analytics_code", ""),
        "LANG": website.get("lang", "vi"),
        "SITE_NAME": esc(website.get("site_name", "")),
        "AUTHOR": esc(website.get("author", "")),
        "WEBSITE_NAME": esc(website.get("name", "")),
        "WEBSITE_DESCRIPTION": esc(website.get("description", "")),
        "DOMAIN_URL": website.get("domain_url", ""),
        "CATEGORY_NAME": esc(category.get("name", "")),
        "CATEGORY_URL": category.get("url", ""),
        "NAV_CATEGORIES": nav_categories(categories, mobile=False),
        "MOBILE_NAV_CATEGORIES": nav_categories(categories, mobile=True),
        "FEATURED_COL_1": "\n".join(cat_featured_col1(p) for p in cat_posts[0:1]),
        "FEATURED_COL_2": "\n\n".join(cat_featured_col2(p) for p in cat_posts[1:3]),
        "FEATURED_COL_3": "\n".join(cat_featured_col3(p) for p in cat_posts[3:8]),
        "MAIN_POSTS": main_posts_html,
        "SIDE_POSTS": "\n".join(cat_side_post(p) for p in cat_posts[12:18]),
        "FOOTER_PAGE_LINKS": footer_page_links(pages),
        "FOOTER_CONTACT": footer_contact(website),
    })
    out = HTML / category["url"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print("built html/%s (%d bai)" % (category["url"], len(cat_posts)))


def build_post_page(post, posts, pages, website):
    tpl = load_template("post.html")
    categories = website.get("categories", [])
    current_category = category_by_id(categories, post.get("category")) or {"name": "", "url": "#"}

    related_all = [p for p in posts if p.get("category") == post.get("category") and p["id"] < post["id"]][:6]
    related_ids = {p["id"] for p in related_all}
    suggested_all = [p for p in posts if p["id"] < post["id"] and p["id"] not in related_ids][:6]

    domain = website.get("domain_url", "")
    og_image = domain + img(post, "480x320")

    html = render(tpl, {
        "GOOGLE_ANALYTICS_CODE": website.get("google_analytics_code", ""),
        "LANG": website.get("lang", "vi"),
        "AUTHOR": esc(website.get("author", "")),
        "SITE_NAME": esc(website.get("name", "")),
        "DOMAIN_URL": domain,
        "TITLE": esc(post["title"]),
        "DESCRIPTION": esc(post.get("description", "")),
        "KEYWORDS": esc(post.get("keywords", "")),
        "OG_IMAGE": og_image,
        "POST_URL": post["url"],
        "ARTICLE_TAGS": article_tags(post.get("keywords", "")),
        "CATEGORY_NAME": esc(current_category.get("name", "")),
        "CATEGORY_URL": current_category.get("url", "#"),
        "CREATED_AT": esc(post.get("created_at", "")),
        "CONTENT": post.get("content", ""),  # raw - da la HTML that, khong escape (nhu Markup() ban goc)
        "NAV_CATEGORIES": nav_categories(categories, mobile=False),
        "MOBILE_NAV_CATEGORIES": nav_categories(categories, mobile=True),
        "FEATURED_ITEMS": "\n".join(featured_item(p) for p in suggested_all[:3]),
        "RELATED_ITEMS": "\n".join(related_item(p) for p in related_all[:4]),
        "WEBSITE_DESCRIPTION": esc(website.get("description", "")),
        "FOOTER_PAGE_LINKS": footer_page_links(pages),
        "FOOTER_CONTACT": footer_contact(website),
    })
    out = HTML / post["url"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print("built html/%s" % post["url"])


def build_page(page, pages, website):
    tpl = load_template("page.html")
    categories = website.get("categories", [])
    domain = website.get("domain_url", "")
    html = render(tpl, {
        "GOOGLE_ANALYTICS_CODE": website.get("google_analytics_code", ""),
        "LANG": website.get("lang", "vi"),
        "AUTHOR": esc(website.get("author", "")),
        "SITE_NAME": esc(website.get("name", "")),
        "DOMAIN_URL": domain,
        "PAGE_TITLE": esc(page["title"]),
        "PAGE_DESCRIPTION": esc(page.get("description", "")),
        "PAGE_KEYWORDS": esc(page.get("keywords", "")),
        "PAGE_URL": page["url"],
        # ban goc: JSON-LD image dung page.image (thuong khong ton tai -> rong), KHAC voi
        # og:image hardcode "banner.webp" (2 quy uoc khac nhau that su trong template goc,
        # giu nguyen ca 2 - xem README.md "Quirk ke thua tu ban goc").
        "PAGE_IMAGE": page.get("image", ""),
        "PAGE_CREATED_AT": esc(page.get("created_at", "")),
        "CONTENT": page.get("content", ""),
        "NAV_CATEGORIES": nav_categories(categories, mobile=False),
        "MOBILE_NAV_CATEGORIES": nav_categories(categories, mobile=True),
        "WEBSITE_DESCRIPTION": esc(website.get("description", "")),
        "FOOTER_PAGE_LINKS": footer_page_links(pages),
        "FOOTER_CONTACT": footer_contact(website),
    })
    out = HTML / page["url"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print("built html/%s" % page["url"])


def build_sitemap(posts, pages, website):
    domain = website.get("domain_url", "")
    if not domain:
        (HTML / "sitemap.xml").write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n</urlset>\n', encoding="utf-8")
        print("built html/sitemap.xml (rong - website.domain_url chua cau hinh)")
        return
    parts = ['<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    parts.append("  <url>\n    <loc>%s</loc>\n    <changefreq>yearly</changefreq>\n    <priority>1.0</priority>\n  </url>" % domain)
    for p in pages:
        parts.append("  <url>\n    <loc>%s%s</loc>\n    <changefreq>yearly</changefreq>\n    <priority>0.8</priority>\n  </url>" % (domain, p["url"]))
    for c in website.get("categories", []):
        parts.append("  <url>\n    <loc>%s%s</loc>\n    <changefreq>yearly</changefreq>\n    <priority>0.7</priority>\n  </url>" % (domain, c["url"]))
    for p in posts:
        parts.append("  <url>\n    <loc>%s%s</loc>\n    <changefreq>yearly</changefreq>\n    <priority>0.9</priority>\n  </url>" % (domain, p["url"]))
    parts.append("</urlset>")
    (HTML / "sitemap.xml").write_text("\n".join(parts) + "\n", encoding="utf-8")
    print("built html/sitemap.xml (%d bai, %d trang, %d danh muc)" % (len(posts), len(pages), len(website.get("categories", []))))


def category_pills(categories):
    return "\n".join(
        '          <a class="notfound-pill" href="./%s">%s</a>' % (c["url"], esc(c["name"]))
        for c in categories
    )


def build_404_page(pages, website):
    """html/404.html - Cloudflare Workers Static Assets serve file nay cho moi URL khong
    khop (wrangler.toml: not_found_handling = "404-page"), kem dung HTTP status 404 that
    (khac SPA fallback 200) - xem README.md."""
    tpl = load_template("404.html")
    categories = website.get("categories", [])
    html = render(tpl, {
        "GOOGLE_ANALYTICS_CODE": website.get("google_analytics_code", ""),
        "LANG": website.get("lang", "vi"),
        "WEBSITE_NAME": esc(website.get("name", "")),
        "WEBSITE_DESCRIPTION": esc(website.get("description", "")),
        "NAV_CATEGORIES": nav_categories(categories, mobile=False),
        "MOBILE_NAV_CATEGORIES": nav_categories(categories, mobile=True),
        "CATEGORY_PILLS": category_pills(categories),
        "FOOTER_PAGE_LINKS": footer_page_links(pages),
        "FOOTER_CONTACT": footer_contact(website),
    })
    (HTML / "404.html").write_text(html, encoding="utf-8")
    print("built html/404.html")


def main():
    website = load_json(DATA / "website.json", {})
    posts_index = load_json(DATA / "posts.json", [])
    pages = load_json(DATA / "pages.json", [])

    # ghep content day du tung bai tu data/posts/<id>.json (index nhe + detail rieng -
    # xem README.md muc "Vi sao tach posts.json / posts/<id>.json")
    posts = []
    for meta in posts_index:
        detail_path = DATA / "posts" / ("%s.json" % meta["id"])
        detail = load_json(detail_path, None)
        if detail is None:
            print("WARN: thieu %s - bo qua bai '%s'" % (detail_path.relative_to(ROOT), meta.get("title")))
            continue
        posts.append({**meta, "content": detail.get("content", "")})

    posts.sort(key=lambda p: p.get("id", 0), reverse=True)
    pages_sorted = sorted(pages, key=lambda p: p.get("id", 0), reverse=True)

    HTML.mkdir(parents=True, exist_ok=True)

    for post in posts:
        build_post_page(post, posts, pages_sorted, website)

    for page in pages_sorted:
        build_page(page, pages_sorted, website)

    for category in website.get("categories", []):
        build_category_page(category, posts, pages_sorted, website)

    build_homepage(posts, pages_sorted, website)
    build_404_page(pages_sorted, website)
    build_sitemap(posts, pages_sorted, website)
    print("Done: %d bai, %d trang, %d danh muc" % (len(posts), len(pages_sorted), len(website.get("categories", []))))


if __name__ == "__main__":
    main()
