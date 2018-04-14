import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time, sys, os, os.path, tempfile

COURSE_ID = 'CCNA3-106'
CURRENT_CHAPTER = ''
QUICK_ANSWER = False
RETRY_LOGIN = False

def cisco(ACCOUNT, PASSWORD):
    # Enabled Flash
    prefs = {
        "profile.default_content_setting_values.plugins": 1,
        "profile.content_settings.plugin_whitelist.adobe-flash-player": 1,
        "profile.content_settings.exceptions.plugins.*,*.per_resource.adobe-flash-player": 1,
        "PluginsAllowedForUrls": "https://assessment.netacad.net"
    }
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", prefs)
    #chrome_options.add_argument("--headless")
    if getattr(sys, 'frozen', False):
        # executed as a bundled exe, the driver is in the extracted folder
        chromeDriver = "chromedriver.exe" if sys.platform.startswith('win') else "chromedriver"
        chromedriver_path = os.path.join(sys._MEIPASS, chromeDriver)
        driver = webdriver.Chrome(chromedriver_path, chrome_options=chrome_options)
    else:
        # executed as a simple script, the driver should be in `PATH`
        driver = webdriver.Chrome(chrome_options=chrome_options)
    find = driver.find_element_by_css_selector
    finds = driver.find_elements_by_css_selector

    def wait(waitCondition, success = None, error = None, timeout = 10):
        try:
            WebDriverWait(driver, timeout).until(waitCondition)
        except TimeoutException:
            print("Timeout")
            error() if error else driver.quit()
        else:
            if success: success()

    def login():
        driver.get("https://www.netacad.com/")
        waitCondition = EC.element_to_be_clickable((By.CSS_SELECTOR, "#headerLoginLink"))
        wait(waitCondition)
        find("#headerLoginLink").click()
        find("#_58_INSTANCE_fm_login").send_keys(ACCOUNT)
        find("#_58_INSTANCE_fm_password").send_keys(PASSWORD)
        find("#_58_INSTANCE_fm_password").submit()
        navigateToCourse()

    def retryLogin():
        global RETRY_LOGIN
        RETRY_LOGIN = True
        login()

    def navigateToCourse():
        print('--->\t選擇CCNA課程')
        waitCondition = EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".course-id.ng-binding"), COURSE_ID)
        wait(waitCondition, None, None if RETRY_LOGIN else retryLogin, 3)
        find(f".title.ng-binding[aria-label={COURSE_ID}]").click()
        navigateToAssignments()

    def navigateToAssignments():
        print('--->\t選擇作業')
        waitCondition = EC.element_to_be_clickable((By.CSS_SELECTOR, "a.assignments"))
        wait(waitCondition)
        find("a.assignments").click()
        chooseAssignment()

    def chooseAssignment():
        print('--->\t選擇第n章作業')
        waitCondition = EC.presence_of_element_located((By.CSS_SELECTOR, "#assignment_group_upcoming_assignments .assignment"))
        wait(waitCondition)
        assignments = finds("#assignment_group_upcoming_assignments li")

        for assignment in assignments:
            assignmentDate = assignment.find_element_by_css_selector('.status-description').text
            if assignmentDate.find('开始') != -1: continue
            assignmentScore = assignment.find_element_by_css_selector('.score-display').text.split('/')[0]
            assignmentScore = 0 if assignmentScore == '-' else float(assignmentScore)
            assignmentButton = assignment.find_element_by_css_selector("a")

            if assignmentScore < 97:
                assignmentButton.click()
                checkScore()
                break
            else:
                print('不符合')
        else:
            tk.messagebox.showwarning(message='無符合的作業！')

    def checkScore():
        print('--->\t檢查是否有分數')
        waitCondition = EC.presence_of_element_located((By.CSS_SELECTOR, "#tool_content"))
        wait(waitCondition)
        global CURRENT_CHAPTER
        CURRENT_CHAPTER = driver.title

        driver.switch_to_frame('tool_content')

        try:
            find(".information .score")
        except NoSuchElementException:
            # 快速參加考試
            global QUICK_ANSWER
            QUICK_ANSWER = True
            takeAssignment()
        else:
            checkFile()

    def takeAssignment():
        print('--->\t參加考試')
        find(".information div:not(.score) a").click()

        assignmentWindow = driver.window_handles[-1]
        driver.switch_to_window(assignmentWindow)
        navigateToAssignment()

    def navigateToAssignment():
        print('--->\t確認參加考試')
        waitCondition = EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']"))
        wait(waitCondition)
        find("input[type='submit']").click()
        checkPacketTracerAndFlash()

    def checkPacketTracerAndFlash():
        print('--->\t略過Packet Tracer')
        waitCondition = EC.presence_of_element_located((By.CSS_SELECTOR, "#controls"))
        wait(waitCondition)
        try:
            find("#skip").click()
        except NoSuchElementException:
            print("沒skip")
            find("#beginassessment").click()
            quickAnswer() if QUICK_ANSWER else normalAnswer()
        else:
            dealWithConfirmDialog()

    def dealWithConfirmDialog():
        print('--->\t確認略過Packet Tracer')
        waitCondition = EC.alert_is_present()
        wait(waitCondition)
        alert = driver.switch_to_alert()
        alert.accept()
        quickAnswer() if QUICK_ANSWER else normalAnswer()

    def quickAnswer():
        print('--->\t快速回答')
        waitCondition = EC.element_to_be_clickable((By.CSS_SELECTOR, "#submit"))
        wait(waitCondition)
        find("#submit").click()
        submitAnswer()

    def submitAnswer():
        print('--->\t送出答案')
        waitCondition = EC.element_to_be_clickable((By.CSS_SELECTOR, "#submitButton"))
        wait(waitCondition)
        global QUICK_ANSWER
        QUICK_ANSWER = False

        find("#submitButton").click()
        driver.close()
        driver.switch_to_window(driver.window_handles[0])
        navigateToAssignments()

    def checkFile():
        print('--->\t檢查是否已經有答案')
        try:
            with open(f"{CURRENT_CHAPTER}.html", mode='r', encoding='UTF-8'):
                pass
        except FileNotFoundError:
            find(".information .score").click()
            scoreWindow = driver.window_handles[-1]
            driver.switch_to_window(scoreWindow)
            navigateToFeedback()
        else:
            takeAssignment()

    def navigateToFeedback():
        print('--->\t沒有答案')
        find("#content .ui-widget.ui-widget-content:nth-child(3) li + li > a").click()
        writeOutFeedback()

    def writeOutFeedback():
        print('--->\t輸出答案')
        waitCondition = EC.presence_of_element_located((By.CSS_SELECTOR, "#items"))
        wait(waitCondition)
        with open(f"{CURRENT_CHAPTER}.html", 'w', encoding='UTF-8') as myFile:
            myFile.write(driver.page_source)
        driver.close()
        driver.switch_to_window(driver.window_handles[0])
        navigateToAssignments()

    def normalAnswer():
        print('--->\t正常回答')
        waitCondition = EC.visibility_of_element_located((By.CSS_SELECTOR, "#questions"))
        wait(waitCondition)
        #Load answers
        with open(f"{CURRENT_CHAPTER}.html", mode='r', encoding='UTF-8') as myFile:
            ANSWERS = myFile.read()
        ANSWERS = BeautifulSoup(ANSWERS, 'html.parser')
        #Loop all quiz
        while find("button#next").get_attribute("aria-disabled") == "false":
            find("button#next").click()
        else:
            #move to the first quiz
            find("#questionbartable td").click()
        # Fetch all questions id
        questionIds = []
        for question in finds(".question"):
            questionId = question.get_attribute("data-ident")
            questionIds.append(questionId)
        # Get Answer
        for questionId in questionIds:
            #print("@@@@@@@@@@@@@@@@@@@@@@@", questionId)
            answer = ANSWERS.select_one(f"div[id$='{questionId}']")
            answerSet = []
            try:
                #選擇題
                options = answer.select('td.option')
                if not options:
                    raise ValueError
            except ValueError:
                hasUA = answer.select_one('div').attrs['id'].startswith('UA', 0, 2)
                if hasUA:
                    #拖拉題
                    print('拖拉題')
                    continue
                else:
                    #填空題
                    blankFilling = answer.select_one('td b').text
                    blankFilling = blankFilling.replace('正确答案： ', '')
                    questionId = questionId.replace('i', 'ANSWERr')
                    find(f'input[name="{questionId}"]').send_keys(blankFilling)
            else:
                for option in options:
                    optionTr = option.previous_sibling
                    while optionTr == '\n':
                        optionTr = optionTr.previous_sibling
                    if optionTr.find("img"):
                        answerValue = option.input['value']
                        answerSet.append(answerValue)
                for answerValue in answerSet:
                    find(f'input[value="{answerValue}"]').click()
                #time.sleep(0.1)
            finally:
                find("button#next").click()
                time.sleep(0.3)
        else:
            print('End')

    login()

def resource_path(relative_path):
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def tkInit():
    window = tk.Tk()
    window.title('Cisco')
    window.geometry('300x280')

    #Frame
    mainFrame = tk.Frame(window)
    mainFrame.pack(pady=5)
    logoFrame = tk.Frame(mainFrame)
    logoFrame.pack(pady=10)
    formFrame = tk.Frame(mainFrame)
    formFrame.pack()
    inputFrame = tk.Frame(formFrame)
    inputFrame.pack()
    leftFormFrame = tk.Frame(inputFrame)
    leftFormFrame.pack(side='left')
    rightFormFrame = tk.Frame(inputFrame)
    rightFormFrame.pack(side='right')
    bottomformFrame = tk.Frame(formFrame)
    bottomformFrame.pack(side='bottom')
    footerFrame = tk.Frame(mainFrame)
    footerFrame.pack()

    #Logo
    canvas = tk.Canvas(logoFrame, height=79, width=150)
    imageDirection = "img"
    logo = tk.PhotoImage(file=resource_path(os.path.join(imageDirection, 'Cisco_Logo.png')))
    canvas.create_image(0, 0, anchor='nw', image=logo)
    canvas.pack(side='top')

    #Title
    tk.Label(logoFrame, text='Cisco Networking Academy', font=("Arial", 18)).pack()

    filepath = '/tmp' if sys.platform.startswith('darwin') else tempfile.gettempdir()
    filename = os.path.join(filepath, 'cisco_info.txt')

    def submit():
        ACCOUNT = accountInput.get()
        PASSWORD = passwordInput.get()
        if ACCOUNT and PASSWORD:
            with open(filename, 'w') as myFile:
                myFile.write(','.join((ACCOUNT, PASSWORD)))
            try:
                cisco(ACCOUNT, PASSWORD)
            except ConnectionResetError:
                tk.messagebox.showwarning(message='帳號或密碼有誤！')
        else:
            tk.messagebox.showwarning(message='請輸入帳號與密碼！')

    def autoCompleteAccountInfo():
        try:
            with open(filename) as myFile:
                account, password = myFile.read().strip().split(',')
                accountInput.insert(0, account)
                passwordInput.insert(0, password)
        except:
            print('沒有保存的帳號密碼')

    #Form
    tk.Label(leftFormFrame, text='帳號：').pack()
    tk.Label(leftFormFrame, text='密碼：').pack()
    accountInput = tk.Entry(rightFormFrame)
    accountInput.pack()
    passwordInput = tk.Entry(rightFormFrame, show='*')
    passwordInput.pack()
    autoCompleteAccountInfo()
    submitButton = tk.Button(bottomformFrame, text='確認', command=submit, width=26)
    submitButton.pack()

    window.mainloop()

if __name__ == '__main__':
    tkInit()
