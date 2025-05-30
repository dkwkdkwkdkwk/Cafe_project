import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# ✅ 환경변수 로딩
load_dotenv()

# ✅ CSV 불러오기
df = pd.read_csv("서울시매출데이터.csv", encoding="cp949")

# ✅ 자치구별 카페 수
cafe_counts = {
    "종로구": 288, "중구": 282, "용산구": 270, "성동구": 275, "광진구": 272,
    "동대문구": 213, "중랑구": 207, "성북구": 270, "강북구": 258, "도봉구": 261,
    "노원구": 223, "은평구": 202, "서대문구": 256, "마포구": 260, "양천구": 257,
    "강서구": 261, "구로구": 211, "금천구": 214, "영등포구": 268, "동작구": 257,
    "관악구": 266, "서초구": 269, "강남구": 249, "송파구": 276, "강동구": 260
}

summary_rows = []

for gu in df["자치구"].unique():
    df_gu = df[df["자치구"] == gu]
    연간_매출_합 = df_gu["당월_매출_금액"].sum()
    카페수 = cafe_counts.get(gu, 1)  # fallback

    def scaled(col):
        return round(df_gu[col].sum() / 12 / 카페수)

    row = {
        "자치구": gu,
        "남성": scaled("남성_매출_금액"),
        "여성": scaled("여성_매출_금액"),
        "연령_10": scaled("연령대_10_매출_금액"),
        "연령_20": scaled("연령대_20_매출_금액"),
        "연령_30": scaled("연령대_30_매출_금액"),
        "연령_40": scaled("연령대_40_매출_금액"),
        "연령_50": scaled("연령대_50_매출_금액"),
        "연령_60": scaled("연령대_60_이상_매출_금액"),
        "월": scaled("월요일_매출_금액"),
        "화": scaled("화요일_매출_금액"),
        "수": scaled("수요일_매출_금액"),
        "목": scaled("목요일_매출_금액"),
        "금": scaled("금요일_매출_금액"),
        "토": scaled("토요일_매출_금액"),
        "일": scaled("일요일_매출_금액"),
        "00_06": scaled("시간대_00~06_매출_금액"),
        "06_11": scaled("시간대_06~11_매출_금액"),
        "11_14": scaled("시간대_11~14_매출_금액"),
        "14_17": scaled("시간대_14~17_매출_금액"),
        "17_21": scaled("시간대_17~21_매출_금액"),
        "21_24": scaled("시간대_21~24_매출_금액"),
        "카페당_월_평균_매출": round(연간_매출_합 / 12 / 카페수)
    }

    summary_rows.append(row)

summary_df = pd.DataFrame(summary_rows)

# ✅ DB 연결
db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

# ✅ 카페당 월 기준 요약 테이블만 저장
summary_df.to_sql("seoul_sales_summary", con=engine, if_exists="replace", index=False)

print("✅ 카페당 월 평균 매출 포함 데이터 저장 완료")