from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Dict, List, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


USER_AGENT = (
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
	"(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def _clean_soup(soup: BeautifulSoup) -> None:
	for tag in soup(["script", "style", "noscript", "svg", "form", "footer", "nav"]):
		tag.decompose()


def _collect_headings(soup: BeautifulSoup) -> List[str]:
	headings: List[str] = []
	for node in soup.select("h1, h2, h3, h4"):
		text = node.get_text(" ", strip=True)
		if text and len(text) >= 3:
			headings.append(text)
	return headings[:100]


def _collect_text_blocks(soup: BeautifulSoup) -> List[str]:
	blocks: List[str] = []
	for node in soup.select("article p, main p, p, li"):
		text = node.get_text(" ", strip=True)
		if text and len(text) >= 25:
			blocks.append(text)
	return blocks


def _parse_and_validate_url(url: str) -> None:
	parsed = urlparse(url)
	if parsed.scheme not in {"http", "https"} or not parsed.netloc:
		raise ValueError("请提供有效的 http/https 网页链接")


def _normalize_url(url: str) -> str:
	parsed = urlparse(url)
	path = parsed.path or "/"
	return f"{parsed.scheme}://{parsed.netloc}{path}"


def _build_candidate_urls(url: str, max_candidates: int = 16) -> List[str]:
	parsed = urlparse(url)
	base = f"{parsed.scheme}://{parsed.netloc}"
	original = _normalize_url(url)

	common_paths = [
		"/for-authors",
		"/authors",
		"/author-information",
		"/author-guidelines",
		"/guide-for-authors",
		"/submission-guidelines",
		"/submit",
		"/content/authorinfo",
		"/content/authors",
	]

	results: List[str] = []
	seen = set()

	def add_candidate(candidate_url: str) -> None:
		normalized = _normalize_url(candidate_url)
		if normalized not in seen:
			seen.add(normalized)
			results.append(normalized)

	add_candidate(original)

	if original.rstrip("/") != base:
		add_candidate(f"{original.rstrip('/')}/")

	for path in common_paths:
		add_candidate(f"{base}{path}")

	path_parts = [part for part in parsed.path.split("/") if part]
	for depth in range(len(path_parts), 0, -1):
		prefix = "/" + "/".join(path_parts[:depth])
		for suffix in ["for-authors", "authors", "submission-guidelines", "guide-for-authors"]:
			add_candidate(f"{base}{prefix}/{suffix}")

	return results[:max_candidates]


def _extract_page_data(response: requests.Response) -> Dict[str, object]:
	soup = BeautifulSoup(response.text, "html.parser")
	_clean_soup(soup)

	title_node = soup.find("title")
	page_title = title_node.get_text(strip=True) if title_node else ""
	headings = _collect_headings(soup)
	blocks = _collect_text_blocks(soup)

	page_text = "\n".join(blocks)
	if len(page_text) > 120000:
		page_text = page_text[:120000]

	return {
		"url": response.url,
		"fetched_at": datetime.now(timezone.utc).isoformat(),
		"status_code": response.status_code,
		"title": page_title,
		"headings": headings,
		"text": page_text,
	}


def _collect_candidate_subpage_urls(response: requests.Response, max_candidates: int = 20) -> List[str]:
	soup = BeautifulSoup(response.text, "html.parser")

	target_keywords = [
		"figure",
		"figures",
		"table",
		"references",
		"citation",
		"submission",
		"submit",
		"checklist",
		"ethics",
		"reporting",
		"format",
		"manuscript",
	]

	skip_extensions = (
		".pdf",
		".doc",
		".docx",
		".xls",
		".xlsx",
		".ppt",
		".pptx",
		".zip",
	)

	base_netloc = urlparse(response.url).netloc
	results: List[str] = []
	seen = set()

	for anchor in soup.select("a[href]"):
		href = anchor.get("href", "").strip()
		if not href or href.startswith("#"):
			continue

		absolute_url = urljoin(response.url, href)
		parsed = urlparse(absolute_url)
		if parsed.scheme not in {"http", "https"}:
			continue
		if parsed.netloc != base_netloc:
			continue
		if parsed.path.lower().endswith(skip_extensions):
			continue

		anchor_text = anchor.get_text(" ", strip=True).lower()
		url_text = absolute_url.lower()
		if not any(keyword in anchor_text or keyword in url_text for keyword in target_keywords):
			continue

		clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
		if clean_url in seen:
			continue

		seen.add(clean_url)
		results.append(clean_url)
		if len(results) >= max_candidates:
			break

	return results


def _http_get_with_retry(url: str, timeout_seconds: int = 20, retries: int = 2) -> requests.Response:
	last_exception: Exception | None = None
	for attempt in range(retries + 1):
		try:
			response = requests.get(
				url,
				timeout=timeout_seconds,
				headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8"},
			)
			response.raise_for_status()
			return response
		except requests.RequestException as exc:
			last_exception = exc
			if attempt < retries:
				time.sleep(0.8 * (attempt + 1))
				continue
			break

	if last_exception:
		raise last_exception

	raise RuntimeError("HTTP 请求失败")


def _resolve_main_response(url: str, timeout_seconds: int = 20) -> Tuple[requests.Response, List[Dict[str, object]], List[str]]:
	candidate_urls = _build_candidate_urls(url)
	attempts: List[Dict[str, object]] = []
	has_forbidden = False

	for candidate_url in candidate_urls:
		try:
			response = _http_get_with_retry(candidate_url, timeout_seconds=timeout_seconds)
			content_type = response.headers.get("Content-Type", "")
			if "text/html" not in content_type.lower():
				attempts.append({"url": candidate_url, "status": response.status_code, "result": "non-html"})
				continue

			attempts.append({"url": candidate_url, "status": response.status_code, "result": "success"})
			return response, attempts, candidate_urls
		except requests.HTTPError as exc:
			status_code = exc.response.status_code if exc.response is not None else None
			if status_code == 403:
				has_forbidden = True
			attempts.append({"url": candidate_url, "status": status_code, "result": "http-error"})
		except requests.RequestException:
			attempts.append({"url": candidate_url, "status": None, "result": "request-error"})

	if has_forbidden:
		raise PermissionError("候选页面均被目标网站拒绝访问（403）")

	raise RuntimeError("自动候选链接尝试后仍无法获取可用作者指南页面")


def fetch_guideline_page(url: str, timeout_seconds: int = 20) -> Dict[str, object]:
	_parse_and_validate_url(url)
	response, attempts, candidate_urls = _resolve_main_response(url, timeout_seconds=timeout_seconds)
	data = _extract_page_data(response)
	data["main_attempts"] = attempts
	data["candidate_urls"] = candidate_urls
	return data


def fetch_guideline_bundle(url: str, timeout_seconds: int = 20, max_subpages: int = 4) -> Dict[str, object]:
	_parse_and_validate_url(url)
	main_response, attempts, main_candidate_urls = _resolve_main_response(url, timeout_seconds=timeout_seconds)

	main_page = _extract_page_data(main_response)
	subpage_candidate_urls = _collect_candidate_subpage_urls(main_response)

	sub_pages: List[Dict[str, object]] = []
	visited_urls = {str(main_page.get("url", ""))}

	for candidate_url in subpage_candidate_urls:
		if candidate_url in visited_urls:
			continue
		if len(sub_pages) >= max_subpages:
			break

		try:
			sub_response = _http_get_with_retry(candidate_url, timeout_seconds=timeout_seconds)
			sub_pages.append(_extract_page_data(sub_response))
			visited_urls.add(candidate_url)
		except requests.RequestException:
			continue

	return {
		"main_page": main_page,
		"sub_pages": sub_pages,
		"visited_urls": sorted(visited_urls),
		"subpage_candidates": subpage_candidate_urls,
		"main_attempts": attempts,
		"main_candidates": main_candidate_urls,
	}
