# 🔑 API 키 및 설정 가이드

프로젝트를 실행하기 위해 필요한 모든 API 키와 설정을 정리했습니다.

## 필수 설정 항목 (3개)

### 1. Gemini API 키 (무료)

**용도**: PDF를 AI로 요약 생성 (setup.py에서만 사용)

**발급 방법**:
1. https://aistudio.google.com/app/apikey 접속
2. Google 계정 로그인
3. "Create API Key" 버튼 클릭
4. 기존 프로젝트 선택 또는 "Create API key in new project" 선택
5. API 키 복사 (예: `AIzaSyA...`)

**비용**: 무료 (월 15 RPM 제한, 이 프로젝트는 1회만 사용하므로 충분)

**설정 위치**:
```bash
# .env 파일
GEMINI_API_KEY=AIzaSyA_your_actual_key_here
```

---

### 2. Gmail 앱 비밀번호 (무료)

**용도**: 이메일 자동 발송 (daily_mailer.py에서 사용)

**전제조건**: Google 계정에 2단계 인증이 활성화되어 있어야 함

**발급 방법**:
1. https://myaccount.google.com/apppasswords 접속
2. Google 계정 로그인 (2단계 인증 요구됨)
3. "앱 선택" 드롭다운 → "기타(맞춤 이름)" 선택
4. 이름 입력 (예: "Daily Study Mailer")
5. "생성" 버튼 클릭
6. 16자리 비밀번호 복사 (예: `abcd efgh ijkl mnop`)
   - 띄어쓰기는 무시하고 입력 가능

**2단계 인증 활성화 방법** (아직 안 했다면):
1. https://myaccount.google.com/security 접속
2. "2단계 인증" 섹션 → "시작하기"
3. 휴대전화 번호로 인증 설정

**설정 위치**:
```bash
# .env 파일 (로컬 테스트용)
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=abcdefghijklmnop  # 띄어쓰기 제거

# GitHub Secrets (자동 발송용)
GMAIL_USER → your_email@gmail.com
GMAIL_APP_PASSWORD → abcdefghijklmnop
```

---

### 3. 수신자 이메일

**용도**: 학습 자료를 받을 이메일 주소

**설정 방법**:
- Gmail이 아니어도 됨 (네이버, 다음, 회사 메일 등 모두 가능)
- 본인 이메일 또는 다른 사람 이메일 입력
- **여러 명에게 발송 가능**: 쉼표(,)로 구분하여 입력

**설정 위치**:
```bash
# .env 파일 (로컬 테스트용)
# 한 명에게 발송
RECIPIENT_EMAIL=recipient@example.com

# 여러 명에게 발송
RECIPIENT_EMAIL=user1@gmail.com,user2@naver.com,user3@daum.net

# GitHub Secrets (자동 발송용)
RECIPIENT_EMAIL → user1@gmail.com,user2@naver.com,user3@daum.net
```

---

## 설정 파일 작성

### 로컬 실행용: .env 파일

```bash
# 1. 예시 파일 복사
cp .env.example .env

# 2. 파일 편집
nano .env  # 또는 vi, vim, code 등 원하는 에디터
```

**.env 파일 내용**:
```env
# Gemini API 키
GEMINI_API_KEY=AIzaSyA_your_actual_gemini_api_key_here

# Gmail 발신 계정
GMAIL_USER=your_email@gmail.com

# Gmail 앱 비밀번호 (16자리)
GMAIL_APP_PASSWORD=abcdefghijklmnop

# 수신자 이메일 (여러 명: 쉼표로 구분)
RECIPIENT_EMAIL=recipient@example.com
```

---

### GitHub Actions용: Secrets 설정

**설정 경로**:
1. GitHub Repository 페이지 접속
2. **Settings** 탭 클릭
3. 좌측 메뉴에서 **Secrets and variables** → **Actions** 클릭
4. **New repository secret** 버튼 클릭

**등록할 Secret 목록** (3개):

| Secret 이름 | 값 | 예시 |
|------------|-----|------|
| `GMAIL_USER` | Gmail 주소 | `myemail@gmail.com` |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 | `abcdefghijklmnop` |
| `RECIPIENT_EMAIL` | 수신자 이메일 | `student@naver.com` |

**주의사항**:
- `GEMINI_API_KEY`는 GitHub Secrets에 등록 **불필요** (setup.py는 로컬에서만 실행)
- Secret 값에 공백이나 따옴표 포함하지 말 것
- Secret 저장 후에는 값을 다시 볼 수 없으므로 정확히 입력

---

## 체크리스트

설정 전 확인:

- [ ] Gemini API 키 발급 완료
- [ ] Gmail 2단계 인증 활성화
- [ ] Gmail 앱 비밀번호 발급 완료
- [ ] 수신자 이메일 주소 확인
- [ ] `.env` 파일 생성 및 작성
- [ ] GitHub Secrets 3개 등록 (GitHub Actions 사용 시)

---

## 테스트 방법

### 1. Gemini API 테스트

```bash
python -c "
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print('❌ GEMINI_API_KEY가 없습니다')
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = model.generate_content('Hello')
    print('✅ Gemini API 연결 성공!')
    print(f'응답: {response.text[:50]}...')
"
```

### 2. Gmail SMTP 테스트

```bash
python -c "
import os
import smtplib
from dotenv import load_dotenv

load_dotenv()
user = os.getenv('GMAIL_USER')
password = os.getenv('GMAIL_APP_PASSWORD')

if not user or not password:
    print('❌ Gmail 설정이 없습니다')
else:
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(user, password)
        print('✅ Gmail SMTP 연결 성공!')
    except Exception as e:
        print(f'❌ 연결 실패: {e}')
"
```

### 3. 전체 시스템 테스트

```bash
# 이메일 발송 테스트 (실제 메일이 발송됩니다)
python daily_mailer.py
```

---

## 문제 해결

### Gemini API 오류

**증상**: `API key not valid` 또는 `403 Forbidden`

**해결**:
1. API 키 재확인: https://aistudio.google.com/app/apikey
2. `.env` 파일에서 `GEMINI_API_KEY=` 뒤에 공백 없는지 확인
3. API 키에 따옴표 없이 입력했는지 확인
4. 무료 할당량 초과 여부 확인

### Gmail SMTP 오류

**증상**: `Username and Password not accepted` 또는 `SMTPAuthenticationError`

**해결**:
1. 2단계 인증 활성화 확인: https://myaccount.google.com/security
2. 앱 비밀번호 재발급 (띄어쓰기 제거하고 입력)
3. Gmail 계정이 맞는지 확인
4. "보안 수준이 낮은 앱" 설정 필요 없음 (앱 비밀번호 사용 시)

### GitHub Actions 실패

**증상**: Workflow 실패, 이메일 미발송

**해결**:
1. Repository Settings → Secrets 확인
2. Secret 이름 대소문자 정확히 확인 (`GMAIL_USER` ≠ `gmail_user`)
3. Actions 로그에서 에러 메시지 확인
4. Secrets 재등록 시도

---

## 보안 권장사항

✅ **하세요**:
- `.env` 파일은 절대 GitHub에 업로드하지 않기 (`.gitignore`에 포함됨)
- 앱 비밀번호는 일반 비밀번호와 다름 (더 안전)
- 프로젝트 종료 후 앱 비밀번호 삭제 가능

❌ **하지 마세요**:
- Gmail 계정의 실제 비밀번호를 코드에 입력하지 않기
- API 키를 공개 저장소에 커밋하지 않기
- 앱 비밀번호를 다른 사람과 공유하지 않기

---

## 요약

| 항목 | 발급 링크 | 용도 | 비용 |
|-----|----------|-----|------|
| Gemini API 키 | https://aistudio.google.com/app/apikey | PDF 요약 생성 | 무료 |
| Gmail 앱 비밀번호 | https://myaccount.google.com/apppasswords | 이메일 발송 | 무료 |
| 수신자 이메일 | - | 메일 수신 | - |

**총 필요한 API/계정**: 2개 (Gemini, Gmail)
**총 비용**: 무료 (Gemini 사용료 약 400원만 발생)
