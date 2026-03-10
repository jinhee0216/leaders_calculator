## GitHub → Netlify 배포용 (Python 없이 사용)

요청하신 방식대로 **Python 실행 없이**, GitHub에 올려서 Netlify로 배포하는 방법입니다.

이 프로젝트에서 Netlify에 필요한 파일은 아래 2개만 있으면 됩니다.

- `public/index.html`
- `netlify.toml`

---

## 1) GitHub에 올릴 파일

최소 구성:

```text
/public/index.html
/netlify.toml
```

`app.py`, `transaction_summary.py`, `templates/`, `requirements.txt`, `tests/` 는
**Netlify 정적 배포에는 필요 없습니다.**

---

## 2) Netlify 배포 순서

1. GitHub에 위 파일 push
2. Netlify 접속 → **Add new site** → **Import from Git**
3. GitHub repo 선택
4. Build settings
   - Build command: 비워도 됨
   - Publish directory: `public`
5. Deploy

배포 완료 후 생성된 URL로 접속해 PDF 업로드/계산하면 됩니다.

---

## 3) 현재 정적 페이지 동작 규칙

- 포함: `지급 2024-08-21 9,890`, `지급 일자 ... 금액 ...`
- 제외: `선지급 ...`

---

## 4) 로컬 미리보기 (선택)

Python 서버 개발이 아니라, 정적 파일 미리보기용입니다.

```bash
python -m http.server 8080
```

브라우저: `http://localhost:8080/public/`


## 로고/배너 넣는 위치 (Netlify 정적 버전)

`public/assets` 폴더에 이미지 파일을 넣으면 됩니다.

- 로고: `public/assets/logo.png`
- 상단 배너: `public/assets/banner.jpg`

페이지에서 참조하는 위치는 `public/index.html` 기준으로 아래와 같습니다.

- 로고 src: `./assets/logo.png`
- 배너 src: `./assets/banner.jpg`

파일명이 다르면 `public/index.html`의 `img src` 경로도 같이 수정해주세요.
