import json
import re
from collections import defaultdict

# ✅ JSON 파일 로딩
with open("merged_cafes.json", "r", encoding="utf-8") as f:
    cafes = json.load(f)

# ✅ 자치구별 카페 저장용 딕셔너리
district_cafes = defaultdict(list)

# ✅ 자치구 추출 및 그룹핑
for cafe in cafes:
    address = cafe.get("주소", "")
    match = re.search(r"서울\s([가-힣]+구)", address)
    if match:
        district = match.group(1)
        cafe["자치구"] = district
        district_cafes[district].append(cafe)

# ✅ 자치구별로 총_리뷰가 많은 상위 2개 카페 추출
top_cafes_by_district = {}

for district, cafe_list in district_cafes.items():
    sorted_list = sorted(cafe_list, key=lambda x: x.get("총_리뷰", 0), reverse=True)
    top_cafes_by_district[district] = sorted_list[:15]

# ✅ 결과 출력
for district, top_cafes in top_cafes_by_district.items():
    print(f"📍 {district} 상위 2개 카페:")
    for cafe in top_cafes:
        print(f"  - {cafe['카페명']} ({cafe['총_리뷰']} 리뷰)")
    print()
