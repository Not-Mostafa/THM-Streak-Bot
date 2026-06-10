import os
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import random

ROOMS = [


    ("polkit", "https://tryhackme.com/room/polkit"),
    ("bashscripting", "https://tryhackme.com/room/bashscripting"),
    ("rppsempire", "https://tryhackme.com/room/rppsempire")


]

def keep_streak(driver, status_callback=None):
    """Reset and complete each configured room once."""
    results = []
    for index, (room_name, room_url) in enumerate(ROOMS, start=1):
        _notify(status_callback, f"Starting room {index}/{len(ROOMS)}: {room_name}.")
        result = _keep_streak_room(driver, room_name, room_url, status_callback)
        results.append(result)
        _notify(status_callback, f"Finished room {index}/{len(ROOMS)}: {room_name} with status {result['status']}.")
    return results



def _keep_streak_room(driver, room_name, room_url, status_callback):
    """Run one reset and completion pass in a room."""
    streak_value = "not found"
    reset_done = False
    submit_done = False

    # --- Setup screenshot directory and helper function ---
    os.makedirs("screenshots", exist_ok=True)

    def take_screenshot(step_name):
        safe_room_name = "".join([c for c in room_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        filename = f"screenshots/{safe_room_name}_{step_name}.png"
        driver.save_screenshot(filename)
        print(f"[📷] Screenshot saved: {filename}")
    # -----------------------------------------------------------

    try:  # <--- THIS IS THE TRY BLOCK THAT WAS MISSING ITS EXCEPT
        # Navigate to the target room
        time.sleep(random.uniform(3, 6))
        driver.get(room_url)
        
        with open("tryhackmebot.log", 'a') as f:
            print(f"[+] Navigated to {room_name} room")
            f.write(f"[+] Navigated to {room_name} room\n")
        
        take_screenshot("1_loaded_page")

        # Try to find and click the profile dropdown
        try:
            # FIXED: Added parentheses around the XPath
            dropdown = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "(//button[@aria-label='dropdown'])[3]"))
            )
            print("[+] Options found 1")
            dropdown.click()
            time.sleep(random.uniform(1, 2))
            print("[+] Options clicked 1")
            
            take_screenshot("2_dropdown_opened")

            # Find and click the reset progress option
            print("[*] Looking for reset option...")
            
            reset_option = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='menuitem'][.//p[text()='Reset Progress']]"))
            )
            print("[+] Options found 2")
            
            driver.execute_script("arguments[0].click();", reset_option)
            time.sleep(random.uniform(1, 3))
            print("[+] Options clicked 2")
            
            take_screenshot("3_reset_clicked")

            # Confirm reset
            confirm_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Yes, reset my progress']"))
            )
            print("[+] Options found 3")
            confirm_button.click()
            print("[+] Options clicked 3")
            
            reset_done = True
            time.sleep(random.uniform(1, 2)) # Brief pause to let modal close
            take_screenshot("4_reset_confirmed")
            
            with open("tryhackmebot.log", 'a') as f:
                print("[+] Room's Progress Reset")
                f.write("[+] Room's Progress Reset\n")
            print("[*] Refreshing page to clear cached progress...")
            driver.refresh()
        except (NoSuchElementException, TimeoutException, ElementClickInterceptedException) as e:
            take_screenshot("ERROR_resetting") 
            with open("tryhackmebot.log", 'a') as f:
                print(f"[!] Error resetting progress: {e}")
                f.write(f"[!] Error resetting progress: {e}\n")
            pass

        time.sleep(random.uniform(3, 6))
        # Scroll to the bottom and complete an action
        time.sleep(random.uniform(2, 4))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(random.uniform(2, 3))
        take_screenshot("5_scrolled_down")
        
        # Find and click the answer button
        try:
            complete_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'answer')]"))
            )
            complete_button.click()
            submit_done = True
            take_screenshot("6_completed_button_clicked")
            
            # (Optional) If you want the notification active:
            _notify(status_callback, f"{room_name}: completion submitted.")
            
        except (NoSuchElementException, TimeoutException, ElementClickInterceptedException) as e:
            take_screenshot("ERROR_completing")
            with open("tryhackmebot.log", 'a') as f:
                print(f"[!] Could not find the answer button: {e}")
                f.write(f"[!] Could not find the answer button: {e}\n")
        if not submit_done:
            _notify(status_callback, f"{room_name}: failed to submit a completion.")
            pass

        # Check the streak counter
        try:
            js_script = 'return document.querySelector(\'button[data-testid="streak-trigger"] p\').textContent;'
            streak_value = driver.execute_script(js_script)
            if streak_value:
                streak_value = streak_value.strip()
            take_screenshot("8_final_streak_checked")
            with open("tryhackmebot.log", 'a') as f:
                print(f"[+] Success! Your Streak is {streak_value}")
                f.write(f"[+] Success! Your Streak is {streak_value}\n") 
        except Exception as e:
            take_screenshot("ERROR_streak_not_found")
            with open("tryhackmebot.log", 'a') as f:
                print(f"[!] Could not find streak counter via JS: {e}")
                f.write(f"[!] Could not find streak counter via JS: {e}\n")

        return {
            "room": room_name,
            "url": room_url,
            "reset": reset_done,
            "submitted": submit_done,
            "streak": streak_value,
            "status": "success" if submit_done else "failed",
        }

    except Exception as e:
        take_screenshot("FATAL_ERROR_ROOM")
        with open("tryhackmebot.log", 'a') as f:
            print(f"[!] Critical error processing room {room_name}: {e}")
            f.write(f"[!] Critical error processing room {room_name}: {e}\n")
            
        return {
            "room": room_name,
            "url": room_url,
            "reset": False,
            "submitted": False,
            "streak": "error",
            "status": "failed",
        }

def _notify(status_callback, message):
    if status_callback:
        status_callback(message)
    else:
        print(f"[+] {message}")
