import csv
import logging

from config import CUSTOMERS_CSV
from gemini_service import generate_text

logger = logging.getLogger(__name__)


def load_customers() -> list[dict[str, str]]:
    with CUSTOMERS_CSV.open(newline="", encoding="utf-8") as csvfile:
        return list(csv.DictReader(csvfile))


def generate_subject_line() -> str:
    return generate_text(
        "Write exactly one catchy marketing email subject line. "
        "Do not include the customer's name. Do not explain. "
        "Output only the subject line in plain text."
    )


def generate_email_body(name: str) -> str:
    return generate_text(
        f"Write a short, friendly marketing email body for {name}. "
        "Keep it under 120 words. Include a greeting, one key offer, "
        "and a clear call to action. Do not include the subject line. "
        "Output plain text only."
    )


def generate_bulk_subject_lines() -> list[dict[str, str]]:
    results = []
    for row in load_customers():
        name = row.get("name", "Customer")
        results.append({"name": name, "subject_line": generate_subject_line()})
    logger.info("Generated %s subject lines", len(results))
    return results


def generate_bulk_email_bodies() -> list[dict[str, str]]:
    results = []
    for row in load_customers():
        name = row.get("name", "Customer")
        email = row.get("email", "")
        results.append({"name": name, "email": email, "body": generate_email_body(name)})
    logger.info("Generated %s email bodies", len(results))
    return results


def generate_full_campaign() -> list[dict[str, str]]:
    results = []
    for row in load_customers():
        name = row.get("name", "Customer")
        email = row.get("email", "")
        results.append(
            {
                "name": name,
                "email": email,
                "subject_line": generate_subject_line(),
                "body": generate_email_body(name),
            }
        )
    logger.info("Generated campaign for %s customers", len(results))
    return results

