import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]


def get_headers_search():
    return {
        "Content-Type": "application/json;charset=UTF-8",
        "Accept":       "application/json, text/plain, */*",
        "Referer":      "https://wuzzuf.net/",
        "User-Agent":   random.choice(USER_AGENTS),
        "Origin":       "https://wuzzuf.net",
    }

def get_headers_details():
    return {
        "Accept":       "application/vnd.api+json, application/json, */*",
        "Referer":      "https://wuzzuf.net/",
        "User-Agent":   random.choice(USER_AGENTS),
        "Origin":       "https://wuzzuf.net",
    }
