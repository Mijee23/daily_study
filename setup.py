#!/usr/bin/env python3
"""
setup.py - PDF를 Gemini 2.0 Flash로 요약하여 저장

사용 라이브러리:
- google-generativeai
- PyPDF2
- python-dotenv
- tqdm

실행 방법:
1. .env 파일에 GEMINI_API_KEY 설정
2. data/pharmacology/, data/anatomy/ 에 PDF 배치
3. python setup.py 실행
4. 완료되면 data/summaries/ 폴더에 40개 md 파일 생성
"""

import os
import json
import time
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

import google.generativeai as genai
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from tqdm import tqdm

# 환경 변수 로드
load_dotenv()

# Gemini API 설정
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되지 않았습니다.")

genai.configure(api_key=GEMINI_API_KEY)

# Gemini 모델 설정 (2.0 Flash)
MODEL_NAME = "gemini-2.0-flash-exp"

# 프롬프트 템플릿
PHARMACOLOGY_PROMPT = """
다음은 약리학 수업자료입니다.
학생이 매일 아침 읽을 학습 자료를 만들어주세요.

**분량**: 약 1,500~2,000자 (5-7분 읽기)

**수업자료를 전반적으로 요약**:

**필수 정리 내용**:
- 수업자료를 전반적으로 요약한 후, 필수적인 내용을 정리해주세요.

1. **💡 핵심 개념** (4-5개)
   - 각 개념을 2-3문장으로 상세히 설명
   - 약물의 작용 기전 포함
   - 왜 이렇게 작동하는지 논리적으로 설명

2. **🏥 임상 적용**
   - 실제 처방 예시 (적응증)
   - 주의사항 및 금기
   - 주요 부작용

3. **⚠️ 중요 암기 사항**
   - 시험에 나올 핵심 포인트
   - 약물명
   - 특이사항

4. **✅ 오늘의 퀴즈** (5문제)
   - 객관식 또는 OX 문제
   - 각 문제 아래에 답과 간단한 해설

**작성 가이드**:
- 마크다운 형식 사용
- 전문 용어는 처음 나올 때 쉽게 풀어서 설명
- 문단 구분 명확히
- 불릿 포인트 적절히 사용
- 학생 입장에서 이해하기 쉽게

**원본 자료**:
{pdf_content}
"""

ANATOMY_PROMPT = """
다음은 해부학 수업자료입니다.
학생이 매일 아침 읽을 학습 자료를 만들어주세요.

**분량**: 약 1,500~2,000자 (5-7분 읽기)

**필수 정리 내용**:
- 수업자료를 전반적으로 요약한 후, 필수적인 내용을 정리해주세요.

1. **📚 학습 키워드** (2-3개)
   - 어떤 구조를 배우고 무엇을 알아야 하는지

2. **🔍 구조와 위치** (상세)
   - 해부학적 위치 명확히

3. **⚙️ 기능** (생리학적 의미)
   - 각 구조의 역할
   - 움직임, 작용
   - 다른 구조와의 협력

4. **🏥 임상 의의**
   - 관련 질환
   - 손상 시 증상
   - 검사/진단 방법
   - 임상에서 중요한 이유

5. **✅ 오늘의 퀴즈** (5문제)
   - 위치, 기능, 임상 관련 문제
   - 각 문제 아래에 답과 해설

**작성 가이드**:
- 마크다운 형식 사용
- 3차원 구조는 텍스트로 최대한 상세히
- 용어는 영어로, anterior/posterior 등
- 도해 없이도 이해 가능하게
- 문단 구분 명확히

**원본 자료**:
{pdf_content}
"""


class PDFSummarizer:
    """PDF 요약 생성 클래스"""

    def __init__(self, model_name: str = MODEL_NAME):
        self.model = genai.GenerativeModel(model_name)
        self.pharmacology_dir = Path("data/pharmacology")
        self.anatomy_dir = Path("data/anatomy")
        self.summaries_dir = Path("data/summaries")
        self.summaries_dir.mkdir(parents=True, exist_ok=True)

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """PDF에서 텍스트 추출"""
        try:
            reader = PdfReader(str(pdf_path))
            text_parts = []

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            # 텍스트 정리
            full_text = "\n\n".join(text_parts)
            # 과도한 공백 제거
            full_text = re.sub(r'\n{3,}', '\n\n', full_text)
            full_text = re.sub(r' {2,}', ' ', full_text)

            return full_text.strip()

        except Exception as e:
            print(f"⚠️  PDF 읽기 오류 ({pdf_path.name}): {e}")
            return ""

    def extract_date_from_filename(self, filename: str) -> Tuple[str, str]:
        """파일명에서 날짜와 제목 추출 (YYYYMMDD_제목.pdf)"""
        match = re.match(r'(\d{8})_(.+)\.pdf', filename)
        if match:
            date_str = match.group(1)
            title = match.group(2)
            return date_str, title
        return "00000000", filename.replace('.pdf', '')

    def scan_pdf_files(self) -> List[Tuple[Path, Path]]:
        """PDF 파일 스캔 및 날짜순 정렬"""
        pharma_files = sorted(
            self.pharmacology_dir.glob("*.pdf"),
            key=lambda p: self.extract_date_from_filename(p.name)[0]
        )

        anatomy_files = sorted(
            self.anatomy_dir.glob("*.pdf"),
            key=lambda p: self.extract_date_from_filename(p.name)[0]
        )

        # 쌍으로 묶기
        max_len = max(len(pharma_files), len(anatomy_files))
        pairs = []

        for i in range(max_len):
            pharma = pharma_files[i] if i < len(pharma_files) else None
            anatomy = anatomy_files[i] if i < len(anatomy_files) else None
            if pharma or anatomy:
                pairs.append((pharma, anatomy))

        return pairs

    def generate_summary(self, pdf_content: str, prompt_template: str,
                        subject: str, retry_count: int = 3) -> str:
        """Gemini API로 요약 생성"""
        prompt = prompt_template.format(pdf_content=pdf_content[:15000])  # 토큰 제한

        for attempt in range(retry_count):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.7,
                        'top_p': 0.95,
                        'max_output_tokens': 2048,
                    }
                )

                if response.text:
                    return response.text.strip()

            except Exception as e:
                if attempt < retry_count - 1:
                    print(f"⚠️  API 호출 실패 (재시도 {attempt + 1}/{retry_count}): {e}")
                    time.sleep(2 ** attempt)  # 지수 백오프
                else:
                    print(f"❌ API 호출 최종 실패 ({subject}): {e}")
                    return f"# 요약 생성 실패\n\n오류: {e}"

        return "# 요약 생성 실패\n\n알 수 없는 오류"

    def save_summary(self, day: int, subject: str, content: str):
        """요약을 마크다운 파일로 저장"""
        filename = f"day{day:02d}_{subject}.md"
        filepath = self.summaries_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    def create_index(self, file_info: List[Dict]):
        """index.json 생성"""
        index_data = {
            "total_days": len(file_info),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "files": file_info
        }

        with open('index.json', 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

    def create_progress(self, total_days: int):
        """progress.json 초기화"""
        progress_data = {
            "current_day": 1,
            "last_sent_date": None,
            "total_days": total_days,
            "completed": False,
            "sent_count": 0
        }

        with open('progress.json', 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)

    def run(self):
        """전체 프로세스 실행"""
        print("=" * 60)
        print("📚 PDF 요약 생성 시작 (Gemini 2.0 Flash)")
        print("=" * 60)

        # PDF 파일 스캔
        print("\n🔍 PDF 파일 스캔 중...")
        pdf_pairs = self.scan_pdf_files()

        if not pdf_pairs:
            print("❌ PDF 파일을 찾을 수 없습니다.")
            print(f"   - {self.pharmacology_dir}/")
            print(f"   - {self.anatomy_dir}/")
            return

        print(f"✅ 총 {len(pdf_pairs)}일치 PDF 발견\n")

        # 파일 목록 출력
        print("📋 발견된 파일 목록:")
        print("-" * 60)
        for i, (pharma, anatomy) in enumerate(pdf_pairs, 1):
            pharma_name = pharma.name if pharma else "없음"
            anatomy_name = anatomy.name if anatomy else "없음"
            print(f"Day {i:2d}: 약리학={pharma_name}")
            print(f"        해부학={anatomy_name}")
        print("-" * 60)

        # 확인 요청
        response = input("\n계속 진행하시겠습니까? (y/n): ").lower()
        if response != 'y':
            print("❌ 취소되었습니다.")
            return

        # 비용 추정
        total_calls = sum([1 if p else 0 for p, _ in pdf_pairs] +
                         [1 if a else 0 for _, a in pdf_pairs])
        estimated_cost = total_calls * 0.015  # 약 $0.015/call
        print(f"\n💰 예상 비용: ${estimated_cost:.2f} (약 {estimated_cost * 1300:.0f}원)")
        print(f"   - 총 API 호출: {total_calls}회\n")

        # 요약 생성
        file_info = []
        success_count = 0
        fail_count = 0

        with tqdm(total=total_calls, desc="요약 생성 중", unit="파일") as pbar:
            for day, (pharma_pdf, anatomy_pdf) in enumerate(pdf_pairs, 1):
                day_info = {"day": day}

                # 약리학 처리
                if pharma_pdf:
                    _, title = self.extract_date_from_filename(pharma_pdf.name)
                    pdf_content = self.extract_text_from_pdf(pharma_pdf)

                    if pdf_content:
                        summary = self.generate_summary(
                            pdf_content,
                            PHARMACOLOGY_PROMPT,
                            f"Day{day} 약리학"
                        )
                        self.save_summary(day, "pharmacology", summary)

                        day_info["pharmacology"] = {
                            "original": pharma_pdf.name,
                            "summary": f"day{day:02d}_pharmacology.md",
                            "title": title
                        }
                        success_count += 1
                    else:
                        fail_count += 1

                    pbar.update(1)
                    time.sleep(0.5)  # Rate limit 방지

                # 해부학 처리
                if anatomy_pdf:
                    _, title = self.extract_date_from_filename(anatomy_pdf.name)
                    pdf_content = self.extract_text_from_pdf(anatomy_pdf)

                    if pdf_content:
                        summary = self.generate_summary(
                            pdf_content,
                            ANATOMY_PROMPT,
                            f"Day{day} 해부학"
                        )
                        self.save_summary(day, "anatomy", summary)

                        day_info["anatomy"] = {
                            "original": anatomy_pdf.name,
                            "summary": f"day{day:02d}_anatomy.md",
                            "title": title
                        }
                        success_count += 1
                    else:
                        fail_count += 1

                    pbar.update(1)
                    time.sleep(0.5)  # Rate limit 방지

                file_info.append(day_info)

        # 인덱스 및 진도 파일 생성
        print("\n📝 인덱스 파일 생성 중...")
        self.create_index(file_info)
        self.create_progress(len(pdf_pairs))

        # 완료 통계
        print("\n" + "=" * 60)
        print("✅ 요약 생성 완료!")
        print("=" * 60)
        print(f"📊 통계:")
        print(f"   - 성공: {success_count}개")
        print(f"   - 실패: {fail_count}개")
        print(f"   - 총 일수: {len(pdf_pairs)}일")
        print(f"\n📂 생성된 파일:")
        print(f"   - 요약 파일: data/summaries/ ({success_count}개)")
        print(f"   - 인덱스: index.json")
        print(f"   - 진도: progress.json")
        print("\n🚀 다음 단계:")
        print("   1. GitHub에 업로드")
        print("   2. GitHub Secrets 설정")
        print("   3. GitHub Actions 활성화")
        print("=" * 60)


if __name__ == "__main__":
    summarizer = PDFSummarizer()
    summarizer.run()
