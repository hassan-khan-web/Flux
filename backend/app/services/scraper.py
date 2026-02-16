import os
import random
import time
import asyncio
import urllib.parse
from typing import Any, Dict, List, Optional, Union, Tuple, cast
import tenacity
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, retry_if_result

import httpx
from app.utils.logger import logger
from prometheus_client import Counter, Histogram
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, retry_if_result, RetryError

SCRAPE_REQUESTS = Counter(
    "flux_scrape_requests_total",
    "Total number of scrape requests",
    ["provider", "status"]
)

SCRAPE_DURATION = Histogram(
    "flux_scrape_duration_seconds",
    "Histogram of scrape duration",
    ["provider"]
)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

class ScraperService:
    def __init__(self):
        self.scrapingbee_key = os.getenv("SCRAPINGBEE_API_KEY")
        self.zenrows_key = os.getenv("ZENROWS_API_KEY")
        self.tavily_key = os.getenv("TAVILY_API_KEY")
        
        self.provider_health = {
            "tavily": {"success": 0, "failure": 0},
            "scrapingbee": {"success": 0, "failure": 0},
            "zenrows": {"success": 0, "failure": 0},
            "direct": {"success": 0, "failure": 0}
        }

        if not any([self.scrapingbee_key, self.zenrows_key, self.tavily_key]):
            logger.warning("No scraping API keys found in environment variables")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(httpx.TimeoutException) | retry_if_result(lambda res: res is None),
        reraise=False,
        retry_error_callback=lambda retry_state: None
    )
    async def _fetch_tavily_extract(self, url: str) -> Optional[Dict]:
        start_time = time.time()
        try:
            logger.info("Attempting Tavily Extract...")
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.tavily.com/extract",
                    json={
                        "api_key": self.tavily_key,
                        "urls": [url],
                        "include_images": False
                    }
                )
                duration = time.time() - start_time
                SCRAPE_DURATION.labels(provider="tavily_extract").observe(duration)

                if response.status_code == 200:
                    SCRAPE_REQUESTS.labels(provider="tavily_extract", status="success").inc()
                    data = response.json()
                    if data.get("results") and isinstance(data["results"], list) and len(data["results"]) > 0:
                        result = data["results"][0]
                        if isinstance(result, dict):
                            return result

                SCRAPE_REQUESTS.labels(provider="tavily_extract", status="error").inc()
                logger.warning(f"Tavily Extract failed with status {response.status_code}: {response.text}")
        except Exception as e:
            SCRAPE_REQUESTS.labels(provider="tavily_extract", status="exception").inc()
            logger.error(f"Tavily Extract error: {e}")
        return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(httpx.TimeoutException) | retry_if_result(lambda res: res is None),
        reraise=False,
        retry_error_callback=lambda retry_state: None
    )
    async def _fetch_tavily(self, query: str, limit: int = 10) -> Optional[Dict]:
        start_time = time.time()
        try:
            logger.info(f"Attempting Tavily fetch with limit={limit}...")
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self.tavily_key,
                        "query": query,
                        "search_depth": "advanced",
                        "include_answer": True,
                        "include_images": False,
                        "max_results": limit
                    }
                )
                duration = time.time() - start_time
                SCRAPE_DURATION.labels(provider="tavily_search").observe(duration)

                if response.status_code == 200:
                    SCRAPE_REQUESTS.labels(provider="tavily_search", status="success").inc()
                    data = response.json()
                    if isinstance(data, dict):
                        return data

                SCRAPE_REQUESTS.labels(provider="tavily_search", status="error").inc()
                logger.warning(f"Tavily failed with status {response.status_code}: {response.text}")
        except httpx.RequestError as e:
            SCRAPE_REQUESTS.labels(provider="tavily_search", status="exception").inc()
            logger.error("Tavily error: %s", e)
        return None

    async def scrape_url(self, url: str) -> Optional[Union[str, Dict]]:
        # Road to 9/10: Health-aware provider selection
        providers: List[Tuple[str, Any]] = []
        if self.tavily_key: providers.append(("tavily", self._fetch_tavily_extract))
        if self.scrapingbee_key: providers.append(("scrapingbee", self._fetch_scrapingbee))
        if self.zenrows_key: providers.append(("zenrows", self._fetch_zenrows))
        providers.append(("direct", self._fetch_direct))

        # Sort by health (success rate)
        def get_health_score(p_tuple):
            p_name = p_tuple[0]
            stats = self.provider_health.get(p_name, {"success": 0, "failure": 0})
            total = stats["success"] + stats["failure"]
            if total == 0: return 1.0 # Default to high for new/unknown
            return stats["success"] / total

        sorted_providers = sorted(providers, key=get_health_score, reverse=True)

        for name, fetch_func in sorted_providers:
            try:
                data = await fetch_func(url)
                if data:
                    self.provider_health[name]["success"] += 1
                    return cast(Optional[Union[str, Dict[Any, Any]]], data)
                self.provider_health[name]["failure"] += 1
            except Exception as e:
                logger.error(f"Provider {name} failed: {e}")
                self.provider_health[name]["failure"] += 1

        return None

    async def scrape_multiple_urls(self, urls: List[str]) -> List[Optional[Union[str, Dict]]]:
        """Scrapes multiple URLs in parallel."""
        tasks = [self.scrape_url(url) for url in urls]
        return await asyncio.gather(*tasks)

    async def fetch_results(self, query: str, region: str = "us", language: str = "en", limit: int = 10) -> Optional[Union[str, Dict]]:
        params = {"q": query, "gl": region, "hl": language, "num": limit}
        search_url = f"https://www.google.com/search?{urllib.parse.urlencode(params)}"

        if self.tavily_key:
            data = await self._fetch_tavily(query, limit)
            if data: return data

        html = None
        debug_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "debug.html")

        if self.scrapingbee_key:
            html = await self._fetch_scrapingbee(search_url)
            if html and self._is_valid_html(html): return html

        if self.zenrows_key:
            html = await self._fetch_zenrows(search_url)
            if html and self._is_valid_html(html): return html

        res = await self._fetch_direct(search_url)
        final_html = html if html else res
        if final_html:
            try:
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(final_html)
                logger.info(f"Saved debug HTML to {debug_path}")
            except Exception as e:
                logger.error("Failed to save debug HTML: %s", e)

        return final_html

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(httpx.TimeoutException),
        reraise=False,
        retry_error_callback=lambda retry_state: None
    )
    async def _fetch_scrapingbee(self, url: str) -> Optional[str]:
        start_time = time.time()
        try:
            logger.info("Attempting ScrapingBee fetch...")
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    "https://app.scrapingbee.com/api/v1/",
                    params={
                        "api_key": self.scrapingbee_key,
                        "url": url,
                        "render_js": "true",
                        "premium_proxy": "true",
                        "stealth_proxy": "true",
                        "block_resources": "false",
                        "country_code": "us",
                        "device": "desktop"
                    }
                )
                duration = time.time() - start_time
                SCRAPE_DURATION.labels(provider="scrapingbee").observe(duration)

                if response.status_code == 200:
                    SCRAPE_REQUESTS.labels(provider="scrapingbee", status="success").inc()
                    return response.text

                SCRAPE_REQUESTS.labels(provider="scrapingbee", status="error").inc()
                logger.warning(f"ScrapingBee failed with status {response.status_code}")
        except httpx.RequestError as e:
            SCRAPE_REQUESTS.labels(provider="scrapingbee", status="exception").inc()
            logger.error("ScrapingBee error: %s", e)
        return None

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(httpx.TimeoutException),
        reraise=False,
        retry_error_callback=lambda retry_state: None
    )
    async def _fetch_zenrows(self, url: str) -> Optional[str]:
        start_time = time.time()
        try:
            logger.info("Attempting ZenRows fetch...")
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    "https://api.zenrows.com/v1/",
                    params={
                        "apikey": self.zenrows_key,
                        "url": url,
                        "js_render": "true",
                        "premium_proxy": "true",
                        "antibot": "true",
                        "location": "United States"
                    }
                )
                duration = time.time() - start_time
                SCRAPE_DURATION.labels(provider="zenrows").observe(duration)

                if response.status_code == 200:
                    SCRAPE_REQUESTS.labels(provider="zenrows", status="success").inc()
                    return response.text

                SCRAPE_REQUESTS.labels(provider="zenrows", status="error").inc()
                logger.warning(f"ZenRows failed with status {response.status_code}")
        except httpx.RequestError as e:
            SCRAPE_REQUESTS.labels(provider="zenrows", status="exception").inc()
            logger.error("ZenRows error: %s", e)
        return None

    async def _fetch_direct(self, url: str) -> Optional[str]:
        try:
            logger.info("Attempting direct fetch fallback...")
            headers = {"User-Agent": random.choice(USER_AGENTS)}  # nosec B311
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    if "captcha" in response.text.lower():
                        logger.warning("Direct fetch encountered CAPTCHA")
                        return None
                    return response.text
                logger.warning(f"Direct fetch failed with status {response.status_code}")
        except httpx.RequestError as e:
            logger.error("Direct fetch error: %s", e)
        return None

    def _is_valid_html(self, html: Optional[str]) -> bool:
        if not html:
            return False

        failure_markers = [
            "Please click here if you are not redirected",
            "having trouble accessing Google Search",
            "detected unusual traffic",
            "Our systems have detected unusual traffic"
        ]

        for marker in failure_markers:
            if marker in html:
                logger.warning(f"Detected invalid HTML with marker: {marker}")
                return False

        return True

    def get_health(self) -> Dict[str, Dict[str, int]]:
        return self.provider_health

scraper = ScraperService()
