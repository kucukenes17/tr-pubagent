from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import urlsplit

from playwright.async_api import Browser, Page, async_playwright
from .models import ProposedAction


@dataclass
class BrowserObservation:
    url: str
    page_title: str
    aria_tree: str
    visible_messages: list[str]
    run_id: str = ""
    step: int = 0
    status: str = ""


class BrowserActionError(ValueError):
    """The requested action is outside the browser's visible capabilities."""


class SafeBrowserEnvironment:
    """Yerel portal için alan adı kısıtlı Playwright ortamı."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        parsed = urlsplit(self.base_url)
        if (parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
                or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment):
            raise ValueError("Use a loopback HTTP origin without a path or credentials")
        self._origin = (parsed.scheme, parsed.hostname, parsed.port or 80)
        self.run_path: str | None = None
        self._playwright = None
        self.browser: Browser | None = None
        self.page: Page | None = None

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        try:
            self.browser = await self._playwright.chromium.launch(headless=True)
            context = await self.browser.new_context(service_workers="block")
            await context.route("**/*", self._route)
            self.page = await context.new_page()
            self.page.set_default_timeout(5000)
        except BaseException:
            await self.__aexit__()
            raise
        return self

    async def __aexit__(self, *_):
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def _route(self, route):
        if not self.allows_url(route.request.url):
            await route.abort("blockedbyclient")
            return
        await route.continue_()

    def allows_url(self, url: str) -> bool:
        parsed = urlsplit(url)
        try:
            origin = (parsed.scheme, parsed.hostname, parsed.port or 80)
        except ValueError:
            return False
        return bool(self.run_path and origin == self._origin and parsed.path == self.run_path
                    and not (parsed.username or parsed.password or parsed.query or parsed.fragment))

    async def open(self, path: str) -> BrowserObservation:
        assert self.page is not None
        if not re.fullmatch(r"/browser/runs/[a-f0-9]{32}", path):
            raise BrowserActionError("Only a benchmark run page can be opened")
        self.run_path = path
        response = await self.page.goto(f"{self.base_url}{path}", wait_until="domcontentloaded")
        if response is None or not response.ok:
            raise BrowserActionError("Run page unavailable; enable the local browser portal")
        return await self.observe()

    async def act(self, action: ProposedAction) -> BrowserObservation:
        assert self.page is not None
        if action.tool == "navigate":
            if action.target_id != self.run_path:
                raise BrowserActionError("Navigation outside the current run is forbidden")
            return await self.open(self.run_path)
        if action.tool not in {"fill", "select", "upload_fixture", "ask_user", "request_confirmation", "submit", "finish", "click"}:
            raise BrowserActionError("Unsupported browser tool")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", action.target_id):
            raise BrowserActionError("Invalid target identifier")
        form = self.page.locator(f'form[data-tool="{action.tool}"][data-target="{action.target_id}"]')
        if await form.count() != 1 or not await form.is_visible():
            raise BrowserActionError("No visible control for this action")
        button = form.get_by_role("button")
        if not await button.is_enabled():
            raise BrowserActionError("Run has already ended")
        if action.tool == "fill":
            value = action.arguments.get("value")
            if not isinstance(value, str) or len(value) > 4096:
                raise BrowserActionError("fill requires a string of at most 4096 characters")
            await form.locator('input[name="value"]').fill(value)
        elif action.tool == "select":
            value = action.arguments.get("option")
            options = [await option.get_attribute("value") for option in await form.locator("option").all()]
            if not isinstance(value, str) or value not in options or not value:
                raise BrowserActionError("Option is not present in the visible select")
            await form.get_by_role("combobox").select_option(value)
        elif action.tool == "upload_fixture":
            value = action.arguments.get("fixture_id")
            options = [await option.get_attribute("value") for option in await form.locator("option").all()]
            if not isinstance(value, str) or value not in options or not value:
                raise BrowserActionError("Fixture is not present in the visible allowlist")
            await form.get_by_role("combobox").select_option(value)
        async with self.page.expect_navigation(wait_until="domcontentloaded") as navigation:
            await button.click()
        response = await navigation.value
        if response is None or not response.ok:
            raise BrowserActionError("Portal rejected the operation")
        return await self.observe()

    async def observe(self) -> BrowserObservation:
        assert self.page is not None
        aria = await self.page.locator("body").aria_snapshot()
        messages = await self.page.locator("[role='alert'], output, [aria-live]").all_text_contents()
        main = self.page.locator("main[data-run-id]")
        return BrowserObservation(
            url=self.page.url, page_title=await self.page.title(), aria_tree=aria[:12000],
            visible_messages=[message.strip() for message in messages if message.strip()],
            run_id=await main.get_attribute("data-run-id") or "",
            step=int(await main.get_attribute("data-step") or 0),
            status=await main.get_attribute("data-status") or "",
        )
