from selenium import webdriver
from selenium.webdriver.common.by import By
import json
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from selenium.common.exceptions import NoSuchElementException

URL = "https://alueducation.instructure.com/courses/1785/gradebook/speed_grader?assignment_id=23813&student_id=5673"
BRAVE = '/usr/bin/brave-browser'

options = webdriver.ChromeOptions()
options.binary_location = BRAVE
options.add_argument("--user-data-dir=/home/waka/.config/BraveSoftware/Brave-BrowserProfile\ 2/")
options.add_argument("--profile-directory=Default")
driver = webdriver.Chrome(options=options)
driver.get(URL)

submissions = {}

seen_students = set()
stop_student_name = "Test Student"

while True:
    try:
        # Check for no submission
        has_no_submission = False
        try:
            no_submission_div = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "this_student_does_not_have_a_submission"))
            )
            if no_submission_div.is_displayed():
                has_no_submission = True
                print("⚠️ Student has no submission")
        except:
            pass

        # Get student name
        name_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#students_selectmenu-button .ui-selectmenu-item-header"))
        )
        student_name = name_element.text.strip()

        # Stop if we've seen this student before
        if student_name in seen_students:
            print(f"🛑 Detected cycle — already saw {student_name}. Exiting.")
            break
        seen_students.add(student_name)

        # Check if graded
        try:
            check_icon = driver.find_element(By.CSS_SELECTOR, "#students_selectmenu-button .icon-check")
            is_graded = check_icon.is_displayed()
        except:
            is_graded = False

        # Get link if available
        if not has_no_submission:
            WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.ID, "speedgrader_iframe"))
            )
            print("✅ Switched into iframe")
            # Check if this is a file upload submission
            try:
                file_upload_element = driver.find_element(By.CSS_SELECTOR, "div.file-upload-submission")
                if file_upload_element.is_displayed():
                    print("📁 Detected file upload submission")
                    driver.switch_to.default_content()
                    href = "File upload submission"
                    submissions[student_name] = {
                        "submission": href,
                        "graded": is_graded
                    }
                    print(f"📌 Saved: {student_name} → {href} | Graded: {is_graded}")
                    
                    # Click "Next" and continue to the next student
                    next_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "next-student-button"))
                    )
                    driver.execute_script("arguments[0].click();", next_button)
                    print("➡️ Moved to next student\n")
                    sleep(3)
                    continue
            except NoSuchElementException:
                # Not a file upload submission, continue with normal flow
                pass

            link_element = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "a.not_external"))
            )
            href = link_element.get_attribute("href")
            print("✅ Found GitHub link:", href)

            driver.switch_to.default_content()
        else:
            href = "No submission"

        # Save student data
        submissions[student_name] = {
            "submission": href,
            "graded": is_graded
        }
        print(f"📌 Saved: {student_name} → {href} | Graded: {is_graded}")

        # Stop if this is the sentinel student
        if student_name == stop_student_name:
            print("🛑 Reached Test Student — stopping loop.")
            break

        # Click "Next"
        next_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "next-student-button"))
        )
        driver.execute_script("arguments[0].click();", next_button)
        print("➡️ Moved to next student\n")
        sleep(3)

    except Exception as e:
        print("❌ Error occurred:", e)
        break

# Save to JSON
with open("github_submissions.json", "w", encoding="utf-8") as f:
    json.dump(submissions, f, indent=4, ensure_ascii=False)

print("\n📦 All submissions saved to github_submissions.json")
driver.quit()