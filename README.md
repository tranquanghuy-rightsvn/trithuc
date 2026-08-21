# TrithucWorld — remake sang GAS + Sheets + Drive + GitHub + Cloudflare Pages

Ban thay the cho CMS Flask/pywebview goc (`main.py`, `myapi.py`, `model.py`, `myrender.py`,
`mygit.py`, `templates/default/*.html`) trong thu muc cha. Kien truc va cac quyet dinh o day
theo dung playbook skill `free-cms-static-site-pipeline` — doc file do truoc neu can hieu
*vi sao*, file nay chi ghi *quyet dinh cu the cho du an TrithucWorld*.

```
GAS (remake/gas) — CMS + auth OTP + upload anh (resize/crop bang canvas)
   │  commit qua GitHub Contents API
   ▼
repo nay (goc = remake/):
   data/website.json, data/posts.json (index), data/posts/<id>.json (content),
   data/pages.json
   html/images/**              <- GAS ghi THANG vao day (khong qua data/, tranh duplicate)
   │  push data/posts.json | data/pages.json | data/website.json (commit CHOT)
   ▼
GitHub Actions (.github/workflows/build.yml): scripts/build.py
   │  doc data/ + templates/*.html, ghi de html/**/*.html + sitemap.xml
   ▼
commit "CI: build html from data" → push
   │
   ▼
Cloudflare Pages (wrangler direct upload trong CI, khong qua git-build cua CF)
```

## Cau truc thu muc

- `templates/*.html` — **design goc, sua tay**. Lay tu `templates/default/*.html` (Jinja2)
  cua ban Flask, giu **nguyen 100% HTML/CSS**, chi thay `{% ... %}` bang placeholder
  `{{TOKEN}}`. Day la nguon thiet ke song — sua truc tiep o day khi doi giao dien.
- `scripts/build.py` — builder (Python stdlib, khong dependency ngoai), thay the
  `myrender.py`. Doc `data/` + `templates/`, ghi ra `html/`.
- `scripts/migrate_from_flask_cms.py` — **chi chay 1 lan** de chuyen du lieu tu
  `../html/data/*.json` (CMS Flask cu) sang schema moi. Sau khi da chuyen han sang GAS,
  khong chay lai script nay — moi thay doi di qua GAS.
- `data/` — nguon du lieu that (GAS ghi khi Luu/Xoa). **Khong sua tay**, build lai se mat.
- `html/` — site tinh build ra (deploy that). File `*.html` do CI ghi de moi lan build —
  khong sua tay. `html/images/**` do GAS ghi truc tiep.
- `gas/` — code Google Apps Script (deploy bang `clasp push`, KHONG qua git — xem
  `.gitignore`). Sau MOI lan sua file trong `gas/`, phai tu liet ke ro file nao doi +
  nhac `clasp push` + Deploy → **New version** (khong phai New deployment, se sinh URL moi).
- `.github/workflows/build.yml` — CI build + deploy Cloudflare Pages.

## Quy tac anh (giu dung Pillow goc, lam lai bang `<canvas>` o `gas/js.html`)

| Loai anh | Kich thuoc | Crop? | Noi xu ly |
|---|---|---|---|
| Thumbnail dai dien bai viet | 120x80, 240x160, 480x320 | **Co**, center-crop theo dung ti le roi scale | `resizeCropCanvas_()` |
| Anh chen trong content bai viet | 720 / 480 / 320 (theo chieu rong) | Khong | `resizeWidthCanvas_()` |
| Logo site | height = 80, giu ti le | Khong | `resizeHeightCanvas_()` |
| Thumbnail site (OG mac dinh trang chu) | 720x480 | **Co** | `resizeCropCanvas_()` |

Xuat `image/webp` qua `canvas.toBlob`/`toDataURL` — can trinh duyet ho tro webp o canvas
(Chrome/Edge/Firefox on; Safari cu co the thieu, chua co fallback PNG tu dong o ban nay).

## Khac biet co chu dich so voi ban goc (cai tien, khong phai loi)

1. **`data/posts.json` tach thanh index nhe + `data/posts/<id>.json` chua content** — thay
   vi 1 file `posts.json` chua ca content nhu ban Flask (moi lan Luu phai ghi lai toan bo
   file, GAS payload lon dan theo so bai). Build script tu ghep lai khi build.
2. **Category ID bat bien, khong danh so lai khi xoa** — ban goc co bug: xoa 1 category o
   giua se renumber toan bo id con lai, lam bai viet cua cac category sau bi gan nham. Sua:
   id cap phat tang dan, khong tai su dung; `deleteCategory` chan xoa neu con bai viet dung
   category do (`Code.js`).
3. **Cloudflare Pages thay Vercel**, deploy qua `wrangler pages deploy` trong GitHub Actions
   (khong qua git-integration build cua Cloudflare) — free, cho phep thuong mai, bandwidth
   khong gioi han (xem skill `hosting-and-quotas.md`). `html/vercel.json` → `html/_redirects`.
4. **CI trigger dung 3 file la commit-chot** (`data/posts.json`, `data/pages.json`,
   `data/website.json`) thay vi ca thu muc `data/**` — tranh build o trang thai do dang.
5. **`ads.txt` quan ly duoc qua CMS** (field `website.ads_txt`, tab Cai dat website trong
   `gas/app.html`) — ban goc la 1 file tinh copy tay 1 lan, khong doi duoc qua CMS. Luu y:
   `saveWebsite()` trong `Code.js` **chi ghi `html/ads.txt` khi field co noi dung** — de
   trong thi KHONG tao file va KHONG dong bo (khong tu xoa file da co san neu ban xoa
   trong field roi Luu — muon go han thi xoa file tren GitHub bang tay).
6. **Them cap quyen `admin`** (ban goc/skill mac dinh chi co `root`/`editor`/`viewer`):
   `root` > `admin` > `editor` > `viewer` (`ROLE_RANK` trong `Code.js`). `root` **chi** set
   bang sua tay Sheet `Users` (khong bao gio qua CMS, ke ca voi tai khoan admin — xem
   `CMS_MANAGEABLE_ROLES`). `admin` quan ly duoc tai khoan `editor`/`viewer` qua tab
   **"Quan ly nguoi dung"** (`listUsersForAdmin`/`saveUser`/`deleteUser`) va thay/sua duoc
   **"Cai dat website"**; `editor` sua noi dung (bai viet/danh muc/trang tinh) nhung
   **khong** thay tab Cai dat website hay Quan ly nguoi dung (an o client trong
   `bootApp()`, VA chan o server bang `requireRole_(token, "admin")` — khong chi dua vao an
   giao dien). Mục "Đăng xuất" đã bị bỏ khỏi sidebar theo yêu cầu — token vẫn sống 30 ngày
   trong `localStorage`, muốn đăng xuất tạm thời thì tự xóa key
   `trithucworld_cms_token` trong DevTools, hoặc yêu cầu thêm lại nút này nếu cần dùng
   trên máy dùng chung.

## Quirk ke thua tu ban goc (CO CHU DICH giu nguyen, khong tu sua, vi user yeu cau match hoan toan)

- **`og:title` tren trang chu luon rong** — template Jinja goc dung `{{website.title}}`,
  key nay khong ton tai trong `website.json` (chi co `website.name`) nen luon render rong.
  Giu nguyen trong `build.py` (`website.get("title","")`), khong tu doi sang `website.name`.
- **`og:image` trang tinh (page.html) hardcode `banner.webp`** (file nay khong ton tai trong
  repo goc) trong khi JSON-LD `image.url` lai dung `page.image` (thuong khong ton tai →
  rong) — 2 quy uoc khac nhau ngay trong 1 template, giu nguyen ca hai.
- **Sidebar "Bai viet noi bat" trong `page.html` la 3 bai HARDCODE cung** (khong doi theo
  tung trang), khong lay tu du lieu that. Giu nguyen trong `templates/page.html`.
- **Trang chu gia dinh DUNG 7 category** (`categories[0]` cho slide-4, `categories[1..6]`
  cho 6 khoi ben duoi) — neu it hon 7, `build.py` bo qua khoi thieu va in canh bao, khong
  crash, nhung day van la gioi han thiet ke ke thua tu ban goc (khong tu lam thanh vong lap
  linh hoat theo so luong category thuc te).
- **Escape HTML dung dung quy uoc MarkupSafe/Jinja2** (`&#39;` cho nhay don), KHONG dung
  `html.escape()` chuan cua Python (`&#x27;`) — da phat hien lech that khi doi chieu output
  voi site dang chay, xem `esc()` trong `build.py`.
- Anh chen trong `content` (HTML tu TinyMCE) da ton san entity — ghi RAW, khong escape lai
  (giong `Markup(...)` cua Jinja ban goc).

## Da xac minh khop ban goc

Da chay `scripts/build.py` tren du lieu that (migrate tu `../html/data/*.json`) va `diff`
tung file voi `../html/*.html` dang co: **khop tuyet doi byte-for-byte** cho trang bai viet
va trang chu (sau khi sua 2 loi phat hien o tren). Trang category chi lech o cho site goc
**dang stale** (chua rerender sau khi them BreadcrumbList JSON-LD vao template — ban build
moi nay dung voi template hien tai, dung hon ban da deploy). Da kiem tra `build.py` chay 2
lan lien tiep cho ket qua idempotent (khong tu sinh diff).

## Checklist truoc khi dua vao dung that

- [ ] **Tao Google Sheet** voi 2 sheet: `Users` (cot `email`, `role` — role: `viewer`/`editor`/
      `root`) va `Meta` (khong bat buoc dung, id da chuyen sang cap phat tu `posts.json`/
      `website.json`).
- [ ] Trong Apps Script Project Settings → Script Properties, dien: `SPREADSHEET_ID`,
      `GITHUB_TOKEN` (fine-grained PAT, quyen Contents read/write tren dung 1 repo),
      `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_BRANCH`.
- [ ] `clasp push` thu muc `gas/`, Deploy → **New deployment** (lan dau), sau la
      **New version** cho moi lan sua.
- [ ] Tao Cloudflare Pages project (ten khop `--project-name` trong `build.yml`), lay
      `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID`, dien vao GitHub repo → Settings →
      Secrets → Actions.
- [ ] Chay `python3 scripts/migrate_from_flask_cms.py` (tu thu muc goc du an, canh `html/`
      cu) de co du lieu that trong `remake/data/`, roi push repo nay len GitHub lan dau.
- [x] **Copy anh bai viet cu**: `../html/images/posts/**` → `remake/html/images/posts/**`
      — da copy (80MB, 1138 file), da rebuild va commit cung repo.
- [ ] Doi cac GitHub token bi lo (xem canh bao duoi) truoc khi push repo len GitHub that.

## ⚠️ Canh bao quan trong tu qua trinh lam viec nay

1. **May tung gan het dung luong o** (~150MB/228GB, tuc 100% da dung) — luc do 1 lenh
   `cp -R` copy anh bai viet (80MB) da lam ho `ENOSPC` toan bo, phai don ngay va tam bo
   qua buoc copy anh. **Cap nhat**: dia da co du cho tro lai (~1.6GB free), da copy lai
   thanh cong toan bo `../html/images/posts/**` (80MB, 1138 file) vao
   `remake/html/images/posts/` va commit. Van nen theo doi dung luong o dinh ky.
2. **Repo goc (`trithucworld/`) dang chua nhieu GitHub Personal Access Token o dang plaintext**
   trong `setup.json`, `task.xml`, `git-credentials.txt`, va comment trong `mygit.py` — da
   bao o luot trao doi truoc, nhac lai vi day la luc chuan bi push code len GitHub that:
   **revoke cac token do va tao token moi rieng cho GAS** (luu trong Script Properties, khong
   commit vao bat ky repo nao).

## Chua lam (co the them sau, tham khao `gas-backend-patterns.md` muc 9)

De giu pham vi ban dau gon, `gas/js.html` **chua** cai dat cac toi uu toc do CMS (boot-once
+ cache `localStorage` theo `updated_at`, prefetch ngam, gioi han so lan nhap sai OTP da co
nhung chua co UI quan ly user rieng). Cac pattern nay deu da mo ta chi tiet trong skill,
them dan khi thuc te can (vd editor phan nan CMS cham).
