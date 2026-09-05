from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from playwright.async_api import Browser, Page, async_playwright


@dataclass
class BrowserObservation:
    url: str
    page_title: str
    aria_tree: str
    visible_messages: list[str]


class SafeBrowserEnvironment:
    """Yerel portal için alan adı kısıtlı Playwright ortamı."""

    def __init__(self, base_url: str = "http://127.0.0.1:3000"):
        self.base_url = base_url.rstrip("/")
        self.allowed_hosts = {urlparse(self.base_url).hostname, "localhost", "127.0.0.1"}
        self._playwright = None
        self.browser: Browser | None = None
        self.page: Page | None = None

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        await self.page.route("**/*", self._route)
        return self

    async def __aexit__(self, *_):
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def _route(self, route):
        host = urlparse(route.request.url).hostname
        if host not in self.allowed_hosts:
            await route.abort("blockedbyclient")
            return
        await route.continue_()

    async def open(self, path: str = "/portal") -> BrowserObservation:
        assert self.page is not None
        await self.page.goto(f"{self.base_url}{path}", wait_until="networkidle")
        return await self.observe()

    async def observe(self) -> BrowserObservation:
        assert self.page is not None
        aria = await self.page.locator("body").aria_snapshot()
        messages = await self.page.locator("[role='alert'], output, [aria-live]").all_text_contents()
        return BrowserObservation(url=self.page.url, page_title=await self.page.title(), aria_tree=aria[:12000], visible_messages=[message.strip() for message in messages if message.strip()])
