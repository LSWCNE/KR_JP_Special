"""로컬 개발/데모용: 실제 구글 시트 없이 sample_data/mock_responses.csv를 그대로
동기화 파이프라인(app.services.sheet_sync)에 통과시켜 DB에 채워 넣는 스크립트.

구글 시트 CSV 링크가 아직 없거나, 오프라인으로 기능을 먼저 확인하고 싶을 때 사용합니다.
실제 연동 후에는 관리자 페이지에서 진짜 CSV URL을 등록하고 "지금 동기화"를 누르면 됩니다.

사용법: python -m app.dev_import_sample
"""
import os

from app.database import Base, engine, SessionLocal
from app.services import sheet_sync

SAMPLE_CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_data", "mock_responses.csv"
)


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        with open(SAMPLE_CSV_PATH, encoding="utf-8-sig") as f:
            csv_text = f.read()
        rows = sheet_sync.parse_csv_rows(csv_text)
        summary = sheet_sync.sync_rows(db, rows)
        print(f"샘플 데이터 임포트 완료: {summary}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
