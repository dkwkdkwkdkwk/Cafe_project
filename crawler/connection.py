import time
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# ✅ 백업 파일 로드
def load_backup():
    try:
        with open("backup.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("page", 1), set(data.get("collected_cafes", [])), data.get("cafes", [])
    except FileNotFoundError:
        return 1, set(), []

# ✅ 백업 저장
def save_backup(page, collected_cafes, cafes):
    backup_data = {
        "page": page,
        "collected_cafes": list(collected_cafes),
        "cafes": cafes
    }
    with open("backup.json", "w", encoding="utf-8") as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)

# ✅ 드라이버 열기
def open_driver():
    driver_path = "C:/CapStone/VCC/chromedriver.exe"
    service = Service(driver_path)
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# ✅ iframe 대기 함수
def wait_for_iframe(driver, iframe_id="searchIframe"):
    driver.switch_to.default_content()
    WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it((By.ID, iframe_id)))

# ✅ 스크롤 함수
def scroll_down_all(driver):
    wait_for_iframe(driver)
    scroll_area = driver.find_element(By.CSS_SELECTOR, "div#_pcmap_list_scroll_container")
    last_height = driver.execute_script("return arguments[0].scrollHeight", scroll_area)
    scroll_try = 0
    while True:
        driver.execute_script("arguments[0].scrollBy(0, 3000);", scroll_area)
        time.sleep(1.5)
        new_height = driver.execute_script("return arguments[0].scrollHeight", scroll_area)
        if new_height == last_height:
            scroll_try += 1
            if scroll_try > 3:
                break
        else:
            scroll_try = 0
        last_height = new_height
    print("✅ 카페 리스트 스크롤 완료")

# ✅ 메뉴판 이미지 긁기
def crawl_menu_images(driver):
    image_urls = []
    try:
        menu_section = driver.find_elements(By.CSS_SELECTOR, "h2.place_section_header")
        for section in menu_section:
            title = section.find_element(By.CSS_SELECTOR, "div.place_section_header_title").text.strip()
            if "메뉴판 이미지로 보기" in title:
                parent = section.find_element(By.XPATH, "..")
                images = parent.find_elements(By.CSS_SELECTOR, "img.K0PDV")
                for img in images:
                    src = img.get_attribute("src")
                    image_urls.append(src)
                break
    except Exception as e:
        print(f"❗ 메뉴판 이미지 긁기 실패: {e}")
    return image_urls

# ✅ 카페 메뉴 긁기
def crawl_menus(driver, name, category, address):
    final_menus = []
    try:
        tabs = driver.find_elements(By.CSS_SELECTOR, "span.veBoZ")
        found_menu_tab = False
        for tab in tabs:
            if tab.text.strip() == "메뉴":
                driver.execute_script("arguments[0].click();", tab)
                print("✅ 메뉴탭 클릭 완료")
                time.sleep(2)
                found_menu_tab = True
                break

        if not found_menu_tab:
            print(f"❗ {name} : 메뉴탭 없음 → 카페 스킵")
            return []

        tab_buttons = driver.find_elements(By.CSS_SELECTOR, "div.category_box_inner button.tab")
        for tab in tab_buttons:
            try:
                tab_text = tab.find_element(By.CSS_SELECTOR, "span.tab_text").text.strip()
                print(f"➡ 탭 클릭: {tab_text}")
                driver.execute_script("arguments[0].click();", tab)
                time.sleep(1.5)

                groups = driver.find_elements(By.CSS_SELECTOR, "div.order_list_inner")
                for group in groups:
                    while True:
                        try:
                            more_button = group.find_element(By.CSS_SELECTOR, "button.GYkZu")
                            driver.execute_script("arguments[0].click();", more_button)
                            time.sleep(1.5)
                        except:
                            break

                    try:
                        group_title = group.find_element(By.CSS_SELECTOR, "div.order_list_tit span.title").text.strip()
                    except:
                        group_title = "기본메뉴"

                    items = group.find_elements(By.CSS_SELECTOR, "ul.order_list_area li.order_list_item")
                    if not items:
                        continue

                    for item in items:
                        try:
                            menu_name = item.find_element(By.CSS_SELECTOR, "div.tit").text.strip()
                        except:
                            menu_name = "메뉴없음"
                        try:
                            price = item.find_element(By.CSS_SELECTOR, "div.price strong").text.strip()
                            if "변동" in price or price == "":
                                price = "-"
                            else:
                                price += "원"
                        except:
                            price = "-"

                        if menu_name == "메뉴없음" or price == "-":
                            continue

                        final_menus.append({
                            "카페명": name,
                            "카테고리": category,
                            "주소": address,
                            "메뉴그룹": group_title,
                            "메뉴": menu_name,
                            "가격": price,
                            "menu_type": "메뉴"
                        })
            except Exception as e:
                print(f"❗ 탭 내부 클릭 실패: {e}")
                continue

        while True:
            try:
                more_button = driver.find_element(By.CSS_SELECTOR, "a.fvwqf")
                driver.execute_script("arguments[0].click();", more_button)
                print("✅ 그룹화 안된 메뉴 더보기 클릭")
                time.sleep(2)
            except NoSuchElementException:
                break
            except Exception as e:
                print(f"❗ 그룹화 안된 메뉴 더보기 클릭 실패: {e}")
                break

        plain_items = driver.find_elements(By.CSS_SELECTOR, "ul > li.E2jtL")
        for item in plain_items:
            try:
                menu_name = item.find_element(By.CSS_SELECTOR, "span.lPzHi").text.strip()
            except:
                menu_name = "메뉴없음"
            try:
                price = item.find_element(By.CSS_SELECTOR, "div.GXS1X").text.strip()
                if "변동" in price or price == "":
                    price = "-"
                else:
                    price += "원"
            except:
                price = "-"

            if menu_name == "메뉴없음" or price == "-":
                continue

            final_menus.append({
                "카페명": name,
                "카테고리": category,
                "주소": address,
                "메뉴그룹": "그룹없음",
                "메뉴": menu_name,
                "가격": price,
                "menu_type": "메뉴"
            })

        menu_images = crawl_menu_images(driver)
        for img_url in menu_images:
            final_menus.append({
                "카페명": name,
                "카테고리": category,
                "주소": address,
                "메뉴그룹": "메뉴판이미지",
                "메뉴": img_url,
                "가격": "-",
                "menu_type": "메뉴판이미지"
            })

    except Exception as e:
        print(f"❗ 메뉴 긁기 전체 실패: {e}")

    return final_menus

# (메인 실행 부분 계속 이어서)

while True:
    page, collected_cafes, cafes = load_backup()
    driver = open_driver()
    try:
        driver.get("https://map.naver.com/v5/search")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.input_search")))

        search_box = driver.find_element(By.CSS_SELECTOR, "input.input_search")
        search_box.click()
        search_box.clear()
        search_box.send_keys("영등포구 카페")
        search_box.send_keys(Keys.ENTER)
        time.sleep(1.5)
        search_box.send_keys(Keys.ENTER)
        time.sleep(3)

        while True:
            print(f"\n📄 영등포구 - 페이지 {page} 시작!")
            wait_for_iframe(driver)
            scroll_down_all(driver)

            items = driver.find_elements(By.CSS_SELECTOR, "li.UEzoS")
            print(f"👉 현재 페이지 카페 수: {len(items)}개")

            cafe_links = []
            for item in items:
                try:
                    name = item.find_element(By.CSS_SELECTOR, "span.TYaxT").text.strip()
                    category = item.find_element(By.CSS_SELECTOR, "span.KCMnt").text.strip()
                    link = item.find_element(By.CSS_SELECTOR, "a.tzwk0")
                    cafe_links.append((name, category, link))
                except:
                    continue

            for idx, (name, category, link) in enumerate(cafe_links):
                if name in collected_cafes:
                    print(f"❗ 이미 수집한 카페 {name} → 스킵")
                    continue
                collected_cafes.add(name)

                try:
                    wait_for_iframe(driver)
                    driver.execute_script("arguments[0].click();", link)
                    time.sleep(2)
                    wait_for_iframe(driver, "entryIframe")
                    time.sleep(2)

                    try:
                        address = driver.find_element(By.CSS_SELECTOR, "span.LDgIH").text.strip()
                    except:
                        address = "-"

                    menus = crawl_menus(driver, name, category, address)
                    if menus:
                        cafes.extend(menus)

                    driver.back()
                    time.sleep(2)

                except Exception as e:
                    print(f"❗ 카페 진입 실패: {e}")
                    driver.refresh()
                    time.sleep(5)
                    continue

            save_backup(page, collected_cafes, cafes)

            driver.switch_to.default_content()
            wait_for_iframe(driver)
            next_buttons = driver.find_elements(By.CSS_SELECTOR, "a.eUTV2[aria-disabled='false']")
            moved = False
            for btn in next_buttons:
                label = btn.find_element(By.CSS_SELECTOR, "span.place_blind").text.strip()
                if label == "다음페이지":
                    driver.execute_script("arguments[0].click();", btn)
                    moved = True
                    print("➡ 다음 페이지 이동 중...")
                    time.sleep(3)
                    break
            if not moved:
                print("\n❗ 더 이상 다음 페이지가 없습니다.")
                break
            page += 1

    except Exception as e:
        print(f"\n❗ 에러 발생: {e}")
        driver.quit()
        time.sleep(5)
        continue

    else:
        save_path = "영등포구_카페.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(cafes, f, ensure_ascii=False, indent=2)
        print(f"\n✅ (에러 발생 여부 관계없이) 저장 완료: {save_path}")

        if os.path.exists("backup.json"):
            os.remove("backup.json")
            print("✅ 백업파일 삭제 완료")

        driver.quit()
        break
