#!/usr/bin/env python3
"""
Blog Publisher Script

Converts markdown files to HTML and pushes them to the Hostinger API.

Usage:
    python publish_blog.py posts/my-article.md           # Publish single post
    python publish_blog.py posts/                        # Publish all posts in folder
    python publish_blog.py posts/my-article.md --draft   # Save as draft (not published)
    python publish_blog.py --list                        # List all posts on server

Markdown files should have YAML frontmatter:
    ---
    title: My Article Title
    slug: my-article-title
    category: python
    tags: [python, tutorial, beginner]
    featured_image: https://example.com/image.jpg
    excerpt: A brief description of the article
    published: true
    ---

    # Article content here...
"""

import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, date

import requests
import frontmatter
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.toc import TocExtension
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_URL = os.getenv('DASHBOARD_API_URL', '').replace('/currency.php', '/blog.php')
API_KEY = os.getenv('BLOG_API_KEY', os.getenv('DASHBOARD_API_KEY', ''))

# Markdown extensions for nice rendering
MD_EXTENSIONS = [
    'extra',
    'smarty',
    FencedCodeExtension(),
    CodeHiliteExtension(css_class='highlight', guess_lang=True),
    TableExtension(),
    TocExtension(permalink=True),
    'nl2br',
]


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text


def parse_markdown_file(filepath: Path) -> dict:
    """Parse a markdown file with frontmatter into post data."""
    post = frontmatter.load(filepath)

    # Convert markdown content to HTML
    md = markdown.Markdown(extensions=MD_EXTENSIONS)
    html_content = md.convert(post.content)

    # Extract metadata with defaults
    metadata = post.metadata

    title = metadata.get('title', filepath.stem.replace('-', ' ').title())
    slug = metadata.get('slug', slugify(title))

    def _format_published_at(value) -> str:
        """
        Ensure published_at is JSON-serializable.
        YAML frontmatter dates may be parsed as datetime/date objects.
        """
        if isinstance(value, datetime):
            return value.isoformat(sep=' ', timespec='seconds')
        if isinstance(value, date):
            return value.isoformat()
        if value is None or value == '':
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return str(value)

    return {
        'slug': slug,
        'title': title,
        'content': html_content,
        'excerpt': metadata.get('excerpt', ''),
        'category': metadata.get('category', 'general'),
        'tags': metadata.get('tags', []),
        'featured_image': metadata.get('featured_image'),
        'is_published': metadata.get('published', True),
        'published_at': _format_published_at(metadata.get('date')),
    }


def publish_post(post_data: dict, draft: bool = False) -> bool:
    """Push post data to the API."""
    if not API_URL or not API_KEY:
        print("Error: API_URL and BLOG_API_KEY (or DASHBOARD_API_KEY) must be set in .env")
        return False

    if draft:
        post_data['is_published'] = False

    try:
        response = requests.post(
            f"{API_URL}?action=create",
            json=post_data,
            headers={
                'Content-Type': 'application/json',
                'X-API-KEY': API_KEY,
            },
            timeout=30,
        )
    except requests.RequestException as e:
        print(f"✗ Network error: {e}")
        return False

    try:
        result = response.json()
    except ValueError:
        body = (response.text or '').strip()
        snippet = body[:800]
        print(f"✗ Invalid response while publishing: {post_data['title']}")
        print(f"  HTTP: {response.status_code} {response.reason}")
        print(f"  URL: {response.url}")
        print(f"  Content-Type: {response.headers.get('Content-Type', '')}")
        print(f"  Body: {snippet if snippet else '<empty response>'}")
        return False

    if response.status_code == 200 and result.get('success'):
        status = "draft" if draft or not post_data.get('is_published') else "published"
        print(f"✓ {status.capitalize()}: {post_data['title']} ({post_data['slug']})")
        return True

    print(f"✗ Failed: {post_data['title']}")
    print(f"  HTTP: {response.status_code} {response.reason}")
    print(f"  Error: {result.get('error', 'Unknown error')}")
    return False


def delete_post(slug: str) -> bool:
    """Delete a post by slug."""
    if not API_URL or not API_KEY:
        print("Error: API_URL and BLOG_API_KEY must be set in .env")
        return False

    try:
        response = requests.post(
            f"{API_URL}?action=delete&slug={slug}",
            headers={'X-API-KEY': API_KEY},
            timeout=30,
        )
    except requests.RequestException as e:
        print(f"✗ Network error: {e}")
        return False

    try:
        result = response.json()
    except ValueError:
        body = (response.text or '').strip()
        snippet = body[:800]
        print(f"✗ Invalid response while deleting: {slug}")
        print(f"  HTTP: {response.status_code} {response.reason}")
        print(f"  URL: {response.url}")
        print(f"  Content-Type: {response.headers.get('Content-Type', '')}")
        print(f"  Body: {snippet if snippet else '<empty response>'}")
        return False

    if response.status_code == 200 and result.get('success'):
        print(f"✓ Deleted: {slug}")
        return True

    print(f"✗ Failed to delete: {slug}")
    print(f"  HTTP: {response.status_code} {response.reason}")
    print(f"  Error: {result.get('error', 'Unknown error')}")
    return False


def list_posts() -> None:
    """List all posts on the server."""
    if not API_URL:
        print("Error: API_URL must be set in .env")
        return

    try:
        response = requests.get(
            f"{API_URL}?action=posts&limit=100",
            timeout=30,
        )
    except requests.RequestException as e:
        print(f"Network error: {e}")
        return

    try:
        result = response.json()
    except ValueError:
        body = (response.text or '').strip()
        snippet = body[:800]
        print("Error: server returned non-JSON response")
        print(f"HTTP: {response.status_code} {response.reason}")
        print(f"URL: {response.url}")
        print(f"Content-Type: {response.headers.get('Content-Type', '')}")
        print(f"Body: {snippet if snippet else '<empty response>'}")
        return

        if 'posts' in result:
            posts = result['posts']
            if not posts:
                print("No posts found.")
                return

            print(f"\n{'SLUG':<40} {'TITLE':<40} {'CATEGORY':<15} {'DATE'}")
            print("-" * 110)

            for post in posts:
                date = post.get('published_at', '')[:10] if post.get('published_at') else 'Draft'
                print(f"{post['slug']:<40} {post['title'][:38]:<40} {post['category']:<15} {date}")

            print(f"\nTotal: {len(posts)} posts")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")


def process_path(path: Path, draft: bool = False) -> tuple[int, int]:
    """Process a file or directory of markdown files."""
    success = 0
    failed = 0

    if path.is_file():
        if path.suffix.lower() in ['.md', '.markdown']:
            post_data = parse_markdown_file(path)
            if publish_post(post_data, draft):
                success += 1
            else:
                failed += 1
        else:
            print(f"Skipping non-markdown file: {path}")

    elif path.is_dir():
        for md_file in sorted(path.glob('**/*.md')):
            post_data = parse_markdown_file(md_file)
            if publish_post(post_data, draft):
                success += 1
            else:
                failed += 1

    return success, failed


def main():
    parser = argparse.ArgumentParser(
        description='Publish markdown blog posts to Hostinger',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        'path',
        nargs='?',
        help='Markdown file or directory to publish',
    )

    parser.add_argument(
        '--draft',
        action='store_true',
        help='Save as draft (not published)',
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List all posts on server',
    )

    parser.add_argument(
        '--delete',
        metavar='SLUG',
        help='Delete a post by slug',
    )

    args = parser.parse_args()

    # List posts
    if args.list:
        list_posts()
        return

    # Delete post
    if args.delete:
        delete_post(args.delete)
        return

    # Publish post(s)
    if not args.path:
        parser.print_help()
        return

    path = Path(args.path)

    if not path.exists():
        print(f"Error: Path not found: {path}")
        sys.exit(1)

    print(f"Publishing {'draft' if args.draft else 'post'}(s) from: {path}\n")

    success, failed = process_path(path, args.draft)

    print(f"\nResults: {success} published, {failed} failed")

    if failed > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
