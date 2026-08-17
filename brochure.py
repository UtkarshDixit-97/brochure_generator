"""
Company brochure generator
Uses local Ollama (OpenAI-compatible API) to pick relevant site links and
write a markdown brochure from scraped page content.

Prerequisites:
  ollama serve
  ollama pull qwen2.5-coder:7b   # or pass --model

Usage:
  uv run python brochure.py HuggingFace https://huggingface.co
  uv run python brochure.py HuggingFace https://huggingface.co --stream
  uv run python brochure.py HuggingFace https://huggingface.co -o brochure.md
"""

import argparse
import json
import sys

import requests
from openai import OpenAI

from scraper import fetch_website_contents, fetch_website_links

OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"
DEFAULT_MODEL = "qwen2.5-coder:7b"

LINK_SYSTEM_PROMPT = """
You are provided with a list of links found on a webpage.
You are able to decide which of the links would be most relevant to include in a brochure about the company,
such as links to an About page, or a Company page, or Careers/Jobs pages.
You should respond in JSON as in this example:

{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page", "url": "https://another.full.url/careers"}
    ]
}
"""

BROCHURE_SYSTEM_PROMPT = """
You are an assistant that analyzes the contents of several relevant pages from a company website
and creates a short brochure about the company for prospective customers, investors and recruits.
Respond in markdown without code blocks.
Include details of company culture, customers and careers/jobs if you have the information.
"""


def check_ollama():
    ping = requests.get("http://127.0.0.1:11434", timeout=5)
    ping.raise_for_status()
    print(f"Ollama is running: {ping.text.strip()}")


def get_links_user_prompt(url):
    user_prompt = f"""
Here is the list of links on the website {url} -
Please decide which of these are relevant web links for a brochure about the company,
respond with the full https URL in JSON format.
Do not include Terms of Service, Privacy, email links.

Links (some might be relative links):

"""
    links = fetch_website_links(url)
    user_prompt += "\n".join(links)
    return user_prompt


def select_relevant_links(client, model, url):
    print(f"Selecting relevant links for {url} using {model}")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": LINK_SYSTEM_PROMPT},
            {"role": "user", "content": get_links_user_prompt(url)},
        ],
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content)
    print(f"Found {len(result['links'])} relevant links")
    return result


def fetch_page_and_all_relevant_links(client, model, url):
    contents = fetch_website_contents(url)
    relevant_links = select_relevant_links(client, model, url)
    result = f"## Landing Page:\n\n{contents}\n## Relevant Links:\n"
    for link in relevant_links["links"]:
        link_url = (link.get("url") or "").strip()
        if not link_url or not link_url.startswith("http"):
            continue
        try:
            page_text = fetch_website_contents(link_url)
        except requests.RequestException as e:
            print(f"Skipping {link_url}: {e}")
            continue
        result += f"\n\n### Link: {link['type']}\n"
        result += page_text
    return result


def get_brochure_user_prompt(client, model, company_name, url):
    user_prompt = f"""
You are looking at a company called: {company_name}
Here are the contents of its landing page and other relevant pages;
use this information to build a short brochure of the company in markdown without code blocks.\n\n
"""
    user_prompt += fetch_page_and_all_relevant_links(client, model, url)
    return user_prompt[:5_000]


def create_brochure(client, model, company_name, url):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": BROCHURE_SYSTEM_PROMPT},
            {"role": "user", "content": get_brochure_user_prompt(client, model, company_name, url)},
        ],
    )
    return response.choices[0].message.content


def stream_brochure(client, model, company_name, url):
    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": BROCHURE_SYSTEM_PROMPT},
            {"role": "user", "content": get_brochure_user_prompt(client, model, company_name, url)},
        ],
        stream=True,
    )
    response = ""
    for chunk in stream:
        text = chunk.choices[0].delta.content or ""
        response += text
        print(text, end="", flush=True)
    print()
    return response


def main():
    parser = argparse.ArgumentParser(description="Generate a company brochure from a website using local Ollama.")
    parser.add_argument("company", help="Company name (e.g. HuggingFace)")
    parser.add_argument("url", help="Company website URL (e.g. https://huggingface.co)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model (default: {DEFAULT_MODEL})")
    parser.add_argument("--stream", action="store_true", help="Stream brochure text to the terminal")
    parser.add_argument("-o", "--output", help="Write brochure markdown to this file")
    args = parser.parse_args()

    try:
        check_ollama()
    except requests.RequestException as e:
        print("Ollama is not reachable. Start it with: ollama serve")
        print(e)
        sys.exit(1)

    print(f"Using model: {args.model}")
    client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")

    if args.stream:
        print("\n--- Brochure (streaming) ---\n")
        brochure = stream_brochure(client, args.model, args.company, args.url)
    else:
        print("\nGenerating brochure...\n")
        brochure = create_brochure(client, args.model, args.company, args.url)
        print(brochure)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(brochure)
        print(f"\nWritten to {args.output}")


if __name__ == "__main__":
    main()
