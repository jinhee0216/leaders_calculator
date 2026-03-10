## PDF 거래내역 월별 합산기

이 저장소에는 두 가지 실행 방식이 있습니다.

1. **Flask 버전**: Python 서버 기반 (`app.py`)
2. **Netlify 정적 버전**: GitHub → Netlify 배포용 (`public/index.html`)

---

## A) Flask 버전 (기존 방식)

거래내역서 PDF 파일을 업로드하면 `지급 일자` 기준 월(`YYYY-MM`)별 `금액`(매출) 합계를 계산합니다.

### 실행 방법

```bash
pip install -r requirements.txt
python app.py
```

실행 후 `http://localhost:8000` 접속.

---

## B) GitHub → Netlify 정적 배포 방식

`public/index.html`은 **서버 없이 브라우저에서 직접 PDF를 읽어** 지급 항목을 집계하는 버전입니다.

- 포함: `지급 2024-08-21 9,890`, `지급 일자 ... 금액 ...`
- 제외: `선지급 ...`

### 배포 순서

1. GitHub에 이 저장소 push
2. Netlify에서 **Add new site → Import from Git**
3. 해당 GitHub repo 선택
4. Build settings
   - Build command: (비워도 됨)
   - Publish directory: `public`
5. Deploy

배포 완료 후 발급된 Netlify URL로 누구나 접속해 사용 가능합니다.

### 로컬에서 정적 버전 테스트

```bash
python -m http.server 8080
```

브라우저에서 `http://localhost:8080/public/` 접속.

---

## 참고

- Flask 버전은 OCR fallback(옵션) 설명이 포함되어 있습니다.
- 정적 Netlify 버전은 브라우저 환경에서 동작하므로 PDF 형식/텍스트 추출 상태에 따라 인식률이 달라질 수 있습니다.
