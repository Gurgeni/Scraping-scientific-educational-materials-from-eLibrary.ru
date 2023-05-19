import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def filtracia(driver):
    driver.find_element(By.CSS_SELECTOR, 'div[id="txt_rubrics"]').click()
    rubrics = ['06', '10', '11', '15', '04', '11', '19', '39', '00', '36', '23', '12', '82', '05', '71', '72', '26', '80']
    for r in rubrics:
        selector = 'input[id="rubrics_' + str(r) + '"]'
        el = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        el.click()
        time.sleep(2)

    driver.find_element(By.CSS_SELECTOR, 'div[id="txt_years"]').click()
    i = 0
    while i < 9:
        selector = 'input[id="years_' + str(2012 + i) + '"]'
        el = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        el.click()
        i = i + 1
        time.sleep(0.5)

    driver.find_element(By.CSS_SELECTOR, 'div[id="txt_types"]').click()
    #types = ['types_RAR', 'types_PRC', 'types_CLA', 'types_CNF', 'types_DSR', 'types_EDU', 'types_BKC', 'types_REV',
             'types_MNG', 'types_MIS', 'types_COL', 'types_CMG']
    # for t in types:
    #    selector = 'input[id="' + t + '"]'
    #    el = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
    #    el.click()
    #    time.sleep(2)


def main():
    driver = webdriver.Chrome()
    driver.get("https://elibrary.ru/org_items.asp?orgsid=322")
    input("Press ENTER")

    filtracia(driver)
    input("Select VIBRAT and perform search")

    cache_pagescript = ''
    while True:
        try:
            lst = driver.find_elements(By.CSS_SELECTOR, 'tr[valign="middle"]')
            for l in lst:
                identifier = str(l.get_attribute('id'))
                if len(identifier) != 0:
                    print(identifier)
                    with open('links7.txt', 'a') as f:
                        f.write(identifier)
                        f.write('\n')
            script = str(driver.find_element(By.CSS_SELECTOR, 'a[title="Следующая страница"]').get_attribute('href')).replace(
                'javascript:', '')
            cache_pagescript = script
            print("Page:" + script)
            driver.execute_script(script)
            time.sleep(3)
        except:
            print("Error occurred")
            inp = input("Press ENTER to perform filtration or enter '1' to continue")
            if inp == '1':
                filtracia(driver)
                input("Select VIBRAT and perform search")
                driver.execute_script(cache_pagescript)
                input("Press ENTER")

if __name__ == "__main__":
    main()
