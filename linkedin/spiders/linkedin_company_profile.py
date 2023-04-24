from bs4 import BeautifulSoup
import json
import scrapy
from urllib.parse import urlencode
import dotenv
import os
import re


dotenv.load_dotenv()


def get_scrapeops_url(url):
    payload = {
        "api_key": os.getenv("SCRAPEOPS_API_KEY"),
        "url": url,
        "render_js": False
    }
    proxy_url = "https://proxy.scrapeops.io/v1/?" + urlencode(payload)
    return proxy_url


class LinkedCompanySpider(scrapy.Spider):
    name = "linkedin_company_profile"

    def read_jobs(self):
        with open("jobs.json") as f:
            jobs = json.load(f)
        return jobs

    def start_requests(self):
        company_pages = self.read_jobs()

        for i, company in enumerate(company_pages):
            yield scrapy.Request(
                url=get_scrapeops_url(company),
                callback=self.parse_response,
                meta={"company_index_tracker": i},
            )

    def get_content_type(self, post):
        if post.css("ul[data-test-id=feed-images-content]").get():
            return "image"

        if post.css("video").get():
            return "video"

        if post.css(".carousel-track-container").get() or post.css("iframe").get():
            return "carousel"

        if post.css(
            "a[data-tracking-control-name=organization_guest_main-feed-card_feed-article-content]"
        ).get():
            return "link"

        if post.css(".update-components-poll").get():
            return "poll"

        return "text"

    def replace_breaks_with_newlines(self, container):
        for br in container.find_all("br"):
            br.replace_with("\n")

    def extract_post_text(self, container):
        soup = BeautifulSoup(
            container.get(),
            "html.parser"
        )
        post = soup.find(
            "p", {"class": "attributed-text-segment-list__content"}
        )

        if not post:
            return ""

        self.replace_breaks_with_newlines(post)

        return post.text

    def txt_to_int(self, text):
        return int("".join(filter(str.isdigit, text)))

    def get_likes(self, post):
        likes = (
            post.css("span[data-test-id=social-actions__reaction-count]::text")
            .get(default="0")
        )
        return self.txt_to_int(likes)

    def get_comments(self, post):
        comments = (
            post.css("a[data-id=social-actions__comments]::text")
            .get(default="0")
        )
        return self.txt_to_int(comments)

    def follower_search(self, response):
        """get all <p> tags with tag "text-color-text-low-emphasis"
        check if it contains "followers"
        if yes, get the number
        if no, set to -1"""
        followers = -1

        for p in response.css("p.text-color-text-low-emphasis"):
            txt = p.css("::text").get(default="")

            if "followers" in txt:
                followers = self.txt_to_int(txt)
                break

        return followers

    def parse_response(self, response):
        company_index_tracker = response.meta["company_index_tracker"]

        if company_index_tracker % 100 == 0:
            print("***************")
            print("****** Scraping page " + str(company_index_tracker + 1))
            print("***************")

        company_item = {}

        company_item["name"] = (
            response.css(".top-card-layout__title::text")
            .get(default="")
            .strip()
        )

        company_item["summary"] = (
            response.css(".top-card-layout__second-subline span::text")
            .get(default="")
            .strip()
        )

        company_item["description"] = (
            response.css(".core-section-container__content p::text")
            .get(default="")
            .strip()
        )

        company_item["website"] = (
            response.css(
                "div[data-test-id=about-us__website] dd a::attr(href)")
            .get(default="")
            .strip()
        )

        company_item["industry"] = (
            response.css("div[data-test-id=about-us__industries] dd::text")
            .extract_first(default="")
            .strip()
        )

        company_item["headquarters"] = (
            response.css("div[data-test-id=about-us__headquarters] dd::text")
            .get(default="")
            .strip()
        )

        company_item["size"] = (
            response.css("div[data-test-id=about-us__size] dd::text")
            .get(default="")
            .strip()
        )

        company_item["type"] = (
            response.css(
                "div[data-test-id=about-us__organizationType] dd::text")
            .get(default="")
            .strip()
        )

        company_item["founded"] = (
            response.css("div[data-test-id=about-us__foundedOn] dd::text")
            .get(default="")
            .strip()
        )

        try:
            followers_text = response.css(
                "h3.top-card-layout__first-subline::text"
            ).getall()[-1]
            company_item["followers"] = int(
                "".join(filter(str.isdigit, followers_text))
            )
        except:
            company_item["followers"] = self.follower_search(response)

        posts = []
        for post in response.css("li.mb-1"):
            time = post.css("time::text").get(default="").strip()

            posts.append({
                "time": time,
                "text": self.extract_post_text(post),
                "likes": self.get_likes(post),
                "comments": self.get_comments(post),
                "content_type": self.get_content_type(post),
            })

        company_item["posts"] = posts

        yield company_item
