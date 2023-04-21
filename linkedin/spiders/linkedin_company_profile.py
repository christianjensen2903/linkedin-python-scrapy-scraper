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
            response.css(".top-card-layout__title h1::text")
            .get(default="not-found")
            .strip()
        )
        company_item["summary"] = (
            response.css(".top-card-layout__second-subline h4 span::text")
            .get(default="not-found")
            .strip()
        )

        company_item["description"] = (
            response.css(".core-section-container__content p::text")
            .get(default="not-found")
            .strip()
        )

        company_details = response.css(".core-section-container__content .mb-2")

        try:
            company_website_line = company_details[0].css(".text-md::text").getall()
            company_item["website"] = company_website_line[1].strip()
        except:
            company_item["website"] = "not-found"

        try:
            company_industry_line = company_details[1].css(".text-md::text").getall()
            company_item["industry"] = company_industry_line[1].strip()
        except:
            company_item["industry"] = "not-found"

        try:
            company_size_line = company_details[2].css(".text-md::text").getall()
            company_item["size"] = company_size_line[1].strip()
        except:
            company_item["size"] = "not-found"

        try:
            company_size_line = company_details[5].css(".text-md::text").getall()
            company_item["founded"] = company_size_line[1].strip()
        except:
            company_item["founded"] = "not-found"

        yield company_item
