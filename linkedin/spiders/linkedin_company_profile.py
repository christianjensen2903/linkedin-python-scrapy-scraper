from bs4 import BeautifulSoup
import json
import scrapy
from urllib.parse import urlencode
import dotenv
import os
import re
import time
from datetime import datetime


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
                cb_kwargs={"linkedin_url": company},
                meta={"company_index_tracker": i},
            )

    def get_number_of_images(self, post):
        image_container = post.css(
            "ul[data-test-id=feed-images-content] li"
        ).getall()

        n_images = len(image_container)

        extra_imgs = post.css(
            "div[data-test-id=feed-images-content__overlay]::text"
        ).get(default="")

        if extra_imgs:
            n_images += self.txt_to_int(extra_imgs)

        return n_images

    def get_content_type(self, post):
        if post.css("ul[data-test-id=feed-images-content]"):
            return "image"

        if post.css("video").get():
            return "video"

        if post.css(".carousel-track-container").get() or post.css("iframe").get():
            return "carousel"

        if post.css(
            "a[data-tracking-control-name=organization_guest_main-feed-card_feed-article-content]"
        ).get():
            return "link"

        if post.css(
            "a[data-test-id=feed-live-video-content]"
        ).get():
            return "live_stream"

        if post.css(
            "article[data-test-id=feed-reshare-content]"
        ):
            return "reshare"

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

    def get_basic_info(self, response):
        def get_simple(selector):
            return (
                response.css(selector)
                .get(default="")
                .strip()
            )

        needed_values = {
            "name": ".top-card-layout__title::text",
            "summary": ".top-card-layout__second-subline span::text",
            "description": ".core-section-container__content p::text",
            "website": "div[data-test-id=about-us__website] dd a::attr(href)",
            "industry": "div[data-test-id=about-us__industries] dd::text",
            "headquarters": "div[data-test-id=about-us__headquarters] dd::text",
            "size": "div[data-test-id=about-us__size] dd::text",
            "type": "div[data-test-id=about-us__organizationType] dd::text",
            "founded": "div[data-test-id=about-us__foundedOn] dd::text",
            "specialties": "div[data-test-id=about-us__specialties] dd::text",
        }
        company_item = {
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        for key, selector in needed_values.items():
            company_item[key] = get_simple(selector)

        return company_item

    def get_show_more_links(self, container):
        soup = BeautifulSoup(
            container,
            "html.parser"
        )
        links = soup.find_all("a")

        return [link["href"] for link in links]

    def get_affiliated_pages(self, response):
        container = response.css(
            "section[data-test-id=affiliated-pages]"
        ).get(default="")

        if not container:
            return []

        return self.get_show_more_links(container)

    def get_similar_pages(self, response):
        container = response.css(
            "section[data-test-id=similar-pages]"
        ).get(default="")

        if not container:
            return []

        return self.get_show_more_links(container)

    def is_repost(self, post):
        container = post.css(
            "p.main-feed-activity-card__header"
        ).get(default="")

        return "reposted" in container

    def parse_response(self, response, linkedin_url):
        with open("response.html", "w") as f:
            f.write(response.text)

        company_index_tracker = response.meta["company_index_tracker"]

        if company_index_tracker % 100 == 0:
            print("***********************")
            print(f"*** Scraping page {company_index_tracker + 1} ***")
            print("***********************")

        company_item = self.get_basic_info(response)
        company_item["linkedin_url"] = linkedin_url
        company_item["affiliated_pages"] = self.get_affiliated_pages(response)
        company_item["similar_pages"] = self.get_similar_pages(response)

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
            if self.is_repost(post):
                continue

            time = post.css("time::text").get(default="").strip()

            post_data = {
                "time": time,
                "text": self.extract_post_text(post),
                "likes": self.get_likes(post),
                "comments": self.get_comments(post),
                "content_type": self.get_content_type(post)
            }

            if post_data["content_type"] == "link":
                post_data["external_link"] = post.css(
                    "a[data-tracking-control-name=organization_guest_main-feed-card_feed-article-content]::attr(href)"
                ).get(default="")

            if post_data["content_type"] == "image":
                post_data["n_images"] = self.get_number_of_images(post)

            if post_data["text"]:
                posts.append(post_data)
            else:
                print("🔴 Missing text - happens sometimes")

        company_item["posts"] = posts

        yield company_item
