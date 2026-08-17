# Company Brochure Generator

An AI-powered Python agent that researches a company's website and generates a concise Markdown brochure using a **local Ollama LLM**.

## How it works

1. Scrapes the company's landing page.
2. Extracts links from the website.
3. Uses an LLM to identify relevant pages such as About, Careers, and Customers.
4. Scrapes those pages.
5. Uses the collected content to generate a company brochure.

```text
Website → Scraper → LLM (link selection)
                     ↓
              Relevant pages
                     ↓
                 LLM → Brochure
```

## Requirements

* Python 3.10+
* [Ollama](https://ollama.com/)
* `uv`

Start Ollama and download the default model:

```bash
ollama serve
ollama pull qwen2.5-coder:7b
```

Install dependencies:

```bash
uv sync
```

## Usage

Generate a brochure:

```bash
uv run python brochure.py HuggingFace https://huggingface.co
```

Stream the output:

```bash
uv run python brochure.py HuggingFace https://huggingface.co --stream
```

Save the brochure:

```bash
uv run python brochure.py HuggingFace https://huggingface.co -o brochure.md
```

Use another Ollama model:

```bash
uv run python brochure.py HuggingFace https://huggingface.co --model qwen2.5-coder:14b
```

## Tech Stack

* Python
* Ollama
* Qwen
* OpenAI-compatible API
* Requests
* uv

All LLM inference runs locally through Ollama, so no external AI API key is required.
