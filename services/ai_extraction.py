import json
import re
import threading
from datetime import date, datetime
from typing import Any

import requests
import logging
from django.conf import settings
from django.core.files.base import ContentFile

TOGETHER_ENDPOINT = "https://api.together.xyz/v1/chat/completions"
MAX_RETRIES = 3
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

CV_JSON_TEMPLATE = {
    "profile": {
        "full_name": "",
        "academic_title": "",
        "institution": "",
        "field_of_study": "",
        "tagline": "",
        "bio": "",
        "current_status": "",
        "google_scholar": "",
        "research_gate": "",
        "years_teaching": None,
        "citation_count": None,
        "students_supervised": None,
        "research_interests": "",
    },
    "education": [
        {"degree": "", "field_of_study": "", "institution": "", "start_year": None, "end_year": None, "description": "", "honor": ""}
    ],
    "publications": [
        {"title": "", "description": "", "pdf_link": "", "github_link": "", "publication_date": None}
    ],
    "teaching": [
        {"course_name": "", "description": "", "syllabus_link": "", "semester": ""}
    ],
    "research_interests_entries": [
        {"title": "", "description": "", "tags": ""}
    ],
    "contact_links": [
        {"label": "", "value": "", "url": "", "link_type": ""}
    ],
}

PROMPT_TEMPLATE = """
You are an expert academic portfolio extractor and copywriter. Given the plain text of an academic CV, return a single JSON object with the exact structure and field names shown below. Do not wrap the response in markdown fences, do not include any text outside the JSON object, and do not add comments.

Important requirements:
- Generate a professional academic `bio` for the `profile` section: 2–4 concise sentences written in a polished academic/professional tone. Do NOT copy sentences verbatim from the CV; rephrase and synthesize content from the CV (experience, education, skills, publications). If the CV has no explicit summary, construct the bio from other sections.
- For optional fields (e.g., `research_interests_entries`, `teaching`, `contact_links`), if the CV does not contain an explicit section, attempt to infer reasonable values from other parts of the CV (e.g., infer 3–5 research interest topics from publication titles, work experience, and keywords). If inference is not possible, return empty lists or empty strings as appropriate.
- Preserve the exact JSON structure below. Include all keys. Use empty string "" or null for unavailable scalar fields, and empty arrays for unavailable lists.

Structure:
{{
    "profile": {{
        "full_name": "",
        "academic_title": "",
        "institution": "",
        "field_of_study": "",
        "tagline": "",
        "bio": "",
        "current_status": "",
        "google_scholar": "",
        "research_gate": "",
        "years_teaching": null,
        "citation_count": null,
        "students_supervised": null,
        "research_interests": ""
    }},
    "education": [
        {{"degree": "", "field_of_study": "", "institution": "", "start_year": null, "end_year": null, "description": "", "honor": ""}}
    ],
    "publications": [
        {{"title": "", "description": "", "pdf_link": "", "github_link": "", "publication_date": null}}
    ],
    "teaching": [
        {{"course_name": "", "description": "", "syllabus_link": "", "semester": ""}}
    ],
    "research_interests_entries": [
        {{"title": "", "description": "", "tags": ""}}
    ],
    "contact_links": [
        {{"label": "", "value": "", "url": "", "link_type": ""}}
    ]
}}

CV Text:
 
{cv_text}

Return only the JSON object.

Special handling for education dates:
- If an education entry in the CV mentions only a single year (for example a short certificate or a single-year listing like "2026"), then set both `start_year` and `end_year` to that year in the returned JSON. Do not leave one of them null when a single explicit year is present.

"""



def _call_together(cv_text: str) -> str:
    payload = {
        "model": settings.TOGETHER_MODEL,
        "temperature": 0.1,
        "max_tokens": 8000,
        "messages": [
            {"role": "system", "content": "You are a robust JSON extraction assistant."},
            {"role": "user", "content": PROMPT_TEMPLATE.format(cv_text=cv_text)}
        ],
    }
    headers = {
        "Authorization": f"Bearer {settings.TOGETHER_API_KEY}",
        "Content-Type": "application/json",
    }
    response = requests.post(TOGETHER_ENDPOINT, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content")
    if not isinstance(content, str):
        raise ValueError("No text content returned from Together API")
    return content.strip()


def _strip_non_json(text: str) -> str:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    match = re.search(r"\{.*\}$", text, re.DOTALL)
    if match:
        return match.group(0)

    # Best effort: if the response begins with JSON but was truncated, try to close any missing braces.
    if text.startswith("{"):
        brace_balance = 0
        in_string = False
        escape = False
        for char in text:
            if escape:
                escape = False
                continue
            if char == "\\":
                escape = True
                continue
            if char == '"':
                in_string = not in_string
            if in_string:
                continue
            if char == '{':
                brace_balance += 1
            elif char == '}':
                brace_balance -= 1
        if brace_balance > 0:
            return text + ('}' * brace_balance)
    raise ValueError("Could not extract JSON object from response")


def extract_cv_data(cv_text: str) -> dict[str, Any]:
    last_error = None
    for attempt in range(MAX_RETRIES):
        raw = None
        try:
            raw = _call_together(cv_text)
            json_text = _strip_non_json(raw)
            extracted = json.loads(json_text)
            if not isinstance(extracted, dict):
                raise ValueError("Extracted JSON is not an object")
            return _normalize_extracted_data(extracted)
        except (ValueError, json.JSONDecodeError, requests.RequestException) as exc:
            last_error = exc
            # If the error is failure to strip JSON, log the raw Together response for debugging.
            if isinstance(exc, ValueError) and str(exc).startswith("Could not extract JSON object"):
                try:
                    logger = logging.getLogger(__name__)
                    logger.error("Failed to extract JSON from Together response; response was truncated or malformed.")
                except Exception:
                    pass
            if attempt + 1 < MAX_RETRIES:
                continue
            raise
    raise last_error or RuntimeError("Failed to extract CV data")


def _normalize_extracted_data(extracted: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(json.dumps(CV_JSON_TEMPLATE))

    profile = extracted.get("profile", {}) if isinstance(extracted.get("profile"), dict) else {}
    for key in result["profile"]:
        value = profile.get(key, result["profile"][key])
        if value is None or value == "":
            result["profile"][key] = None if key in ["years_teaching", "citation_count", "students_supervised"] else ""
        else:
            result["profile"][key] = value

    for collection_name in ["education", "publications", "teaching", "research_interests_entries", "contact_links"]:
        extracted_items = extracted.get(collection_name)
        if isinstance(extracted_items, list) and extracted_items:
            normalized_items = []
            for item in extracted_items:
                if not isinstance(item, dict):
                    continue
                normalized = {}
                for template_item_key, template_item_val in result[collection_name][0].items():
                    raw_value = item.get(template_item_key, template_item_val)
                    normalized[template_item_key] = None if raw_value is None else raw_value
                normalized_items.append(normalized)
            if normalized_items:
                result[collection_name] = normalized_items
    return result


def _extract_text_from_pdf(file_obj) -> str:
    try:
        from pypdf import PdfReader
        from pypdf.errors import PdfReadError
    except ImportError as exc:
        raise ImportError("pypdf is required to extract text from PDF files") from exc

    file_obj.seek(0)
    pypdf_error = None
    try:
        reader = PdfReader(file_obj)
        text_parts = []
        for page in reader.pages:
            try:
                text_parts.append(page.extract_text() or "")
            except Exception:
                text_parts.append("")
        extracted_text = "\n\n".join(text_parts).strip()
        if extracted_text:
            return extracted_text
    except PdfReadError as exc:
        pypdf_error = exc
    except Exception as exc:
        pypdf_error = exc

    file_obj.seek(0)
    try:
        import pdfplumber
    except ImportError as exc:
        if pypdf_error is not None:
            raise RuntimeError(
                    "We couldn't read this PDF. It may be corrupted or protected. Try saving it as a new PDF or use a Word document."
                ) from pypdf_error
        raise ImportError("pdfplumber is required as a fallback to extract text from PDF files") from exc

    try:
        with pdfplumber.open(file_obj) as pdf:
            text_parts = []
            for page in pdf.pages:
                try:
                    text_parts.append(page.extract_text() or "")
                except Exception:
                    text_parts.append("")
        extracted_text = "\n\n".join(text_parts).strip()
        if extracted_text:
            return extracted_text
        raise ValueError(
            "This file appears to be a scanned image and does not contain extractable text. Please use a Word document or a text-based PDF."
        )
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(
            "We couldn't read this PDF. It may be corrupted or protected. Try saving it as a new PDF or use a Word document."
        ) from exc


def _extract_text_from_docx(file_obj) -> str:
    try:
        import docx
    except ImportError as exc:
        raise ImportError("python-docx is required to extract text from Word files") from exc
    file_obj.seek(0)
    document = docx.Document(file_obj)
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs).strip()


def extract_text_from_cv_file(file_obj, filename: str, file_size: int | None = None) -> str:
    extension = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
    extension = f".{extension}"
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported file type. Please upload PDF or DOCX.")
    size = file_size if file_size is not None else getattr(file_obj, 'size', None)
    if size is not None and size > MAX_UPLOAD_SIZE:
        raise ValueError("File size exceeds the 10MB limit.")
    if extension == ".pdf":
        return _extract_text_from_pdf(file_obj)
    if extension == ".docx":
        return _extract_text_from_docx(file_obj)
    raise ValueError("Unsupported file type. Please upload PDF or DOCX.")


def _parse_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        digits = re.findall(r"\d+", str(value))
        if digits:
            return int(digits[0])
    return None


def _parse_publication_date(value: Any) -> date | None:
    if value is None:
        return None
    value_text = str(value).strip()
    if not value_text:
        return None
    patterns = ["%Y-%m-%d", "%Y-%m", "%B %Y", "%b %Y", "%Y"]
    for pattern in patterns:
        try:
            parsed = datetime.strptime(value_text, pattern)
            if pattern == "%Y":
                return date(parsed.year, 1, 1)
            return parsed.date()
        except ValueError:
            continue
    year_match = re.search(r"(19|20)\d{2}", value_text)
    if year_match:
        return date(int(year_match.group(0)), 1, 1)
    return None


def _is_valid_contact_type(link_type: Any) -> bool:
    from portfolios.models import ContactLink

    return str(link_type) in {choice[0] for choice in ContactLink.LINK_TYPES}


def save_extracted_data(profile, extracted_json: dict[str, Any]) -> dict[str, Any]:
    profile_data = extracted_json.get("profile", {}) if isinstance(extracted_json.get("profile"), dict) else {}
    string_fields = [
        "full_name", "academic_title", "institution", "field_of_study",
        "tagline", "bio", "current_status", "google_scholar",
        "research_gate", "research_interests",
    ]
    int_fields = ["years_teaching", "citation_count", "students_supervised"]

    for field_name in string_fields:
        value = profile_data.get(field_name)
        if value not in (None, ""):
            setattr(profile, field_name, str(value).strip())

    for field_name in int_fields:
        parsed = _parse_int(profile_data.get(field_name))
        if parsed is not None:
            setattr(profile, field_name, parsed)

    profile.save()

    from portfolios.models import ContactLink, Education, Publication, ResearchInterest, Teaching

    if not profile.education_entries.exists():
        education_to_create = []
        for order_index, item in enumerate(extracted_json.get("education", [])):
            if not isinstance(item, dict):
                continue
            degree = str(item.get("degree", "") or "").strip()
            institution = str(item.get("institution", "") or "").strip()
            if not degree and not institution:
                continue
            education_to_create.append(Education(
                profile=profile,
                degree=degree or "",
                field_of_study=str(item.get("field_of_study", "") or "").strip(),
                institution=institution or "",
                start_year=_parse_int(item.get("start_year")) or datetime.now().year,
                end_year=_parse_int(item.get("end_year")),
                description=str(item.get("description", "") or "").strip(),
                honor=str(item.get("honor", "") or "").strip(),
                order_index=order_index,
            ))
        if education_to_create:
            Education.objects.bulk_create(education_to_create)

    if not profile.publications.exists():
        publication_to_create = []
        for item in extracted_json.get("publications", []):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "") or "").strip()
            if not title:
                continue
            publication_to_create.append(Publication(
                profile=profile,
                title=title,
                description=str(item.get("description", "") or "").strip(),
                pdf_link=str(item.get("pdf_link", "") or "").strip(),
                github_link=str(item.get("github_link", "") or "").strip(),
                publication_date=_parse_publication_date(item.get("publication_date")),
            ))
        if publication_to_create:
            Publication.objects.bulk_create(publication_to_create)

    if not profile.teachings.exists():
        teaching_to_create = []
        for item in extracted_json.get("teaching", []):
            if not isinstance(item, dict):
                continue
            course_name = str(item.get("course_name", "") or "").strip()
            if not course_name:
                continue
            teaching_to_create.append(Teaching(
                profile=profile,
                course_name=course_name,
                description=str(item.get("description", "") or "").strip(),
                syllabus_link=str(item.get("syllabus_link", "") or "").strip(),
                semester=str(item.get("semester", "") or "").strip(),
            ))
        if teaching_to_create:
            Teaching.objects.bulk_create(teaching_to_create)

    if not profile.research_interests_entries.exists():
        ri_to_create = []
        for item in extracted_json.get("research_interests_entries", []):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "") or "").strip()
            if not title:
                continue
            ri_to_create.append(ResearchInterest(
                profile=profile,
                title=title,
                description=str(item.get("description", "") or "").strip(),
                tags=str(item.get("tags", "") or "").strip(),
                order_index=len(ri_to_create),
            ))
        if ri_to_create:
            ResearchInterest.objects.bulk_create(ri_to_create)

    if not profile.contact_links.exists():
        contact_to_create = []
        for item in extracted_json.get("contact_links", []):
            if not isinstance(item, dict):
                continue
            label = str(item.get("label", "") or "").strip()
            value = str(item.get("value", "") or "").strip()
            if not label and not value:
                continue
            link_type = str(item.get("link_type", "") or "").strip()
            if not _is_valid_contact_type(link_type):
                link_type = "link"
            contact_to_create.append(ContactLink(
                profile=profile,
                label=label or "Contact",
                value=value or "",
                url=str(item.get("url", "") or "").strip(),
                link_type=link_type,
                order_index=len(contact_to_create),
            ))
        if contact_to_create:
            ContactLink.objects.bulk_create(contact_to_create)

    return extracted_json
