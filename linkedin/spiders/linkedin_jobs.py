import json
import scrapy
from urllib.parse import urlencode
import dotenv
import os


dotenv.load_dotenv()


def get_scrapeops_url(url):
    payload = {
        "api_key": os.getenv("SCRAPEOPS_API_KEY"),
        "url": url,
        "render_js": False,
    }
    proxy_url = "https://proxy.scrapeops.io/v1/?" + urlencode(payload)
    return proxy_url


class LinkedCompanySpider(scrapy.Spider):
    name = "linkedin_jobs"

    api_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Software%2Bdeveloper&location=United%2BStates&trk=public_jobs_jobs-search-bar_search-submit&start="

    def start_requests(self):
        first_job_on_page = 0
        first_url = self.api_url + str(first_job_on_page)
        yield scrapy.Request(
            url=get_scrapeops_url(first_url),
            callback=self.parse_job,
            meta={"first_job_on_page": first_job_on_page},
        )

    def parse_job(self, response):
        first_job_on_page = response.meta["first_job_on_page"]

        # job_item = {}
        # jobs = response.css("li")

        # get all company links
        company_links = response.css("h4 a::attr(href)").getall()
        # Yield a dictionary with the link
        for link in company_links:
            yield {"company_link": link}

        # num_jobs_returned = len(jobs)
        # print("******* Num Jobs Returned *******")
        # print(num_jobs_returned)
        # print("*****")

        # for job in jobs:
        #     job_item["job_title"] = job.css("h3::text").get(default="not-found").strip()
        #     job_item["job_detail_url"] = (
        #         job.css(".base-card__full-link::attr(href)")
        #         .get(default="not-found")
        #         .strip()
        #     )
        #     job_item["job_listed"] = (
        #         job.css("time::text").get(default="not-found").strip()
        #     )

        #     job_item["company_name"] = (
        #         job.css("h4 a::text").get(default="not-found").strip()
        #     )
        #     job_item["company_link"] = job.css("h4 a::attr(href)").get(
        #         default="not-found"
        #     )
        #     job_item["company_location"] = (
        #         job.css(".job-search-card__location::text")
        #         .get(default="not-found")
        #         .strip()
        #     )
        #     yield job_item

        #### REQUEST NEXT PAGE OF JOBS HERE ######
        if len(company_links) > 0:
            first_job_on_page = int(first_job_on_page) + 25
            next_url = self.api_url + str(first_job_on_page)
            yield scrapy.Request(
                url=get_scrapeops_url(next_url),
                callback=self.parse_job,
                meta={"first_job_on_page": first_job_on_page},
            )
