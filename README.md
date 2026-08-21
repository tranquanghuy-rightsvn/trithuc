# TrithucWorld — remake sang GAS + Sheets + Drive + GitHub + Cloudflare Workers (Static Assets)

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
Cloudflare Workers + Static Assets (wrangler deploy trong CI - xem wrangler.toml)
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
- `.github/workflows/build.yml` — CI build + deploy Cloudflare (Workers Static Assets).
- `wrangler.toml` — cau hinh Cloudflare Worker (`name`, `assets.directory`) — doi ten Worker
  o day (kem sua `name` cho khop) neu can, khong sua trong `build.yml`.

## Quy tac anh (giu dung Pillow goc, lam lai bang `<canvas>` o `gas/js.html`)

| Loai anh | Kich thuoc | Crop? | Noi xu ly |
|---|---|---|---|
| Thumbnail dai dien bai viet | 120x80, 240x160, 480x320 | **Co**, center-crop theo dung ti le roi scale | `resizeCropCanvas_()` |
| Anh chen trong content bai viet | 720 / 480 / 320 (theo chieu rong) | Khong | `resizeWidthCanvas_()` |
| Logo site | height = 80, giu ti le | Khong | `resizeHeightCanvas_()` |
| Thumbnail site (OG mac dinh trang chu) | 720x480 | **Co** | `resizeCropCanvas_()` |

Xuat `image/webp` qua `canvas.toBlob`/`toDataURL` — can trinh duyet ho tro webp o canvas
(Chrome/Edge/Firefox on; Safari cu co the thieu, chua co fallback PNG tu dong o ban nay).

**Bug that da gap + da sua (`gas/js.html`)**: anh chen trong content dung `src` TUONG DOI
(dung cho site that, vd `images/posts/72/1/xxx-720.webp`) — nhung TinyMCE chay TRONG trang
GAS (origin khac han site that), nen src tuong doi khong resolve duoc, anh "bien mat ngay
tuc thi" khi vua upload xong (swap tu blob: tam sang src that bi vo). Sua theo dung
`gas-backend-patterns.md` muc 11: `boot()` tra them `github: {owner, repo, branch}` (khong
phai secret), client dung de hien ANH BANG URL TUYET DOI
(`raw.githubusercontent.com/.../html/...`) trong luc soan (ca khi mo bai cu de sua lan anh
vua chen moi), roi tu doi lai thanh tuong doi ngay truoc khi goi `savePost` (xem
`toAbsoluteImageSrcs_`/`toRelativeImageSrcs_`).

## Khac biet co chu dich so voi ban goc (cai tien, khong phai loi)

1. **`data/posts.json` tach thanh index nhe + `data/posts/<id>.json` chua content** — thay
   vi 1 file `posts.json` chua ca content nhu ban Flask (moi lan Luu phai ghi lai toan bo
   file, GAS payload lon dan theo so bai). Build script tu ghep lai khi build.
2. **Category ID bat bien, khong danh so lai khi xoa** — ban goc co bug: xoa 1 category o
   giua se renumber toan bo id con lai, lam bai viet cua cac category sau bi gan nham. Sua:
   id cap phat tang dan, khong tai su dung; `deleteCategory` chan xoa neu con bai viet dung
   category do (`Code.js`).
3. **Cloudflare (Workers + Static Assets) thay Vercel**, deploy qua `wrangler deploy` trong
   GitHub Actions (cau hinh `wrangler.toml` o repo root) — free, cho phep thuong mai,
   bandwidth khong gioi han (xem skill `hosting-and-quotas.md`, luu y skill mo ta "Cloudflare
   Pages" nhung Cloudflare da gop san pham nay vao chung Workers, khong con luong tao rieng
   "Pages" tren dashboard nua). `html/vercel.json` → `html/_redirects` (van dung dung quy
   uoc voi Workers Static Assets).
   **Bay quan trong**: Workers Static Assets mac dinh `html_handling = "auto-trailing-slash"`
   — TU DONG redirect `/bai-viet.html` → `/bai-viet` (bo duoi `.html`). Site nay da chay lau,
   Google da index URL co `.html` — doi se anh huong SEO thuc su. Da set
   `html_handling = "none"` trong `wrangler.toml` de tat han vi nay, giu nguyen URL that
   nhu file (giong Vercel/Flask ban goc). Kem `not_found_handling = "none"` (site nhieu
   trang, khong phai SPA — tra 404 that, khong am tham fallback ve `index.html`).
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
7. **"Liên hệ" ở footer quản lý được qua CMS, dạng free text** (`website.footer_contact_html`,
   textarea trong tab Cài đặt website) — ban đầu là `<ul>` hardcode y hệt trong ca 4
   template. Ghi RAW khong escape (giống `content` bai viet) vao trong `<ul>` co san, cho
   phep chen the HTML (`<a href="mailto:...">`...). `build.py` co
   `DEFAULT_FOOTER_CONTACT` khop dung noi dung cu de khong vo site neu field chua duoc set.
8. **Them trang 404 tuy chinh** (`templates/404.html` → `html/404.html`, build boi
   `build_404_page()`) — ban goc (Vercel) khong co trang 404 rieng. `wrangler.toml` set
   `not_found_handling = "404-page"` de Cloudflare Workers Static Assets serve dung file
   nay kem HTTP status 404 THAT cho moi URL khong khop (khac SPA fallback tra 200 - se
   khien Google index nham noi dung trang chu o URL sai).

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
- [x] Tao Cloudflare Worker ten `trithuc` (khop `name` trong `wrangler.toml`) — Cloudflare
      hien khong con luong tao "Pages" rieng, moi thu deu la Workers (co the co Static
      Assets). Tao `CLOUDFLARE_API_TOKEN` voi quyen **Account > Workers Scripts > Edit**
      (KHONG phai "Cloudflare Pages > Edit" — quyen do danh cho model Pages cu, se khong
      deploy duoc Worker) + lay `CLOUDFLARE_ACCOUNT_ID`, dien vao GitHub repo → Settings →
      Secrets and variables → Actions.
- [ ] Chay `python3 scripts/migrate_from_flask_cms.py` (tu thu muc goc du an, canh `html/`
      cu) de co du lieu that trong `remake/data/`, roi push repo nay len GitHub lan dau.
- [x] **Copy anh bai viet cu**: `../html/images/posts/**` → `remake/html/images/posts/**`
      — da copy (80MB, 1138 file), da rebuild va commit cung repo.
- [ ] Doi cac GitHub token bi lo (xem canh bao duoi) truoc khi push repo len GitHub that.
- [ ] **`images/thumb.webp` (OG mac dinh trang chu/category) chua ton tai** — file nay CHUA
      TUNG duoc tao ke ca o ban goc (khong phai loi phat sinh trong qua trinh remake). Upload
      qua tab Cai dat website (truong "Thumbnail site", crop cung 720x480) sau khi CMS chay
      that.
- [ ] **Bai "Lich su Kim Tu Thap" (id 72) hoan toan khong co anh** (3 thumbnail + 3 anh
      content) o bat ky dau — da kiem tra ca `trithucworld.com` (404 ca trang bai viet) nen
      day la bai nhap/draft chua tung publish that su, khong phai du lieu bi mat trong luc
      remake. Can: xoa bai nay di roi tao lai qua CMS moi (co anh), hoac tu upload anh bu
      vao qua CMS neu muon giu nguyen bai.

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

## UX: spinner loading + confirm truoc khi xoa

Moi nut trong `gas/app.html` goi mot thao tac bat dong bo (Luu/Xoa/Dang nhap/Mo bai de sua...)
deu di qua 2 helper trong `gas/js.html`:

- `gasCall(name, ...args)` — boc `google.script.run` thanh Promise.
- `withLoading(btn, promise)` — disable nut + hien vong xoay (`class="is-loading"`, xem
  `css.html`) NGAY LUC GOI (dong bo, truoc khi cho ket qua), tranh nguoi dung bam nhieu lan
  trong luc dang xu ly; tu phuc hoi nut khi xong (ca thanh cong lan loi).

Moi nut trong HTML truyen chinh no vao qua `this` (vd `onclick="savePostClick(this)"`); cac
nut sinh ra trong bang (danh sach bai/danh muc/trang/user) cung truyen `this` tuong tu trong
chuoi HTML dung `.map()`. **Xoa** (bai viet/danh muc/trang/user) da co san `confirm()` truoc
khi goi server, giu nguyen — chi them spinner cho phan goi server sau khi da confirm.

## Boot: stale-while-revalidate qua localStorage (da lam, gas-backend-patterns.md muc 9b)

Bug UX that da gap: moi lan tai lai trang Admin, man hinh Dang nhap hien ra ~1-3s (thoi gian
cho round-trip `boot()`) roi moi vao duoc Admin, du token van con hop le - gay cam giac
"nhap nhay". Sua: `bootApp()` trong `gas/js.html` cache nguyen ket qua `boot()` vao
`localStorage` (`LS_BOOT_CACHE_KEY`) — lan tai sau hien Admin **NGAY** tu cache (0 giay cam
nhan), roi goi lai `boot()` NGAM (`revalidateBootInBackground_()`) de xac thuc token +
lam moi du lieu; token het han thi moi dua ve man Dang nhap that. Lan dau chua co cache thi
hien `#boot-loading` (vong xoay trung tinh) thay vi nhap nhay man Dang nhap trong luc cho.
**Chua lam** (co the them neu can, xem `gas-backend-patterns.md` muc 9c/9d): cache tung
bai/trang rieng theo `updated_at`, prefetch ngam danh sach bai khi mo Admin.

**Bug that da gap + da sua**: cache ban dau CHI duoc ghi lai luc `boot()`/`revalidate` chay,
khong duoc dong bo ngay sau khi Luu/Xoa - nen "xoa bai xong, tai lai trang ngay sau do van
thay bai do" (doc tu cache cu trong khoanh khac truoc khi revalidate ngam kip chay xong).
Sua: them `syncBootCache_()` goi ngay sau MOI thao tac Luu/Xoa lam doi posts/pages/website
(`doSavePost`, `deletePostClick`, `savePageClick`, `deletePageClick`, `createCategoryClick`,
`deleteCategoryClick`, `saveWebsiteClick`) de cache luon khop du lieu that ngay lap tuc,
khong phai doi vong revalidate tiep theo. Dong thoi `revalidateBootInBackground_()` gio
cung tu ve lai 3 bang danh sach (bai/danh muc/trang) sau khi lay du lieu moi - truoc day chi
cap nhat bien ma khong ve lai gi ca, nen du lieu moi khong bao gio hien len man hinh dang mo.

## Modal thong bao + xac nhan (thay alert()/confirm() native)

Moi `alert(...)` trong `gas/js.html` da doi thanh `showAlert(message, type)` — **modal giua
man hinh** (khong phai toast goc man hinh - da thu toast truoc, user muon modal phai bam moi
dong), dung chung CSS `.confirm-overlay`/`.confirm-box` voi modal xac nhan Xoa. `type` mac
dinh `"error"` (chu do); `"success"` (chu xanh, in dam) cho thong bao thanh cong. Chi hien
**thong tin chinh** (khong con tien to kieu "Loi luu bai viet: ...").

Moi `confirm(...)` da doi thanh `showConfirm(message)` — modal 2 nut Hủy/Xóa, tra ve
`Promise<boolean>`; 4 ham Xoa (`deletePostClick`, `deleteCategoryClick`, `deletePageClick`,
`deleteUserClick`) da chuyen thanh `async function` de dung duoc `await showConfirm(...)`.

`showSyncAlert(message)` = `showAlert()` + tu dong noi them cau nhac "Bình tĩnh: cần 1 phút
để mọi thứ được cập nhật trên website!" — goi sau MOI thao tac Luu/Xoa lam website rebuild
(bai viet, danh muc, trang tinh, cai dat website) de nguoi dung khong hoang mang khi vao site
thay chua doi ngay. Khong dung cho quan ly nguoi dung (khong lam rebuild).

**Gotcha thuc te da gap luc debug voi user**: `typeof showToast` tra ve `"function"` va
`doSavePost.toString().includes("showSyncToast")` tra ve `true` deu KHONG chung minh code
*moi nhat* dang chay - chi chung minh 1 ham CU THE da ton tai tu 1 lan push nao do truoc day.
Voi 1 file duoc sua nhieu lan lien tiep trong 1 phien, luon kiem tra dung diem call site can
quan tam (vd goi thang ham trong Console de xem hanh vi thuc te), va nhac nguoi dung **hard
reload hoac dong han tab** sau moi lan Deploy > New version - F5 thuong khong du vi trang
GAS chay trong iframe co the giu cache HTML/JS cu.

## Redirect "/admin" sang GAS CMS + don file mo coi

`scripts/build.py` gio co `build_admin_redirect()` sinh `html/admin/index.html` (thu muc
rieng, KHONG phai file phang `admin.html` — doi lai theo yeu cau user de URL sach hon) —
trang trung gian tu dong chuyen huong (`meta refresh` + `location.replace()`, du phong ca 2)
sang URL `/exec` that su cua GAS CMS (hang sang trong `ADMIN_GAS_URL`, doi khi deploy lai tao
URL moi — xem `gas-backend-patterns.md` gotcha #4). `html/_redirects` co rewrite
`/admin -> /admin/index.html` va `/admin/ -> /admin/index.html` (200) de dung duoc URL ngan
`/admin` (khong duoi `.html`, khong can go `/admin/index.html`) — van BAT BUOC phai khai bao
rewrite nay du file nam trong thu muc con, vi `wrangler.toml` da tat `html_handling` nen
Cloudflare khong tu dong resolve thu muc → `index.html`.

**Chi 1 lop chan bot (CO CHU DICH, khac khuyen nghi 2 lop mac dinh cua
`static-site-build.md` muc 6)**: chi dua vao `<meta name="robots" content="noindex,
nofollow, noarchive, nosnippet">` tren chinh `admin/index.html` — **KHONG** them
`Disallow: /admin` vao `robots.txt` theo yeu cau ro rang cua user, vi `robots.txt` la file
**cong khai** ai cung doc duoc — khai bao `Disallow: /admin` vo tinh "quang cao" chinh xac
duong dan trang quan tri cho bat ky ai (ke ca bot xau khong tuan thu robots.txt) xem file do.

**Don file .html mo coi** (bug that da gap): xoa 1 bai/trang/danh muc qua CMS chi xoa
`data/`, KHONG tung xoa file `.html` da build san — nen bai da xoa van truy cap duoc tren
site that vo thoi han. `main()` trong `build.py` gio tinh lai tap hop URL hop le SAU MOI lan
build (posts + pages + categories + `index.html`/`404.html`), roi xoa moi file `.html` o goc
`html/` khong nam trong tap do — chi quet top-level (`HTML.glob("*.html")`, khong de quy) nen
khong dung cham/xoa nham `html/admin/index.html` nam trong thu muc con. Da kiem tra idempotent
(chay 2 lan lien tiep khong tu xoa/sinh them gi).

## Chua lam (co the them sau, tham khao `gas-backend-patterns.md` muc 9)

De giu pham vi ban dau gon, `gas/js.html` **chua** cai dat prefetch ngam danh sach bai/trang,
gioi han so lan nhap sai OTP da co nhung chua co UI quan ly rieng. Cac pattern nay deu da mo
ta chi tiet trong skill, them dan khi thuc te can (vd editor phan nan CMS cham).
