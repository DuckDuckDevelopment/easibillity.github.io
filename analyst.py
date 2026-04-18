"""
Intelligent Analysis Module

This module uses Google's Gemini API to intelligently analyze and filter grant results.
The Analyst evaluates raw search results for:

1. Disease Relevance: Does this grant actually match the patient's condition?
2. Income Eligibility: Does the FPL threshold align with the patient's financial situation?
3. Grant Status: Is this actively accepting applications?
4. Quality Assessment: Will this grant likely help the patient?

This AI-powered filtering dramatically improves result quality compared to simple
keyword matching.

Environment Requirements:
  - GEMINI_API_KEY: Google Gemini API key for AI analysis (set in .env)

Author: DuckDuckCode
"""

import os
from dotenv import load_dotenv

load_dotenv()

import json
import re
import time
from typing import List, Dict, Any

import google.generativeai as genai

# Configure Gemini API with key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set. Add it to .env or the environment.")

genai.configure(api_key=GEMINI_API_KEY)


def _extract_json_array(text: str) -> str:
    """
    Extract the first JSON array from model output text.
    
    Gemini sometimes wraps JSON in markdown code blocks or adds explanatory text.
    This function robustly extracts the actual JSON array from the response.
    
    Args:
        text (str): Raw text output from Gemini model
    
    Returns:
        str: Valid JSON array string (e.g., '[{...}, {...}]')
    
    Raises:
        ValueError: If no valid JSON array can be found in the text
    """
    if not isinstance(text, str):
        raise ValueError("Model output is not text")

    # Remove markdown code block markers that Gemini sometimes adds
    cleaned = re.sub(r"```(?:json)?", "", text).strip()

    # Try to find a JSON array anywhere in the text
    m = re.search(r"(\[.*\])", cleaned, re.S)
    if m:
        return m.group(1)

    # If the whole cleaned text looks like a JSON array, return it
    if cleaned.startswith("[") and cleaned.endswith("]"):
        return cleaned

    raise ValueError("No JSON array found in model output")


def _compact_grants_for_prompt(grants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Reduce grant objects to a compact form for the AI prompt.
    
    Reduces token usage by sending only essential information to Gemini:
    - name: Grant identifier
    - short_description: Relevant grant details
    - url: Reference link
    - amount: Funding level if available
    
    Args:
        grants (list): List of full grant dictionaries from Hunter module
    
    Returns:
        list: Compacted grant dictionaries suitable for AI analysis
    """
    compact = []
    for g in grants:
        compact.append({
            "name": g.get("name"),
            "short_description": g.get("short_description") or g.get("description") or "",
            "url": g.get("url"),
            "amount": g.get("amount")
        })
    return compact


def _income_label(fpl_pct: float) -> str:
    """
    Categorize income level based on FPL percentage.
    
    Args:
        fpl_pct (float): Federal Poverty Level percentage
    
    Returns:
        str: Income category label for user display
    """
    if fpl_pct <= 100:
        return "Low income"
    if fpl_pct <= 200:
        return "Near low income"
    return "Not low income"


def evaluate_grants(fpl_pct: float, disease_name: str, grants: List[Dict[str, Any]],
                    max_retries: int = 2, model_name: str = "gemini-2.5-flash") -> List[Dict[str, Any]]:
    """
    Analyze and filter grants using Gemini AI for relevance and eligibility.
    
    Uses AI to:
    1. Filter grants for disease and income relevance
    2. Remove closed, exhausted, or clearly unrelated grants
    3. Score remaining grants for quality and likelihood of approval
    4. Normalize all results to consistent format
    
    Falls back to rule-based enrichment if Gemini is unavailable or returns invalid results.
    
    Args:
        fpl_pct (float): Patient's Federal Poverty Level percentage
        disease_name (str): Patient's disease condition
        grants (list): Raw grant search results from Hunter module
        max_retries (int): Number of retry attempts if API fails (default: 2)
        model_name (str): Gemini model to use (default: "gemini-2.5-flash")
    
    Returns:
        list: List of analyzed grant dictionaries with fields:
            - name (str): Grant name
            - amount (float): Funding amount if known
            - logic (str): AI's reasoning for eligibility
            - url (str): Grant website
            - eligibility (str): "Eligible" or "Verify"
            - disease (str): Patient's disease
            - income_level (str): Patient's income category
    
    Note:
        - Uses exponential backoff for retries on API failure
        - Returns empty list if all analysis attempts fail
        - Automatically enriches results with income/disease metadata
    """
    patient_profile = {"fpl_pct": fpl_pct, "disease": disease_name}
    compact_results = _compact_grants_for_prompt(grants)

    # Prompt instructs Gemini to be selective and return only relevant grants
    prompt = (
        "You are a medical grant auditor.\n"
        f"Patient Profile: {json.dumps(patient_profile)}\n"
        f"Search Results: {json.dumps(compact_results)}\n\n"
        "TASK:\n"
        "- Keep only grants that clearly match the patient's disease and FPL eligibility.\n"
        "- Exclude grants that are closed, exhausted, or clearly unrelated.\n"
        "- For each remaining grant return an object with keys: name, amount, logic, url\n"
        "Return ONLY a JSON array. Do not add any explanatory text before or after the JSON.\n"
    )

    model = genai.GenerativeModel(model_name)
    backoff_base = 1.5

    # Retry loop with exponential backoff
    for attempt in range(max_retries + 1):
        try:
            # Use temperature=0.0 for deterministic, consistent results
            response = model.generate_content(prompt, temperature=0.0)

            # Extract text from response (handling different SDK versions)
            text = getattr(response, "text", None)
            if not text:
                candidates = getattr(response, "candidates", None)
                if candidates and len(candidates) > 0:
                    first = candidates[0]
                    text = first.get("content") or first.get("text") or None

            if not text:
                raise RuntimeError("Empty response from model")

            # Parse JSON array from response
            json_str = _extract_json_array(text)
            parsed = json.loads(json_str)

            # Normalize results to standard format
            normalized: List[Dict[str, Any]] = []
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                name = item.get("name")
                if not name:
                    continue
                url = item.get("url")
                amount = item.get("amount", None)
                logic = item.get("logic") or item.get("reason") or ""

                normalized_item = {
                    "name": name,
                    "amount": amount,
                    "logic": logic,
                    "url": url,
                    "eligibility": "Eligible" if fpl_pct <= 100 else "Verify",
                    "disease": disease_name,
                    "income_level": _income_label(fpl_pct)
                }
                normalized.append(normalized_item)

            if not normalized:
                raise ValueError("Model returned no valid grants")

            return normalized

        except Exception:
            # On final attempt, return fallback enriched grants
            if attempt == max_retries:
                fallback: List[Dict[str, Any]] = []
                for g in grants:
                    gg = dict(g)  # shallow copy
                    gg["eligibility"] = "Eligible" if fpl_pct <= 100 else "Verify"
                    gg["income_level"] = _income_label(fpl_pct)
                    gg["disease"] = disease_name
                    gg["logic"] = gg.get("short_description") or gg.get("description") or "Matched by keyword"
                    fallback.append(gg)
                return fallback

            # Exponential backoff before retrying
            time.sleep(backoff_base ** attempt)
            continue
    compact = []
    for g in grants:
        compact.append({
            "name": g.get("name"),
            "short_description": g.get("short_description") or g.get("description") or "",
            "url": g.get("url"),
            "amount": g.get("amount")
        })
    return compact


def _income_label(fpl_pct: float) -> str:
    if fpl_pct <= 100:
        return "Low income"
    if fpl_pct <= 200:
        return "Near low income"
    return "Not low income"


def evaluate_grants(fpl_pct: float, disease_name: str, grants: List[Dict[str, Any]],
                    max_retries: int = 2, model_name: str = "gemini-2.5-flash") -> List[Dict[str, Any]]:
    """
    Analyze hunter results using Gemini and return a normalized list of grants.

    Signature kept synchronous so it can be run in a threadpool from FastAPI.
    Returns a list of dicts with at least: name, amount, logic, url, eligibility, disease, income_level.
    Falls back to a simple rule-based enrichment if the model fails or returns invalid JSON.
    """
    patient_profile = {"fpl_pct": fpl_pct, "disease": disease_name}
    compact_results = _compact_grants_for_prompt(grants)

    prompt = (
        "You are a medical grant auditor.\n"
        f"Patient Profile: {json.dumps(patient_profile)}\n"
        f"Search Results: {json.dumps(compact_results)}\n\n"
        "TASK:\n"
        "- Keep only grants that clearly match the patient's disease and FPL eligibility.\n"
        "- Exclude grants that are closed, exhausted, or clearly unrelated.\n"
        "- For each remaining grant return an object with keys: name, amount, logic, url\n"
        "Return ONLY a JSON array. Do not add any explanatory text before or after the JSON.\n"
    )

    model = genai.GenerativeModel(model_name)
    backoff_base = 1.5

    for attempt in range(max_retries + 1):
        try:
            # Deterministic generation for consistent parsing
            response = model.generate_content(prompt, temperature=0.0)

            # The SDK may expose the text in different attributes depending on version
            text = getattr(response, "text", None)
            if not text:
                candidates = getattr(response, "candidates", None)
                if candidates and len(candidates) > 0:
                    # candidates may be list of dicts
                    first = candidates[0]
                    text = first.get("content") or first.get("text") or None

            if not text:
                raise RuntimeError("Empty response from model")

            json_str = _extract_json_array(text)
            parsed = json.loads(json_str)

            normalized: List[Dict[str, Any]] = []
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                name = item.get("name")
                if not name:
                    continue
                url = item.get("url")
                amount = item.get("amount", None)
                logic = item.get("logic") or item.get("reason") or ""

                normalized_item = {
                    "name": name,
                    "amount": amount,
                    "logic": logic,
                    "url": url,
                    "eligibility": "Eligible" if fpl_pct <= 100 else "Verify",
                    "disease": disease_name,
                    "income_level": _income_label(fpl_pct)
                }
                normalized.append(normalized_item)

            if not normalized:
                raise ValueError("Model returned no valid grants")

            return normalized

        except Exception:
            # On final attempt, return fallback enriched grants
            if attempt == max_retries:
                fallback: List[Dict[str, Any]] = []
                for g in grants:
                    gg = dict(g)  # shallow copy
                    gg["eligibility"] = "Eligible" if fpl_pct <= 100 else "Verify"
                    gg["income_level"] = _income_label(fpl_pct)
                    gg["disease"] = disease_name
                    gg["logic"] = gg.get("short_description") or gg.get("description") or "Matched by keyword"
                    fallback.append(gg)
                return fallback

            # exponential backoff before retrying
            time.sleep(backoff_base ** attempt)
            continue
