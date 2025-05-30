import pandas as pd
import json
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# ✅ 환경변수 로딩
load_dotenv()
db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

# ✅ JSONL 파일 읽기
jsonl_path = "menu_items.json"
with open(jsonl_path, "r", encoding="utf-8") as f:
    records = [json.loads(line.strip()) for line in f if line.strip()]

# ✅ DataFrame으로 변환
df = pd.DataFrame(records)

# ✅ popular_menu 테이블로 저장
df.to_sql("popular_menu", con=eine, if_exists="replace", index=False)

print("✅ popular_menu 테이블에 업로드 완료")
