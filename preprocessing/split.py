import pandas as pd
import json
import re
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# ✅ 환경변수 로딩
load_dotenv()
db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

# ✅ JSON 파일 불러오기
with open("개인카페.json", "r", encoding="utf-8") as f:
    personal_data = [json.loads(line) for line in f]

with open("프랜차이즈.json", "r", encoding="utf-8") as f:
    franchise_data = [json.loads(line) for line in f]

# ✅ DataFrame 변환
df_personal = pd.DataFrame(personal_data)
df_franchise = pd.DataFrame(franchise_data)

# ✅ 자치구 추출 함수
def extract_district(address):
    match = re.search(r"서울\s?([가-힣]+구)", address)
    return match.group(1) if match else None

df_personal["자치구"] = df_personal["주소"].apply(extract_district)
df_franchise["자치구"] = df_franchise["주소"].apply(extract_district)

# ✅ `-점`으로 끝나는 카페는 프랜차이즈로 이동
franchise_like = df_personal[df_personal["카페명"].str.endswith("점", na=False)]
df_personal_cleaned = df_personal[~df_personal["카페명"].str.endswith("점", na=False)]

# ✅ 중복 제거 (자치구 + 카페명)
df_personal_unique = df_personal_cleaned.drop_duplicates(subset=["자치구", "카페명"])
franchise_like_unique = franchise_like.drop_duplicates(subset=["자치구", "카페명"])
df_franchise_unique = df_franchise.drop_duplicates(subset=["자치구", "카페명"])

# ✅ 자치구별 카페 수 계산
personal_counts = df_personal_unique["자치구"].value_counts().rename("개인카페_수")
franchise_counts_base = df_franchise_unique["자치구"].value_counts()
franchise_counts_extra = franchise_like_unique["자치구"].value_counts()
franchise_counts = (franchise_counts_base + franchise_counts_extra).fillna(0).astype(int).rename("프랜차이즈카페_수")

# ✅ 병합 및 정리
merged = pd.concat([personal_counts, franchise_counts], axis=1).fillna(0).astype(int).reset_index()
merged = merged.rename(columns={"index": "자치구"})

# ✅ PostgreSQL에 저장
merged.to_sql("district_cafe_count", con=engine, if_exists="replace", index=False)

print("✅ district_cafe_count 테이블로 저장 완료")
