#!/usr/bin/env python3
"""
daily_mailer.py - 저장된 요약을 이메일로 발송

사용 라이브러리:
- python-dotenv
- markdown2
- smtplib (내장)
- email (내장)

실행 방법:
- GitHub Actions에서 매일 자동 실행
- 또는 로컬에서: python daily_mailer.py

기능:
- 진도 확인 및 중복 발송 방지
- 마크다운 → HTML 변환
- Gmail SMTP 발송
- 재시도 로직
- 에러 로깅
- 진도 자동 업데이트
"""

import os
import json
import smtplib
import time
from datetime import datetime, date
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional

import markdown2
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 설정
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')

# 경로
SUMMARIES_DIR = Path("data/summaries")
PROGRESS_FILE = Path("progress.json")
INDEX_FILE = Path("index.json")


class DailyMailer:
    """매일 학습 자료 이메일 발송 클래스"""

    def __init__(self):
        self.validate_config()
        self.progress = self.load_progress()
        self.index = self.load_index()

    def validate_config(self):
        """환경 변수 검증"""
        if not GMAIL_USER:
            raise ValueError("GMAIL_USER가 설정되지 않았습니다.")
        if not GMAIL_APP_PASSWORD:
            raise ValueError("GMAIL_APP_PASSWORD가 설정되지 않았습니다.")
        if not RECIPIENT_EMAIL:
            raise ValueError("RECIPIENT_EMAIL이 설정되지 않았습니다.")

    def load_progress(self) -> Dict:
        """진도 파일 로드"""
        if not PROGRESS_FILE.exists():
            # 초기화
            progress = {
                "current_day": 1,
                "last_sent_date": None,
                "total_days": 20,
                "completed": False,
                "sent_count": 0
            }
            self.save_progress(progress)
            return progress

        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_progress(self, progress: Dict):
        """진도 파일 저장"""
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

    def load_index(self) -> Dict:
        """인덱스 파일 로드"""
        if not INDEX_FILE.exists():
            raise FileNotFoundError("index.json 파일이 없습니다. setup.py를 먼저 실행하세요.")

        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def should_send_today(self) -> bool:
        """오늘 발송해야 하는지 확인"""
        today = date.today().isoformat()

        # 이미 완료된 경우
        if self.progress.get('completed', False):
            print("✅ 모든 학습이 완료되었습니다!")
            return False

        # 오늘 이미 발송한 경우
        if self.progress.get('last_sent_date') == today:
            print(f"ℹ️  오늘 이미 발송했습니다 (Day {self.progress['current_day'] - 1})")
            return False

        # 진도가 총 일수를 초과한 경우
        if self.progress['current_day'] > self.progress['total_days']:
            print("✅ 모든 학습이 완료되었습니다!")
            self.progress['completed'] = True
            self.save_progress(self.progress)
            return False

        return True

    def load_summary(self, day: int, subject: str) -> Optional[str]:
        """요약 파일 로드"""
        filename = f"day{day:02d}_{subject}.md"
        filepath = SUMMARIES_DIR / filename

        if not filepath.exists():
            print(f"⚠️  파일을 찾을 수 없습니다: {filename}")
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def markdown_to_html(self, markdown_text: str) -> str:
        """마크다운을 HTML로 변환"""
        return markdown2.markdown(
            markdown_text,
            extras=['fenced-code-blocks', 'tables', 'break-on-newline']
        )

    def get_day_info(self, day: int) -> Dict:
        """특정 날짜 정보 가져오기"""
        for file_info in self.index['files']:
            if file_info['day'] == day:
                return file_info
        return {}

    def extract_quiz_from_content(self, content: str) -> str:
        """마크다운 내용에서 퀴즈 섹션 추출"""
        # "복습 퀴즈" 또는 "오늘의 퀴즈" 섹션 찾기
        import re
        patterns = [
            r'#+\s*✅\s*복습 퀴즈.*?(?=\n#+\s|\Z)',
            r'#+\s*✅\s*오늘의 퀴즈.*?(?=\n#+\s|\Z)',
            r'#+\s*복습 퀴즈.*?(?=\n#+\s|\Z)',
            r'#+\s*오늘의 퀴즈.*?(?=\n#+\s|\Z)'
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
            if match:
                return match.group(0).strip()

        return ""

    def create_html_email(self, day: int, pharma_content: str, anatomy_content: str) -> str:
        """HTML 이메일 생성"""
        # 진행률 계산
        progress = (day / self.progress['total_days']) * 100
        remaining = self.progress['total_days'] - day
        next_day = day + 1 if day < self.progress['total_days'] else day

        # 제목 가져오기
        day_info = self.get_day_info(day)
        pharma_title = day_info.get('pharmacology', {}).get('title', '약리학')
        anatomy_title = day_info.get('anatomy', {}).get('title', '해부학')

        # 마크다운 → HTML
        pharma_html = self.markdown_to_html(pharma_content)
        anatomy_html = self.markdown_to_html(anatomy_content)

        # 전날 복습 퀴즈 생성
        review_section = ""
        if day > 1:
            prev_pharma = self.load_summary(day - 1, 'pharmacology')
            prev_anatomy = self.load_summary(day - 1, 'anatomy')

            if prev_pharma and prev_anatomy:
                prev_pharma_quiz = self.extract_quiz_from_content(prev_pharma)
                prev_anatomy_quiz = self.extract_quiz_from_content(prev_anatomy)

                prev_day_info = self.get_day_info(day - 1)
                prev_pharma_title = prev_day_info.get('pharmacology', {}).get('title', '약리학')
                prev_anatomy_title = prev_day_info.get('anatomy', {}).get('title', '해부학')

                review_html = f"""
                <div class="section review">
                  <div class="section-header">
                    <span class="section-icon">🔁</span>
                    <h2 class="section-title">어제의 복습 (Day {day-1})</h2>
                  </div>
                  <div class="content">
                    <h3>💊 약리학 복습: {prev_pharma_title}</h3>
                    {self.markdown_to_html(prev_pharma_quiz) if prev_pharma_quiz else '<p>퀴즈를 찾을 수 없습니다.</p>'}

                    <h3>🫀 해부학 복습: {prev_anatomy_title}</h3>
                    {self.markdown_to_html(prev_anatomy_quiz) if prev_anatomy_quiz else '<p>퀴즈를 찾을 수 없습니다.</p>'}
                  </div>
                </div>
                """
                review_section = review_html

        # 오늘 날짜
        today = date.today().strftime('%Y년 %m월 %d일')

        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Day {day} 학습 자료</title>
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Malgun Gothic',
                   'Apple SD Gothic Neo', sans-serif;
      line-height: 1.6;
      color: #333;
      background-color: #f5f5f5;
      padding: 20px;
    }}

    .container {{
      max-width: 600px;
      margin: 0 auto;
      background-color: white;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      overflow: hidden;
    }}

    .header {{
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px 20px;
      text-align: center;
    }}

    .header h1 {{
      font-size: 24px;
      margin-bottom: 8px;
    }}

    .progress-bar {{
      background-color: rgba(255,255,255,0.3);
      height: 8px;
      border-radius: 4px;
      margin-top: 15px;
      overflow: hidden;
    }}

    .progress-fill {{
      background-color: white;
      height: 100%;
      width: {progress}%;
      transition: width 0.3s ease;
    }}

    .section {{
      padding: 30px 20px;
      border-bottom: 1px solid #eee;
    }}

    .section:last-of-type {{
      border-bottom: none;
    }}

    .section-header {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 20px;
    }}

    .section-icon {{
      font-size: 28px;
    }}

    .section-title {{
      font-size: 20px;
      font-weight: bold;
      color: #667eea;
    }}

    .pharmacology {{
      background-color: #f0f4ff;
    }}

    .anatomy {{
      background-color: #fff0f6;
    }}

    .review {{
      background-color: #fffbea;
    }}

    .content h1 {{
      font-size: 22px;
      color: #333;
      margin: 20px 0 12px 0;
    }}

    .content h2 {{
      font-size: 18px;
      color: #333;
      margin: 20px 0 10px 0;
    }}

    .content h3 {{
      font-size: 16px;
      color: #555;
      margin: 15px 0 8px 0;
    }}

    .content p {{
      margin-bottom: 12px;
      color: #666;
    }}

    .content ul, .content ol {{
      margin-left: 20px;
      margin-bottom: 12px;
    }}

    .content li {{
      margin-bottom: 6px;
      color: #666;
    }}

    .content strong {{
      color: #333;
    }}

    .content code {{
      background-color: #f4f4f4;
      padding: 2px 6px;
      border-radius: 3px;
      font-family: 'Courier New', monospace;
      font-size: 0.9em;
    }}

    .content blockquote {{
      background-color: #fffbea;
      border-left: 4px solid #f59e0b;
      padding: 15px;
      margin: 15px 0;
      border-radius: 4px;
    }}

    .content table {{
      border-collapse: collapse;
      width: 100%;
      margin: 15px 0;
    }}

    .content th, .content td {{
      border: 1px solid #ddd;
      padding: 8px;
      text-align: left;
    }}

    .content th {{
      background-color: #f0f4ff;
      font-weight: bold;
    }}

    .footer {{
      background-color: #f9fafb;
      padding: 20px;
      text-align: center;
      color: #999;
      font-size: 14px;
    }}

    .footer a {{
      color: #667eea;
      text-decoration: none;
    }}

    .footer p {{
      margin: 5px 0;
    }}

    @media (max-width: 600px) {{
      body {{
        padding: 10px;
      }}

      .header {{
        padding: 20px 15px;
      }}

      .section {{
        padding: 20px 15px;
      }}

      .section-title {{
        font-size: 18px;
      }}
    }}

    @media (prefers-color-scheme: dark) {{
      body {{
        background-color: #1a1a1a;
      }}

      .container {{
        background-color: #2d2d2d;
      }}

      .content h1, .content h2, .content h3, .content strong {{
        color: #e0e0e0;
      }}

      .content p, .content li {{
        color: #b0b0b0;
      }}

      .footer {{
        background-color: #1a1a1a;
        color: #666;
      }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <!-- 헤더 -->
    <div class="header">
      <h1>📚 Day {day}/{self.progress['total_days']} - 오늘의 학습</h1>
      <p>{today}</p>
      <div class="progress-bar">
        <div class="progress-fill"></div>
      </div>
    </div>

    <!-- 전날 복습 퀴즈 (Day 2부터) -->
    {review_section}

    <!-- 약리학 섹션 -->
    <div class="section pharmacology">
      <div class="section-header">
        <span class="section-icon">💊</span>
        <h2 class="section-title">오늘의 약리학: {pharma_title}</h2>
      </div>
      <div class="content">
        {pharma_html}
      </div>
    </div>

    <!-- 해부학 섹션 -->
    <div class="section anatomy">
      <div class="section-header">
        <span class="section-icon">🫀</span>
        <h2 class="section-title">오늘의 해부학: {anatomy_title}</h2>
      </div>
      <div class="content">
        {anatomy_html}
      </div>
    </div>

    <!-- 푸터 -->
    <div class="footer">
      <p>💪 잘하고 있어요! {remaining}일 남았습니다.</p>
      <p>📅 다음 학습: Day {next_day}</p>
      <p style="margin-top: 10px; font-size: 12px;">
        자동 발송 시스템 | 매일 아침 새로운 지식을 전달합니다
      </p>
    </div>
  </div>
</body>
</html>"""

        return html

    def send_email(self, day: int, html_content: str, retry_count: int = 3) -> bool:
        """이메일 발송 (재시도 로직 포함)"""
        subject = f"📚 Day {day}/{self.progress['total_days']} - 오늘의 학습 자료"

        # 여러 수신자 처리 (쉼표로 구분)
        recipients = [email.strip() for email in RECIPIENT_EMAIL.split(',')]

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = GMAIL_USER
        msg['To'] = ', '.join(recipients)

        # HTML 파트 추가
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        for attempt in range(retry_count):
            try:
                # Gmail SMTP 연결
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                    server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
                    server.sendmail(GMAIL_USER, recipients, msg.as_string())

                print(f"✅ 이메일 발송 성공 (Day {day})")
                print(f"   수신자: {', '.join(recipients)}")
                return True

            except Exception as e:
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    print(f"⚠️  발송 실패 (재시도 {attempt + 1}/{retry_count}): {e}")
                    print(f"   {wait_time}초 후 재시도...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ 이메일 발송 최종 실패: {e}")
                    return False

        return False

    def update_progress(self):
        """진도 업데이트"""
        today = date.today().isoformat()
        self.progress['current_day'] += 1
        self.progress['last_sent_date'] = today
        self.progress['sent_count'] += 1

        # 완료 체크
        if self.progress['current_day'] > self.progress['total_days']:
            self.progress['completed'] = True

        self.save_progress(self.progress)

    def run(self):
        """메일 발송 프로세스 실행"""
        print("=" * 60)
        print("📧 매일 학습 메일 발송 시스템")
        print("=" * 60)

        # 발송 여부 확인
        if not self.should_send_today():
            return

        current_day = self.progress['current_day']
        print(f"\n📅 오늘 발송: Day {current_day}/{self.progress['total_days']}")

        # 요약 파일 로드
        print("\n📖 요약 파일 로드 중...")
        pharma_content = self.load_summary(current_day, 'pharmacology')
        anatomy_content = self.load_summary(current_day, 'anatomy')

        if not pharma_content or not anatomy_content:
            print("❌ 요약 파일을 찾을 수 없습니다.")
            return

        # HTML 이메일 생성
        print("🎨 HTML 이메일 생성 중...")
        html_content = self.create_html_email(current_day, pharma_content, anatomy_content)

        # 이메일 발송
        print("📤 이메일 발송 중...")
        success = self.send_email(current_day, html_content)

        if success:
            # 진도 업데이트
            self.update_progress()
            print(f"\n✅ 완료! 다음 발송: Day {self.progress['current_day']}")
        else:
            print("\n❌ 발송 실패. 나중에 다시 시도하세요.")

        print("=" * 60)


if __name__ == "__main__":
    try:
        mailer = DailyMailer()
        mailer.run()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
