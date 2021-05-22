# -*- coding: UTF-8 -*-
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
import pandas as pd
import re
import asyncio
from aiohttp import ClientSession

# times to scroll web page
SCROLL_COUNT = 3

# succeesful or failed projects
SUCCESSFUL_OR_FAILED = True

# IS_FLEXIBLE set true to input url & output filename by user
IS_FLEXIBLE = False
INPUT_URL = "https://www.flyingv.cc/projects?filter=all&sort=end&category=product"
OUTPUT_FILENAME = "ethan-test"

# for internal usage
FIXED_COL_NAMES = [
    "商品名",
    "提案者",
    "目標金額",
    "募到總金額",
    "達成百分比",
    "贊助總人數",
    "募資開始日",
    "募資結束日",
    "FB連結",
    "官網連結",
    "專案介紹圖片",
    "專案介紹影片",
    "常見問題數量",
    "留言人數",
    "進度更新數量",
    "贊助方案數量",
]
DYNAMIC_COL_NAMES = ["金額", "贊助人數", "預計寄送時間", "限量個數", "內容簡介"]
CASE_PREFIX = "方案"


def get_valid_str(object):
    return object.text if object else ""


def check(project):
    success = project.find(class_="tag red")
    actual = get_valid_str(project.find(class_="date pull-right"))
    end = "已結束"
    if actual != end:
        # print("未結束")
        return False
    if SUCCESSFUL_OR_FAILED:
        if not success:
            # print("未成功")
            return False
    else:
        if success:
            # print("已成功")
            return False
    return True


def get_output_col_names(max_cols):
    col_names = FIXED_COL_NAMES.copy()
    extra_cols = (max_cols - len(FIXED_COL_NAMES)) / len(DYNAMIC_COL_NAMES)
    for i in range(int(extra_cols)):
        col_names.extend([f"{CASE_PREFIX}{i+1}{s}" for s in DYNAMIC_COL_NAMES])
    return col_names


class Crawler:
    project_infos = []
    finished_count = 0

    def run(self):
        options = Options()
        options.add_argument("--disable-notifications")

        chrome = webdriver.Chrome("./chromedriver", chrome_options=options)
        chrome.get(inputUrl)
        # 按下載入更多
        chrome.execute_script("$('.btn-more').click()")
        for i in range(SCROLL_COUNT):
            chrome.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
        soup = BeautifulSoup(chrome.page_source)

        self.projects = [p for p in soup.select(".projectCard")]

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.get_project_infos())

        chrome.quit()

    async def get_project_infos(self):
        tasks = []
        async with ClientSession() as session:
            for project in self.projects:
                if check(project):
                    tasks.append(
                        asyncio.create_task(self.get_project_info(project, session))
                    )
            self.total_task_count = len(tasks)
            await asyncio.gather(*tasks)

    async def get_project_info(self, project, session):
        project_info = []

        projectUrl = project.find("a", {"class": "projectUrl"})
        title = get_valid_str(project.find("h2", {"class": "title"}))
        creator = get_valid_str(project.find("p", {"class": "creator"}).a)
        goal_money = get_valid_str(project.find("span", {"class": "goalMoney"}))
        percent = get_valid_str(
            project.find("span", {"class": "hidden-md goalpercent goal"})
        )

        async with session.get(projectUrl["href"]) as response:
            html_body = await response.text()
            project_soup = BeautifulSoup(html_body, "lxml")
            ### start time & end time ###
            timeRaw = project_soup.find("blockquote")  # class_='success'
            if not timeRaw:
                print(projectUrl["href"])
                return []
            m = re.findall(r"\d{4}/\d{1,2}/\d{1,2}", timeRaw.text)
            start_time = m[0]
            end_time = m[1]
            ### external websites ###
            fb_url = ""
            web_url = ""
            detail = project_soup.find(class_="creator-detail")

            if detail.find(class_="creatorFanpage"):
                fb_url = detail.find(class_="creatorFanpage")["href"]
            if detail.find(class_="creatorWebsite"):
                web_url = detail.find(class_="creatorWebsite")["href"]

            ### check img & video ###
            has_img = ""
            has_video = ""
            story = project_soup.find(class_="story")
            img = story.find("img")
            video = story.find(class_="fr-video fr-fvc fr-dvb fr-draggable")
            topVideo = project_soup.find(class_="videoBlock")

            has_img = "v" if img else ""
            has_video = "v" if video or topVideo else ""

            total_people = get_valid_str(
                project_soup.find("div", {"class": "numberRow totalPeople"}).h2
            )
            progress_money = re.findall(
                "\d+",
                get_valid_str(
                    project_soup.find("p", {"class": "metatext moneyFormat"})
                ),
            )[0]

            progress = project_soup.find(class_="postNav")
            faqs = project_soup.find(class_="faqNav")
            comments = project_soup.find(class_="commentNav")

            progress_count = -1
            if progress != None:
                async with session.get(progress["href"]) as response:
                    body = await response.text()
                    progress_soup = BeautifulSoup(body, "lxml")
                    goals = progress_soup.find(class_="postWrapper").find_all(
                        class_="post post-goal"
                    )
                    items = progress_soup.find(class_="postWrapper").find_all(
                        class_="post post-item"
                    )
                    progress_count = len(goals) + len(items)

            faqs_count = -1
            if faqs:
                faq_url = faqs.get("href", None)
                if faq_url:
                    async with session.get(faq_url) as response:
                        body = await response.text()
                        faqs_soup = BeautifulSoup(body, "lxml")
                        questions = faqs_soup.find(class_="faqWrapper").find_all(
                            class_="faq"
                        )
                        faqs_count = len(questions)

            comments_count = -1
            if comments != None:
                async with session.get(comments["href"]) as response:
                    body = await response.text()
                    comments_soup = BeautifulSoup(body, "lxml")
                    comments_groups = comments_soup.find_all(
                        "div", {"class": "comment-group"}
                    )
                    comments_count = len(comments_groups)

            ### 商品名 提案者 目標金額 募到總金額 達成百分比 贊助總人數 留言人數 贊助方案數量 開始時間 結束時間 有圖片 有影片 常見問題數量 評論數量 發表進度數量
            project_info.append(title)
            project_info.append(creator)
            project_info.append(progress_money)
            project_info.append(goal_money)
            project_info.append(percent)
            project_info.append(total_people)
            project_info.append(start_time)
            project_info.append(end_time)
            project_info.append(fb_url)
            project_info.append(web_url)
            project_info.append(has_img)
            project_info.append(has_video)
            project_info.append(faqs_count)
            project_info.append(comments_count)
            project_info.append(progress_count)

            ### Cases ###
            offline_items = project_soup.find_all(class_="rewardItem offline")
            item_count = len(offline_items)

            project_info.append(item_count)

            for item in offline_items:
                ammount = item.find("div", {"class": "number pull-left"})
                # print(ammount.text)
                number = item.find("div", {"class": "meta-wrapper"}).find(
                    "p", {"class": "meta-detail"}
                )
                # print(number.text)
                containers = (
                    item.find(class_="cardrow rewardMeta container-fluid")
                    .find(class_="meta-wrapper")
                    .find_all(class_="meta-item")
                )
                sponsor_count = ""
                limit = ""
                expect_time = ""
                for c in containers:
                    label = c.find(class_="meta-label")
                    detail = c.find(class_="meta-detail")
                    if not label or not detail:
                        continue
                    if label.text == "贊助人數":
                        sponsor_count = detail.text
                    elif label.text == "限量":
                        limit = detail.text
                    elif label.text == "預計寄送時間":
                        expect_time = detail.text

                content = item.find(class_="cardrow rewardDes")

                project_info.append(ammount.text)
                project_info.append(sponsor_count)
                project_info.append(expect_time)
                project_info.append(limit)
                project_info.append(content.text)

        self.project_infos.append(project_info)
        self.finished_count += 1
        print(f"{self.finished_count}/{self.total_task_count}")

    def output(self, output_filename):
        print(f"Saving to {output_filename}...")
        max_cols = len(FIXED_COL_NAMES)
        for project_info in self.project_infos:
            max_cols = max(len(project_info), max_cols)
        col_names = get_output_col_names(max_cols)

        df = pd.DataFrame(data=self.project_infos, columns=col_names)
        df.to_excel(output_filename, encoding="utf-8")
        print(f"Saved to {output_filename}!")


if __name__ == "__main__":
    inputUrl = INPUT_URL
    output_filename = OUTPUT_FILENAME
    if IS_FLEXIBLE:
        inputUrl = input("Enter url: ")
        output_filename = input("Enter file name: ")
    start_time = time.time()

    crawler = Crawler()
    print("Start crawling!")
    crawler.run()
    postflix = "_success.xlsx" if SUCCESSFUL_OR_FAILED else "_failed.xlsx"
    output_filename += postflix
    crawler.output(output_filename)
    print("Finished crawling!")
    cost = float(time.time() - start_time)
    print(f"Cost %.2f s" % cost)
