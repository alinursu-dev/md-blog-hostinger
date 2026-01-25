# md-blog-hostinger

CLI workflow I use to publish Markdown blog posts to my website at [alinursu.com](https://alinursu.com).

This repo contains:
- `publish_blog.py`: converts Markdown + YAML frontmatter into HTML and publishes it via an HTTP API.
- `generate_blog_api_key.py`: generates a secure API key and a bcrypt hash to store on the server.
- `posts/`: local Markdown drafts/posts (example + template).

## What this does

- Parse a Markdown file with YAML frontmatter
- Convert Markdown → HTML (tables, fenced code blocks, syntax highlighting, etc.)
- Send JSON payloads to a server endpoint (e.g. `https://alinursu.com/api/blog.php`)

## Requirements

- **Python**: 3.10+ (tested on macOS with a virtual environment)
- **A server API endpoint**: `.../api/blog.php` (or similar) that accepts:
  - `POST ?action=create` (requires `X-API-KEY`)
  - `POST ?action=delete&slug=...` (requires `X-API-KEY`)
  - `GET ?action=posts&limit=...` (for listing posts)
- **A MySQL/MariaDB database** backing the API

## Local setup (macOS / zsh)

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create your local config:

```bash
cp env.example .env
```

Then edit `.env` and set your values.

## Configuration (`.env`)

This script derives the blog API URL from your dashboard currency endpoint:

- `DASHBOARD_API_URL=https://your-domain.com/api/currency.php`
- The publisher automatically converts that to `.../api/blog.php`

Supported env vars:
- **`DASHBOARD_API_URL`**: your site API base URL ending in `/currency.php` (used to derive `/blog.php`)
- **`BLOG_API_KEY`**: API key used for blog publishing (recommended)
- **`DASHBOARD_API_KEY`**: fallback if `BLOG_API_KEY` isn’t set

Security note: keep `.env` private (never commit it).

## Writing posts

Posts are Markdown files with YAML frontmatter. Minimal example:

```markdown
---
title: Hello World
slug: hello-world
category: general
tags: [introduction, personal]
excerpt: Short description shown on listing pages.
published: true
date: 2026-01-25
---

# Hello World

Your post content here...
```

Frontmatter fields used by `publish_blog.py`:
- **`title`** (string): defaults to filename if missing
- **`slug`** (string): defaults to a slugified title if missing
- **`category`** (string): defaults to `general`
- **`tags`** (array): defaults to `[]`
- **`featured_image`** (string URL, optional)
- **`excerpt`** (string): defaults to `""`
- **`published`** (bool): defaults to `true`
- **`date`** (date/datetime/string, optional): converted to a JSON-serializable string for the API

## Publishing

Publish a single post:

```bash
python3 publish_blog.py posts/hello-world.md
```

Publish every `.md` file under `posts/`:

```bash
python3 publish_blog.py posts/
```

Publish as a draft (forces `is_published = false`):

```bash
python3 publish_blog.py posts/hello-world.md --draft
```

## Listing & deleting

List posts on the server:

```bash
python3 publish_blog.py --list
```

Delete a post by slug:

```bash
python3 publish_blog.py --delete hello-world
```

## Generating the blog API key (server setup)

Generate a new API key + bcrypt hash:

```bash
python3 generate_blog_api_key.py
```

This prints:
- a `BLOG_API_KEY=...` line for your local `.env`
- an SQL `INSERT` statement to store the hash on the server (phpMyAdmin)

## Database schema (server-side)

Your server API should have (at minimum) tables for blog posts and API keys.
Example schema you can adapt:

```sql
CREATE TABLE blog_posts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  slug VARCHAR(255) NOT NULL UNIQUE,
  title VARCHAR(255) NOT NULL,
  excerpt TEXT NULL,
  content LONGTEXT NOT NULL,
  featured_image VARCHAR(2048) NULL,
  category VARCHAR(100) NOT NULL DEFAULT 'general',
  tags JSON NULL,
  is_published BOOLEAN NOT NULL DEFAULT FALSE,
  published_at DATETIME NULL,
  reading_time INT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE api_keys (
  id INT AUTO_INCREMENT PRIMARY KEY,
  key_name VARCHAR(64) NOT NULL UNIQUE,
  key_hash VARCHAR(255) NOT NULL,
  description TEXT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_used_at DATETIME NULL
);
```

## Troubleshooting

- **`TypeError: Object of type date is not JSON serializable`**
  - Your frontmatter has `date: YYYY-MM-DD` which parses as a Python `date`.
  - `publish_blog.py` already normalizes this to a JSON-safe string; if you see this error, ensure you’re running the latest local script.

- **`Error: server returned non-JSON response`**
  - Usually means your server endpoint returned HTML (e.g. a 500/404/403 page).
  - The script prints HTTP status + a short body snippet to help you debug.

- **HTTP 500 from the API**
  - On Hostinger, this is commonly a backend/PHP error (bad `config.php`, DB connection failure, missing tables, etc.).
  - Check your hosting error logs and verify the API can connect to the DB.

## Notes

- This repo is intentionally focused on the **publishing client** (Python). The server endpoint must exist on your hosting environment.

