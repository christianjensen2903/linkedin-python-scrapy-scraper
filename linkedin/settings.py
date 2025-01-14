# Scrapy settings for linkedin project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import dotenv
import os

BOT_NAME = "linkedin"

SPIDER_MODULES = ["linkedin.spiders"]
NEWSPIDER_MODULE = "linkedin.spiders"
LOG_LEVEL = 'INFO'
CONCURRENT_REQUESTS = 25
CONCURRENT_REQUESTS_PER_DOMAIN = 25

# Obey robots.txt rules
ROBOTSTXT_OBEY = False
