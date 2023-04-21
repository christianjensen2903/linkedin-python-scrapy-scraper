import json
import scrapy
from urllib.parse import urlencode
import dotenv
import os


dotenv.load_dotenv()


def get_scrapeops_url(url):
    payload = {"api_key": os.getenv("SCRAPEOPS_API_KEY"), "url": url, "render_js": True}
    proxy_url = "https://proxy.scrapeops.io/v1/?" + urlencode(payload)
    return proxy_url


class LinkedCompanySpider(scrapy.Spider):
    name = "linkedin_company_profile"

    # add your own list of company urls here
    company_pages = [
        "https://www.linkedin.com/company/usebraintrust",
        "https://www.linkedin.com/company/copenhagen-fintech",
    ]

    def start_requests(self):
        # uncomment below if reading the company urls from a file instead of the self.company_pages array

        for i, company in enumerate(self.company_pages):
            yield scrapy.Request(
                url=get_scrapeops_url(company),
                callback=self.parse_response,
                meta={"company_index_tracker": i},
            )

    def parse_response(self, response):
        company_index_tracker = response.meta["company_index_tracker"]
        print("***************")
        print(
            "****** Scraping page "
            + str(company_index_tracker + 1)
            + " of "
            + str(len(self.company_pages))
        )
        print("***************")

        company_item = {}

        company_item["name"] = (
            response.css(".top-card-layout__title::text")
            .get(default="not-found")
            .strip()
        )
        company_item["summary"] = (
            response.css(".top-card-layout__second-subline span::text")
            .get(default="not-found")
            .strip()
        )

        company_item["description"] = (
            response.css(".core-section-container__content p::text")
            .get(default="not-found")
            .strip()
        )

        company_item["website"] = (
            response.css("div[data-test-id=about-us__website] dd a::attr(href)")
            .get(default="not-found")
            .strip()
        )

        company_item["industry"] = (
            response.css("div[data-test-id=about-us__industries] dd::text")
            .extract_first(default="not-found")
            .strip()
        )

        company_item["headquarters"] = (
            response.css("div[data-test-id=about-us__headquarters] dd::text")
            .get(default="not-found")
            .strip()
        )

        company_item["size"] = (
            response.css("div[data-test-id=about-us__size] dd::text")
            .get(default="not-found")
            .strip()
        )

        company_item["type"] = (
            response.css("div[data-test-id=about-us__organizationType] dd::text")
            .get(default="not-found")
            .strip()
        )

        company_item["founded"] = (
            response.css("div[data-test-id=about-us__foundedOn] dd::text")
            .get(default="not-found")
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
            company_item["followers"] = -1

        # Get posts
        posts = []
        for post in response.css("li.mb-1"):
            time = post.css("time::text").get(default="not-found").strip()
            text = (
                post.css(".attributed-text-segment-list__content::text")
                .get(default="not-found")
                .strip()
            )
            likes = (
                post.css("span[data-test-id=social-actions__reaction-count]::text")
                .get(default="0")
                .strip()
            )

            comments = (
                post.css("a[data-test-id=social-actions__comment-count]::text")
                .get(default="0")
                .strip()
            )

            if (
                post.css(".feed-images-content__list").get(default="not-found").strip()
                != "not-found"
            ):
                has_image = True
            else:
                has_image = False

            if post.css("video").get(default="not-found").strip() != "not-found":
                has_video = True
            else:
                has_video = False

            if (
                post.css(".carousel-track-container").get(default="not-found").strip()
                != "not-found"
            ):
                has_carousel = True
            else:
                has_carousel = False

            if (
                post.css(
                    "a[data-tracking-control-name=organization_guest_main-feed-card_feed-article-content]"
                )
                .get(default="not-found")
                .strip()
            ) != "not-found":
                has_link = True
            else:
                has_link = False

            if has_image:
                content_type = "image"
            elif has_video:
                content_type = "video"
            elif has_carousel:
                content_type = "carousel"
            elif has_link:
                content_type = "link"
            else:
                content_type = "text"

            post_item = {
                "time": time,
                "text": text,
                "likes": likes,
                "comments": comments,
                "content_type": content_type,
            }
            posts.append(post_item)

        company_item["posts"] = posts

        yield company_item
