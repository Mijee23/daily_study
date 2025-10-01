# 📚 매일 학습 메일 시스템

Gemini 2.0 Flash를 사용한 초저가 자동 학습 메일 발송 시스템

## ✨ 특징

- 💰 **초저가**: 총 비용 약 400원 (₩)
- 🤖 **AI 요약**: Gemini 2.0 Flash로 고품질 요약
- 📧 **자동 발송**: 매일 오전 8시 자동 이메일
- 📱 **모바일 최적화**: 반응형 HTML 이메일
- 🔄 **진도 관리**: 자동 진도 추적
- 🎨 **예쁜 디자인**: 다크모드 지원

## 📊 시스템 구성

### Phase 1: 초기 설정 (로컬, 1회)
- **setup.py**: PDF → Gemini 2.0 Flash → 요약 생성
- **비용**: $0.10~0.30 (약 400원)

### Phase 2: 자동 발송 (GitHub Actions, 매일)
- **daily_mailer.py**: 저장된 요약 → 이메일 발송
- **비용**: $0 (완전 무료!)

## 🚀 빠른 시작

### 1단계: Repository 설정

```bash
# Repository 클론 (또는 Fork)
git clone https://github.com/yourusername/daily-study-mailer.git
cd daily-study-mailer

# 가상 환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2단계: API 키 발급

#### Gemini API 키 (무료)
1. https://aistudio.google.com/app/apikey 접속
2. "Create API Key" 클릭
3. API 키 복사

#### Gmail 앱 비밀번호
1. https://myaccount.google.com/apppasswords 접속
2. "앱 선택" → "기타" 입력 → "생성"
3. 16자리 비밀번호 복사

### 3단계: 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env  # 또는 원하는 에디터 사용
```

**.env 파일 내용:**
```env
GEMINI_API_KEY=your_actual_api_key_here
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_password
RECIPIENT_EMAIL=recipient@example.com
```

### 4단계: PDF 파일 배치

PDF 파일을 날짜 형식으로 준비:
- 형식: `YYYYMMDD_제목.pdf`
- 예시: `20250303_약동학기초.pdf`

```
data/
├── pharmacology/
│   ├── 20250303_약동학기초.pdf
│   ├── 20250305_자율신경계약물.pdf
│   ├── 20250307_중추신경계약물.pdf
│   └── ... (총 10개)
└── anatomy/
    ├── 20250304_골격계.pdf
    ├── 20250306_근육계.pdf
    ├── 20250308_순환계.pdf
    └── ... (총 10개)
```

### 5단계: 요약 생성 (로컬에서 1회 실행)

```bash
python setup.py
```

**실행 과정:**
1. PDF 파일 자동 스캔
2. 파일 목록 확인 요청
3. 비용 추정 표시
4. Gemini API로 요약 생성 (진행률 표시)
5. `data/summaries/` 폴더에 40개 md 파일 생성
6. `index.json`, `progress.json` 생성

**예상 소요 시간:** 5-10분

### 6단계: GitHub 업로드

```bash
# Git 초기화 (새 프로젝트인 경우)
git init
git add .
git commit -m "Initial commit: Add summaries"

# GitHub에 푸시
git remote add origin https://github.com/yourusername/daily-study-mailer.git
git branch -M main
git push -u origin main
```

**중요**: `.gitignore`가 원본 PDF 파일을 제외하므로, 요약 파일만 업로드됩니다.

### 7단계: GitHub Secrets 설정

1. GitHub Repository → **Settings** 탭
2. **Secrets and variables** → **Actions**
3. **New repository secret** 클릭
4. 다음 3개 Secret 추가:

| Name | Value |
|------|-------|
| `GMAIL_USER` | your_email@gmail.com |
| `GMAIL_APP_PASSWORD` | your_16_char_password |
| `RECIPIENT_EMAIL` | recipient@example.com |

### 8단계: GitHub Actions 활성화

1. **Actions** 탭 클릭
2. "Daily Study Mail" 워크플로우 확인
3. 필요시 "Enable workflow" 클릭

**자동 발송 시작!** 🎉
- 매일 오전 8시 (한국 시간) 자동 발송
- 진도는 자동으로 업데이트됩니다

## 🧪 테스트

### 로컬에서 이메일 발송 테스트

```bash
python daily_mailer.py
```

이메일이 정상적으로 발송되는지 확인하세요.

### GitHub Actions 수동 실행

1. **Actions** 탭
2. "Daily Study Mail" 워크플로우 선택
3. **Run workflow** → **Run workflow**

## 📊 진도 확인

### 현재 진도 확인
```bash
cat progress.json
```

**출력 예시:**
```json
{
  "current_day": 5,
  "last_sent_date": "2025-10-05",
  "total_days": 20,
  "completed": false,
  "sent_count": 4
}
```

### 인덱스 파일 확인
```bash
cat index.json
```

## 📁 프로젝트 구조

```
daily-study-mailer/
├── data/
│   ├── pharmacology/          # 원본 PDF (로컬에만)
│   ├── anatomy/               # 원본 PDF (로컬에만)
│   └── summaries/             # 생성된 요약 (GitHub에 업로드)
│       ├── day01_pharmacology.md
│       ├── day01_anatomy.md
│       └── ... (총 40개)
├── .github/
│   └── workflows/
│       └── daily.yml          # GitHub Actions 워크플로우
├── setup.py                   # 초기 요약 생성
├── daily_mailer.py            # 매일 발송
├── requirements.txt           # Python 의존성
├── progress.json              # 진도 추적
├── index.json                 # 파일 인덱스
├── .env.example               # 환경 변수 예시
├── .gitignore                 # Git 제외 파일
└── README.md                  # 이 파일
```

## 💰 비용 상세

### Phase 1: 초기 요약 생성 (1회)
- **모델**: Gemini 2.0 Flash
- **API 호출**: 40회 (약리학 20개 + 해부학 20개)
- **예상 비용**: $0.10~0.30 (약 130~400원)
- **실행 환경**: 로컬

### Phase 2: 매일 발송 (20일)
- **API 호출**: 0회 (저장된 요약 사용)
- **비용**: $0 (완전 무료)
- **실행 환경**: GitHub Actions (무료)

### 총 비용: 약 400원 ☕

## 🎨 이메일 미리보기

이메일은 다음과 같이 구성됩니다:

- **헤더**: 진행률 바 포함
- **약리학 섹션**: 파란색 배경
- **해부학 섹션**: 분홍색 배경
- **푸터**: 남은 일수 및 다음 학습 안내
- **반응형**: 모바일/데스크톱 최적화
- **다크모드**: 시스템 설정에 따라 자동 전환

## ❓ 문제 해결

### PDF 읽기 오류
```bash
pip install --upgrade PyPDF2
```

### Gemini API 오류
- API 키 확인: https://aistudio.google.com/app/apikey
- 무료 할당량 확인

### Gmail 발송 실패
1. 앱 비밀번호 재확인
2. 2단계 인증 활성화 확인
3. Gmail "보안 수준이 낮은 앱" 설정 확인

### GitHub Actions 실패
1. Secrets 확인
2. Actions 로그 확인
3. `progress.json` 권한 확인

### 중복 발송 방지
- 시스템이 자동으로 `last_sent_date` 확인
- 같은 날 재실행해도 중복 발송 안 됨

## 🔧 고급 설정

### 발송 시간 변경

`.github/workflows/daily.yml` 파일 수정:

```yaml
on:
  schedule:
    # 매일 오후 6시 (한국 시간 = 09:00 UTC)
    - cron: '0 9 * * *'
```

### 요약 분량 조정

`setup.py`의 프롬프트 수정:

```python
PHARMACOLOGY_PROMPT = """
...
**분량**: 약 2,000~2,500자 (7-10분 읽기)
...
"""
```

### 이메일 디자인 커스터마이징

`daily_mailer.py`의 `create_html_email()` 메서드에서 HTML/CSS 수정

## 📝 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

## 🤝 기여

Issues와 Pull Requests 환영합니다!

## 📞 지원

문제가 있으면 [Issue](https://github.com/yourusername/daily-study-mailer/issues)를 열어주세요.

---

**만든 이유**: 매일 아침 출근길에 가볍게 읽을 학습 자료가 필요했고,
AI 요약과 자동화를 결합하면 초저가로 가능하다는 것을 증명하고 싶었습니다.

**총 비용 400원으로 20일간 매일 고품질 학습 자료를 받으세요!** ☕📚
