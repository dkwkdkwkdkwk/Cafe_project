import pandas as pd
import json
import re
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# ✅ 환경변수 로드
load_dotenv()

# ✅ DB 연결
db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise ValueError("❌ DATABASE_URL 환경변수를 찾을 수 없습니다.")
engine = create_engine(db_url)

# ✅ JSON Lines 파일 읽기
def load_json_lines(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

# ✅ 가격 문자열 → 정수로 변환
def clean_price(x):
    if isinstance(x, str):
        digits = re.sub(r"[^\d]", "", x)
        return int(digits) if digits else None
    return None

# ✅ 메뉴 통합 매핑 테이블
MENU_MAPPING = {
    "바닐라 라떼": "바닐라라떼",
    "바닐라라뗴": "바닐라라떼",
    "카페 라떼": "카페라떼",
    "딸기 라떼": "딸기라떼",
    # 필요한 만큼 계속 추가
}

def unify_menu_name(menu):
    if not isinstance(menu, str):
        return None
    return MENU_MAPPING.get(menu.strip(), menu.strip())

# ✅ 전처리 함수
def preprocess_menu_data(data):
    df = pd.DataFrame(data)
    df = df[df["menu_type"] == "메뉴"]
    df["가격"] = df["가격"].apply(clean_price)
    df["자치구"] = df["주소"].str.extract(r"서울\s*(\S+구)")
    df["메뉴"] = df["메뉴"].apply(unify_menu_name)
    df = df.dropna(subset=["자치구", "메뉴", "가격"])
    return df

# ✅ 개인카페 처리
indep_data = load_json_lines("개인카페.json")
indep_df = preprocess_menu_data(indep_data)
indep_avg = indep_df.groupby(["자치구", "메뉴"])["가격"].mean().reset_index()
indep_avg = indep_avg.rename(columns={"가격": "개인카페_평균가격"})

# ✅ 프랜차이즈 처리
fran_data = load_json_lines("프랜차이즈.json")
fran_df = preprocess_menu_data(fran_data)
fran_avg = fran_df.groupby(["자치구", "메뉴"])["가격"].mean().reset_index()
fran_avg = fran_avg.rename(columns={"가격": "프랜차이즈_평균가격"})

# ✅ outer join: 자치구 + 메뉴 기준
merged = pd.merge(indep_avg, fran_avg, on=["자치구", "메뉴"], how="outer")
merged = merged.dropna(subset=["개인카페_평균가격", "프랜차이즈_평균가격"])

# ✅ 25개 자치구에서 모두 팔리는 메뉴만 필터링
menu_counts = merged.groupby("메뉴")["자치구"].nunique()
common_menus = menu_counts[menu_counts == 25].index
merged = merged[merged["메뉴"].isin(common_menus)]

# ✅ 저장
merged.to_sql("menu_price_stats", con=engine, if_exists="replace", index=False)

print("✅ menu_price_stats 테이블 저장 완료 (공통메뉴 + 환경변수 방식)")
