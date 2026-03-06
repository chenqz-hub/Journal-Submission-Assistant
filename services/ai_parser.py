from __future__ import annotations

import re
from typing import Dict, List, Optional


def _find_first_match(patterns: List[str], text: str, flags: int = re.IGNORECASE) -> Optional[re.Match[str]]:
	for pattern in patterns:
		match = re.search(pattern, text, flags)
		if match:
			return match
	return None


def _extract_evidence_lines(text: str, keywords: List[str], max_items: int = 5) -> List[str]:
	lines = [line.strip() for line in text.splitlines() if line.strip()]
	results: List[str] = []
	lowered = [keyword.lower() for keyword in keywords]
	for line in lines:
		line_lower = line.lower()
		if any(keyword in line_lower for keyword in lowered):
			results.append(line)
			if len(results) >= max_items:
				break
	return results


def _extract_sections(text: str) -> List[str]:
	section_candidates = [
		"title page",
		"abstract",
		"keywords",
		"introduction",
		"methods",
		"results",
		"discussion",
		"conclusion",
		"acknowledgments",
		"references",
	]
	text_lower = text.lower()
	return [section for section in section_candidates if section in text_lower]


def _build_cover_letter_draft(journal_name: str, rules: Dict[str, object]) -> str:
	reference_style = rules.get("reference_style") or "journal-required style"
	word_limit = rules.get("manuscript_word_limit")
	conflict_required = bool(rules.get("conflict_statement_required"))
	data_required = bool(rules.get("data_availability_required"))

	parts = [
		"Dear Editor,",
		"",
		f"Please consider our manuscript for publication in {journal_name}.",
	]

	if word_limit:
		parts.append(f"The manuscript is prepared in line with your author guidelines and is within the expected length ({word_limit} words-related requirement).")
	else:
		parts.append("The manuscript is prepared in line with your author guidelines.")

	parts.append(f"References and formatting have been checked against the journal requirements, including {reference_style} expectations when applicable.")

	if conflict_required:
		parts.append("All authors declare that there are no competing interests related to this submission.")

	if data_required:
		parts.append("A data availability statement has been included according to journal policy.")

	parts.extend(
		[
			"All authors have approved the manuscript and agree with this submission.",
			"",
			"Sincerely,",
			"Corresponding Author",
		]
	)

	return "\n".join(parts)


async def parse_journal_rules(page_data: Dict[str, object], use_llm: bool = True) -> Dict[str, object]:
	"""
	Hybrid Parsing with LLM fallback.
	"""
	# Always start with fast Regex
	regex_result = _parse_journal_rules_regex(page_data)
	
	rules = regex_result.get("rules", {})
	
	# Decide if LLM is needed
	# Thresholds: If word limits OR ref style missing
	limits_missing = (rules.get("manuscript_word_limit") is None)
	style_missing = (rules.get("reference_style") is None)
	
	if use_llm:
		try:
			from services.llm_helper import extract_rules_with_llm
			# Extract text, truncate if needed inside helper
			text = str(page_data.get("text", ""))
			if len(text) > 500: # Only bother if we have some text
				llm_extracted = await extract_rules_with_llm(text)
				
				if llm_extracted:
					# Merge LLM data into rules carefully
					# We trust Regex for precise number matches usually, but LLM for context
					# If Regex found NOTHING for a field, take LLM
					for field, value in llm_extracted.items():
						if value is not None:
							# Handle case where LLM returns a dictionary/object instead of a primitive
							if isinstance(value, dict) and 'value' in value:
								rules[field] = value['value']
							elif isinstance(value, dict):
								# Just grab the first value or stringify
								for v in value.values():
									if isinstance(v, (int, float, str)):
										rules[field] = v
										break
							else:
								rules[field] = value
							# Add to resolved items list for UI consistency?
							# Probably need to update the whole structure
					
					# Recalculate resolved items simply
					resolved = [
						{"field": k, "value": v, "confidence": 0.9} 
						for k, v in rules.items() 
						if v is not None and k != "required_sections" and k != "figure_formats"
					]
					regex_result["resolved_items"] = resolved
					regex_result["coverage_score"] = round(len(resolved) / 14, 2)
					regex_result["source_type"] = "hybrid-llm"
		except Exception as e:
			print(f"LLM augmentation error: {e}")

	return regex_result


def _parse_journal_rules_regex(page_data: Dict[str, object]) -> Dict[str, object]:
	text = str(page_data.get("text", ""))
	title = str(page_data.get("title", ""))
	headings = page_data.get("headings", []) if isinstance(page_data.get("headings"), list) else []

	main_word_count_match = _find_first_match(
		[
			r"(?:manuscript|article|paper|text|body)[^\n\.]{0,80}?\b(\d{3,5})\s*words?",
			r"(?:include|excluding)[^\n\.]{0,80}?\b(\d{3,5})\s*words?",
		],
		text,
	)
	# Filter low values for manuscript limit (e.g. < 1000) to avoid abstract confusion
	if main_word_count_match:
		val = int(main_word_count_match.group(1))
		if val < 500: # 500 words is too short for a paper, likely abstract
			main_word_count_match = None

	abstract_word_count_match = _find_first_match(
		[r"abstract[^\n\.]{0,80}?\b(\d{2,4})\s*words?", r"\b(\d{2,4})\s*words?[^\n\.]{0,80}?abstract"],
		text,
	)
	title_length_match = _find_first_match(
		[r"title[^\n\.]{0,80}?\b(\d{1,3})\s*(?:characters|words)", r"\b(\d{1,3})\s*(?:characters|words)[^\n\.]{0,80}?title"],
		text,
	)

	font_family_match = _find_first_match([r"(Times New Roman|Arial|Calibri|Helvetica|瀹嬩綋|浠垮畫)"], text)
	font_size_match = _find_first_match([r"\b(\d{1,2})\s*(?:pt|point)\b"], text)
	line_spacing_match = _find_first_match([r"(single[- ]spaced|double[- ]spaced|1\.5[- ]spaced|single spacing|double spacing)"], text)
	reference_style_match = _find_first_match([r"\b(APA|Vancouver|Harvard|IEEE|AMA|NLM|Chicago)\b"], text)
	dpi_match = _find_first_match([r"\b(\d{2,4})\s*dpi\b"], text)

	figure_formats = sorted(
		set(
			match.upper()
			for match in re.findall(r"\b(tif|tiff|eps|jpg|jpeg|png|pdf)\b", text, flags=re.IGNORECASE)
		)
	)

	cover_letter_required = "cover letter" in text.lower()
	ethics_required = any(k in text.lower() for k in ["ethics", "irb", "institutional review board"])
	conflict_required = any(k in text.lower() for k in ["conflict of interest", "competing interest"]) 
	data_availability_required = "data availability" in text.lower()

	extracted_items = [
		{
			"field": "manuscript_word_limit",
			"value": int(main_word_count_match.group(1)) if main_word_count_match else None,
			"confidence": 0.85 if main_word_count_match else 0.0,
		},
		{
			"field": "abstract_word_limit",
			"value": int(abstract_word_count_match.group(1)) if abstract_word_count_match else None,
			"confidence": 0.85 if abstract_word_count_match else 0.0,
		},
		{
			"field": "title_length_limit",
			"value": int(title_length_match.group(1)) if title_length_match else None,
			"confidence": 0.75 if title_length_match else 0.0,
		},
		{
			"field": "font_family",
			"value": font_family_match.group(1) if font_family_match else None,
			"confidence": 0.7 if font_family_match else 0.0,
		},
		{
			"field": "font_size_pt",
			"value": int(font_size_match.group(1)) if font_size_match else None,
			"confidence": 0.7 if font_size_match else 0.0,
		},
		{
			"field": "line_spacing",
			"value": line_spacing_match.group(1) if line_spacing_match else None,
			"confidence": 0.7 if line_spacing_match else 0.0,
		},
		{
			"field": "reference_style",
			"value": reference_style_match.group(1) if reference_style_match else None,
			"confidence": 0.65 if reference_style_match else 0.0,
		},
		{
			"field": "figure_min_dpi",
			"value": int(dpi_match.group(1)) if dpi_match else None,
			"confidence": 0.7 if dpi_match else 0.0,
		},
	]

	resolved_items = [item for item in extracted_items if item["value"] is not None]
	coverage_score = round(len(resolved_items) / len(extracted_items), 2)

	return {
		"source": {
			"url": page_data.get("url"),
			"title": title,
			"fetched_at": page_data.get("fetched_at"),
		},
		"rules": {
			"manuscript_word_limit": int(main_word_count_match.group(1)) if main_word_count_match else None,
			"abstract_word_limit": int(abstract_word_count_match.group(1)) if abstract_word_count_match else None,
			"title_length_limit": int(title_length_match.group(1)) if title_length_match else None,
			"font_family": font_family_match.group(1) if font_family_match else None,
			"font_size_pt": int(font_size_match.group(1)) if font_size_match else None,
			"line_spacing": line_spacing_match.group(1) if line_spacing_match else None,
			"reference_style": reference_style_match.group(1) if reference_style_match else None,
			"figure_min_dpi": int(dpi_match.group(1)) if dpi_match else None,
			"figure_formats": figure_formats,
			"required_sections": _extract_sections(text),
			"cover_letter_required": cover_letter_required,
			"ethics_statement_required": ethics_required,
			"conflict_statement_required": conflict_required,
			"data_availability_required": data_availability_required,
		},
		"evidence": {
			"wording_snippets": _extract_evidence_lines(
				text,
				[
					"word",
					"abstract",
					"font",
					"line spacing",
					"references",
					"dpi",
					"cover letter",
					"ethics",
					"conflict of interest",
				],
				max_items=8,
			),
			"headings": headings[:20],
		},
		"resolved_items": resolved_items,
		"coverage_score": coverage_score,
	}


async def parse_journal_rules_bundle(bundle_data: Dict[str, object]) -> Dict[str, object]:
	main_page = bundle_data.get("main_page", {}) if isinstance(bundle_data.get("main_page"), dict) else {}
	sub_pages = bundle_data.get("sub_pages", []) if isinstance(bundle_data.get("sub_pages"), list) else []

	all_pages: List[Dict[str, object]] = [main_page]
	all_pages.extend(page for page in sub_pages if isinstance(page, dict))

	combined_text_parts: List[str] = []
	combined_headings: List[str] = []
	page_summaries: List[Dict[str, object]] = []

	for page in all_pages:
		# Use regex only for individual page stats to be fast
		page_parsed = _parse_journal_rules_regex(page)
		page_rules = page_parsed.get("rules", {}) if isinstance(page_parsed.get("rules"), dict) else {}
		matched_fields = [
			field_name
			for field_name, field_value in page_rules.items()
			if field_value not in (None, [], "") and field_name != "required_sections"
		]

		page_text = str(page.get("text", ""))
		if page_text:
			combined_text_parts.append(page_text)

		headings = page.get("headings", []) if isinstance(page.get("headings"), list) else []
		combined_headings.extend(str(item) for item in headings)

		page_summaries.append(
			{
				"url": page.get("url"),
				"title": page.get("title"),
				"text_length": len(page_text),
				"matched_rule_fields": matched_fields,
				"matched_rule_count": len(matched_fields),
				"page_coverage_score": page_parsed.get("coverage_score", 0),
				"evidence_snippets": (
					page_parsed.get("evidence", {}).get("wording_snippets", [])[:3]
					if isinstance(page_parsed.get("evidence", {}), dict)
					else []
				),
			}
		)

	combined_page_data = {
		"url": main_page.get("url"),
		"title": main_page.get("title"),
		"fetched_at": main_page.get("fetched_at"),
		"headings": combined_headings,
		"text": "\n".join(combined_text_parts),
	}

	# Use hybrid mode for the final combined result if regex isn't perfect
	parsed = await parse_journal_rules(combined_page_data, use_llm=True)

	title_text = str(main_page.get("title", "Target Journal"))
	title_parts = [part.strip() for part in title_text.split("|") if part.strip()]
	if len(title_parts) >= 2:
		journal_name = title_parts[-1]
	else:
		journal_name = title_parts[0] if title_parts else "Target Journal"

	parsed["cover_letter"] = {
		"journal_name": journal_name,
		"draft": _build_cover_letter_draft(journal_name, parsed.get("rules", {})),
	}
	parsed["crawl"] = {
		"mode": "two-hop",
		"main_url": main_page.get("url"),
		"subpage_count": len(sub_pages),
		"pages": page_summaries,
		"visited_urls": bundle_data.get("visited_urls", []),
		"main_attempts": bundle_data.get("main_attempts", []),
		"main_candidates": bundle_data.get("main_candidates", []),
	}

	return parsed
