import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException


ROOMS = [
    ("polkit", "https://tryhackme.com/room/polkit"),
    ("rppsempire", "https://tryhackme.com/room/rppsempire"),
    ("bashscripting", "https://tryhackme.com/room/bashscripting"),
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


def _notify(status_callback, message):
    if status_callback:
        status_callback(message)
    else:
        print(f"[+] {message}")


def _keep_streak_room(driver, room_name, room_url, status_callback):
    """Run one reset and completion pass in a room."""
    streak_value = "not found"
    reset_done = False
    submit_done = False
    try:
        # Navigate to the target room
        time.sleep(random.uniform(3, 6))
        driver.get(room_url)
        
        with open("tryhackmebot.log", 'a') as f:
            print(f"[+] Navigated to {room_name} room")
            f.write(f"[+] Navigated to {room_name} room\n")
        
        # Try to find and click the profile dropdown
        try:
            dropdown = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'dropdown')]"))
            )
            dropdown.click()
            
            time.sleep(random.uniform(1, 2))
            
            # Find and click the reset progress option
            reset_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Reset Room Progress')]"))
            )
            reset_option.click()
            
            time.sleep(random.uniform(1, 3))
            
            # Confirm reset
            confirm_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Yes')]"))
            )
            confirm_button.click()
            reset_done = True
            
            with open("tryhackmebot.log", 'a') as f:
                print("[+] Room's Progress Reset")
                f.write("[+] Room's Progress Reset\n")
            _notify(status_callback, f"{room_name}: room progress reset.")
                
        except (NoSuchElementException, TimeoutException, ElementClickInterceptedException) as e:
            with open("tryhackmebot.log", 'a') as f:
                print(f"[!] Error resetting progress: {e}")
                f.write(f"[!] Error resetting progress: {e}\n")
                print("[!] Trying alternative XPaths...")
                f.write("[!] Trying alternative XPaths...\n")
            
            # Try alternative XPaths
            try:
                # Try to find any dropdown or menu button
                dropdown_alternatives = [
                    "//div[contains(@class, 'dropdown')]",
                    "//button[contains(@class, 'dropdown')]",
                    "//div[contains(@class, 'menu')]",
                    "//button[contains(@class, 'menu')]",
                    "//div[@id='user-menu']",
                    "//button[contains(@class, 'navbar-toggler')]"
                ]
                
                for xpath in dropdown_alternatives:
                    try:
                        menu = driver.find_element(By.XPATH, xpath)
                        menu.click()
                        time.sleep(1)
                        break
                    except:
                        continue
                
                # Look for reset option with various XPaths
                reset_alternatives = [
                    "//a[contains(text(), 'Reset')]",
                    "//a[contains(text(), 'reset')]",
                    "//button[contains(text(), 'Reset')]",
                    "//div[contains(text(), 'Reset')]",
                    "//span[contains(text(), 'Reset')]"
                ]
                
                for xpath in reset_alternatives:
                    try:
                        reset = driver.find_element(By.XPATH, xpath)
                        reset.click()
                        time.sleep(1)
                        break
                    except:
                        continue
                
                # Try to find confirm button with various XPaths
                confirm_alternatives = [
                    "//button[contains(text(), 'Yes')]",
                    "//button[contains(text(), 'Confirm')]",
                    "//button[contains(text(), 'OK')]",
                    "//button[contains(@class, 'confirm')]",
                    "//button[contains(@class, 'success')]"
                ]
                
                for xpath in confirm_alternatives:
                    try:
                        confirm = driver.find_element(By.XPATH, xpath)
                        confirm.click()
                        reset_done = True
                        _notify(status_callback, f"{room_name}: room progress reset using fallback controls.")
                        break
                    except:
                        continue
                        
            except Exception as e2:
                with open("tryhackmebot.log", 'a') as f:
                    print(f"[!] Alternative methods also failed: {e2}")
                    f.write(f"[!] Alternative methods also failed: {e2}\n")
        if not reset_done:
            _notify(status_callback, f"{room_name}: failed to confirm room progress reset.")

        # Scroll to the bottom and complete an action
        time.sleep(random.uniform(3, 6))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(random.uniform(2, 3))
        
        # Try to find and click a complete button
        try:
            complete_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Complete')]"))
            )
            complete_button.click()
            submit_done = True
            _notify(status_callback, f"{room_name}: completion submitted.")
        except (NoSuchElementException, TimeoutException) as e:
            with open("tryhackmebot.log", 'a') as f:
                print(f"[!] Could not find complete button: {e}")
                f.write(f"[!] Could not find complete button: {e}\n")
                print("[!] Trying alternative buttons...")
                f.write("[!] Trying alternative buttons...\n")
            
            # Try alternative buttons
            button_alternatives = [
                "//button[contains(@class, 'completed')]",
                "//button[contains(@class, 'complete')]",
                "//button[contains(@class, 'submit')]",
                "//button[contains(@class, 'answer')]",
                "//button[contains(text(), 'Submit')]",
                "//button[contains(text(), 'Answer')]",
                "//button[contains(text(), 'Next')]"
            ]
            
            for xpath in button_alternatives:
                try:
                    button = driver.find_element(By.XPATH, xpath)
                    button.click()
                    submit_done = True
                    _notify(status_callback, f"{room_name}: completion submitted using fallback controls.")
                    break
                except:
                    continue
        if not submit_done:
            _notify(status_callback, f"{room_name}: failed to submit a completion.")

        # Check the streak counter
        time.sleep(random.uniform(1, 3))
        driver.get(room_url)  # Refresh to see updated streak
        
        try:
            streak = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "user-streak"))
            ).get_attribute("data-streak")
            streak_value = streak
            
            with open("tryhackmebot.log", 'a') as f:
                print(f"[+] Success! Your Streak is {streak}")
                f.write(f"[+] Success! Your Streak is {streak}\n")
                
        except (NoSuchElementException, TimeoutException) as e:
            with open("tryhackmebot.log", 'a') as f:
                print(f"[!] Could not find streak counter: {e}")
                f.write(f"[!] Could not find streak counter: {e}\n")
                
            # Try to find streak counter with alternative XPaths
            streak_alternatives = [
                "//div[contains(@class, 'streak')]",
                "//span[contains(@class, 'streak')]",
                "//div[contains(text(), 'streak')]",
                "//span[contains(text(), 'streak')]"
            ]
            
            for xpath in streak_alternatives:
                try:
                    streak_element = driver.find_element(By.XPATH, xpath)
                    with open("tryhackmebot.log", 'a') as f:
                        print(f"[+] Found streak element: {streak_element.text}")
                        f.write(f"[+] Found streak element: {streak_element.text}\n")
                    streak_value = streak_element.text
                    break
                except:
                    continue
        return {
            "room": room_name,
            "url": room_url,
            "reset": reset_done,
            "submitted": submit_done,
            "streak": streak_value,
            "status": "success" if reset_done and submit_done else "failed",
        }
            
    except KeyboardInterrupt:
        with open("tryhackmebot.log", 'a') as f:
            print("[!] Process interrupted by user")
            f.write("[!] Process interrupted by user\n")
        raise
            
    except Exception as e:
        with open("tryhackmebot.log", 'a') as f:
            print(f"[!] Something Went Wrong: {e}")
            f.write(f"[!] Something Went Wrong: {e}\n")
        raise
