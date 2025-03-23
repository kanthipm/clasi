from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

service = Service(executable_path="chromedriver.exe")

#chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument('--headless')   
#driver = webdriver.Chrome(options=chrome_options);
driver = webdriver.Chrome(service = service);
    
driver.get("https://dukehub.duke.edu/psp/CSPRD01/EMPLOYEE/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_Main?")

#WebDriverWait(driver, 5).until(
#    EC.presence_of_element_located((By.CLASS_NAME, "MuiTypography-root MuiTypography-h2"))
#)

net_id = driver.find_element(By.ID, "expand-netid")
net_id.click()

pw_click = driver.find_element(By.ID, "use-password-instead")
pw_click.click()

#username = driver.find_element(By.ID, "j_username")
#username.clear() 
#username.send_keys("jh884")

#password = driver.find_element(By.ID, "j_password")
#password.clear()
#password.send_keys("jh884")

time.sleep(10)

driver.quit()