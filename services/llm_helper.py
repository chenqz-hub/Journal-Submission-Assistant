import os
import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for API Key
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

client = None
if API_KEY:
    client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)

async def extract_rules_with_llm(text: str) -> Dict[str, Any]:
    """
    Uses an LLM to extract journal submission rules from text.
    Returns a dictionary matching the internal rule structure.
    """
    if not client:
        print("Warning: LLM client not initialized. Missing OPENAI_API_KEY.")
        return {}

    # Increase text limit to utilize larger context window of modern models (e.g. Qwen-Plus)
    # 60,000 chars is roughly 15k-20k tokens.
    info_text = text[:60000]

    system_prompt = """
    You are an expert academic editor. Extract author guidelines from the provided text into a JSON object.
    
    IMPORTANT INSTRUCTION: 
    When extracting these guidelines, focus ONLY on the format requirements for "Original Articles" (or "Research Articles", "Original Research", "Full-length articles"). 
    ABSOLUTE RULE: YOU MUST ONLY EXTRACT DATA FOR "Original Articles" or "Full-length articles" or "Research Articles". IGNORE any rules about "Short communications", "Letters", "Brief Reports", "Editorials" or "Reviews". If there are multiple limits, choose the one for Original Articles.
    For example, if Original Articles say "3,500 words" and Short Communications say "1,500 words", you MUST extract "3500".
    Pay special attention to precise figure/image requirements (DPI, supported formats, resolution).

    Return ONLY raw JSON (no markdown formatting).
    Target JSON structure:
    {
        "manuscript_word_limit": int | string | null (Full paper word count OR page limit. e.g. 5000 or "15 pages"),
        "abstract_word_limit": int | string | null,
        "title_length_limit": int | string | null,
        "font_family": string | null (e.g. "Times New Roman". default to null if ambiguous),
        "font_size_pt": int | null,
        "line_spacing": string | null (e.g. "double", "single", "1.5"),
        "reference_style": string | null (e.g. "APA", "Vancouver", "Harvard", "IEEE", "AMA"),
        "figure_min_dpi": int | null (Extract the general/halftone/color image minimum DPI, typically 300. DO NOT extract the line-art DPI such as 1000 or 1200 unless it is the only one mentioned),
        "figure_formats": [string] (e.g. ["TIFF", "EPS"]),
        "cover_letter_required": boolean,
        "ethics_statement_required": boolean,
        "conflict_statement_required": boolean,
        "data_availability_required": boolean
    }
    If a value is not found, use null or false as appropriate.
    """

    user_prompt = f"Here is the text from the Author Guidelines:\n\n{info_text}"
    
    print(f"DEBUG: Sending request to LLM ({MODEL_NAME})... Text length: {len(info_text)}")

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if not content:
            return {}
            
        # Clean up markdown code blocks if present (common with some models)
        content = content.replace("```json", "").replace("```", "").strip()
        
        try:
            data = json.loads(content)
            return data
        except json.JSONDecodeError:
            print(f"LLM JSON Decode Error. Raw content: {content[:100]}...")
            return {}
            
    except Exception as e:
        print(f"LLM Extraction failed: {e}")
        return {}


async def revise_cover_letter_with_llm(existing_cover_letter: str, journal_name: str, rules_json: str) -> str:
    """
    Revise an existing Cover Letter using LLM based on user's draft and journal rules.
    """
    if not client:
        print("Warning: LLM client not initialized for Cover Letter.")
        return ""

    system_prompt = """You are a highly experienced academic editor. Your task is to REVISE the user's existing Cover Letter draft for a new journal submission.

Requirements for Revision:
1. Preserve the user's original scientific content, tone, and paragraph structure as much as possible. Do NOT write a new letter from scratch.
2. Replace any old journal names in the draft with the provided 'Target Journal Name'. If the new name isn't provided, use '[Target Journal]'.
3. Check the provided 'Journal Rules'. Focus specifically on mandatory declarations (e.g., Conflict of Interest statement, Data Availability statement, Ethical approval, Author contributions). 
4. If a rule says a statement is "required" (true) but you cannot clearly find it in the user's draft, seamlessly ADD a standard professional statement for it at the end of the letter (just before the sign-off).
5. Do NOT include any markdown formatting (e.g. ```), code blocks, or explanations of what you did. Just return the pure text of the revised letter.
"""

    user_prompt = f"Target Journal Name: {journal_name or 'Not specified'}\n\nJournal Rules:\n{rules_json}\n\nExisting Cover Letter Draft:\n{existing_cover_letter[:8000]}"

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        return content.strip()
    except Exception as e:
        print(f"LLM Cover Letter revision failed: {e}")
        # Return the error message so the caller knows what happened
        raise ValueError(f"澶фā鍨嬭皟鐢ㄥけ璐? {str(e)}")

async def reformat_references_with_llm(refs_text: str, target_style: str) -> str:
    """
    Uses an LLM to reformat a raw reference list into the target style (e.g., Vancouver, APA).
    """
    if not client:
        print("Warning: LLM client not initialized for reference formatting.")
        return refs_text

    system_prompt = """
    You are an expert academic copyeditor. Your task is to reformat the provided list of references strictly into the requested citation style.
    Requirements:
    1. Output strictly the newly formatted references, keeping the original order.
    2. Maintain one reference per line. Start each line appropriately (e.g., [1], [2] for Vancouver, or hanging names for APA).
    3. Do NOT output any markdown, conversational text, explanations, or headings like 'References'. Only the raw text list.
    """

    user_prompt = f"Target Formatting Style: {target_style}\n\nReferences to convert:\n{refs_text[:30000]}"

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM reference formatting failed: {e}")
        return refs_text
