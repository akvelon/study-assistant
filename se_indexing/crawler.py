import json
from argparse import ArgumentParser
from posixpath import normpath
from urllib.parse import urljoin, urlparse
from uuid import uuid4
import re

import requests
from bs4 import BeautifulSoup


def url_remove_past_path(url: str) -> str:
    return urlparse(url)._replace(params="", query="", fragment="").geturl()


def url_normalize(url: str) -> str:
    url = url_remove_past_path(url)
    # Use Posix paths to normalize cases like example/ and example paths to example/
    url_path_norm: str = normpath(urlparse(url).path)
    return urljoin(url, url_path_norm)


def is_header_or_footer(tag):
    return tag.name == "header" or tag.name == "footer"


def find_canonical_link(soup: BeautifulSoup) -> str | None:
    # Find rel="canonical" tag
    canonical_tag = soup.find(attrs={"rel": "canonical"})
    # Return canonical link if exists
    if canonical_tag is not None:
        return canonical_tag.get("href")
    return None


def extract_metadata(soup: BeautifulSoup) -> list[dict[str, str]] | None:
    # Find all meta tags in document
    all_meta_tags = soup.find_all("meta")
    if all_meta_tags is None:
        return None
    # Include any meta tags that exist
    metadata: list[dict[str, str]] = [
        {str(tag.get("name")): str(tag.get("content"))}
        for tag in all_meta_tags
        # Only include meta tags with name attribute (not charset, http-equiv, etc.)
        if tag.get("name") is not None
    ]
    return metadata


def find_main_content(soup: BeautifulSoup) -> list[BeautifulSoup]:
    """There are 4 cases: <main> tag, "main" id tag, "Skip to main content" link, or fallback to <body> tag."""

    # Attempt to find <main> tag
    main_content = soup.find("main")
    if main_content:
        return main_content.find_all()

    # Attempt to find "main" id tag
    main_content = soup.find(id="main")
    if main_content:
        return main_content.find_all()

    # Attempt to match "Skip to main content" links
    pattern = r"skip.*main\scontent"
    skip_link = soup.find(string=re.compile(pattern, re.IGNORECASE))
    if skip_link:
        # Get id of main content
        id = skip_link.parent.get("href")
        # Exclude leading #
        main_content = soup.find(id=id[1:])
        # Return main content and all next siblings (if any)
        return main_content.find_all(recursive=False) + main_content.find_next_siblings()

    # Fall back to <body> tag
    return soup.body.find_all()


def extract_main_content(tags: list[BeautifulSoup]) -> list[BeautifulSoup]:
    # Extract text from all tags
    elements = []
    for tag in tags:
        elements += tag.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "dl"]
        )
    return elements


def extract_image_metadata(
    tags: list[BeautifulSoup], base_url: str
) -> list[dict[str, str | None]]:
    image_metadata: list[dict[str, str | None]] = []
    for tag in tags:
        if images := tag.find_all("img"):
            for image in images:
                image_metadata.append(
                    {
                        "src": urljoin(base_url, image.get("src")),
                        "alt": image.get("alt"),
                    }
                )
    return image_metadata


def remove_duplicate_eol(text: str) -> str:
    # Match consecutive EOL lines (and any whitespace padding)
    pattern = r"(\s*\n\s*){1,}"
    replacement = "\n"

    # Use regex to substitute pattern with replacement
    cleaned_text = re.sub(pattern, replacement, text)

    return cleaned_text


def extract_urls(soup: BeautifulSoup) -> list[str]:
    # Extract href meta from all <a> tags
    urls: list[str] = [
        url.get("href") for url in soup.find_all("a") if url.get("href") is not None
    ]
    # Remove params, queries, and fragments
    urls = [url_normalize(url) for url in urls]

    return urls


def remove_outside_urls(urls: list[str], base_url: str) -> list[str]:
    base_netloc = urlparse(base_url).netloc
    urls = [url for url in urls if urlparse(url).netloc == base_netloc]
    return urls


def join_relative_urls(urls: list[str], base_url: str) -> list[str]:
    urls = [urljoin(base_url, url) for url in urls]
    return urls


def jsonify_document(
    url: str,
    title: str,
    metadata: list[dict[str, str]] | None,
    image_metadata: list[dict[str, str | None]],
    plain_text: str,
) -> str:
    document_data = {
        "url": url,
        "title": title,
        "type": "school",
        "metadata": metadata,
        "image_metadata": image_metadata,
        "content": plain_text,
    }
    json_data = json.dumps(
        document_data,
        indent=4,
    )
    return json_data


class Crawler:
    def __init__(self):
        self.webpage_url: str | None = None
        self.max_depth: int = 5
        self.curr_depth: int = 1
        self.visited_urls: set[str] = set()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        self.timeout = 5

    def scrape(self, url: str):
        """Recursively scrape webpage extracting canonical link, title, metadata, and plain text."""
        try:
            if self.webpage_url is None:
                self.webpage_url = url

            webpage_response: requests.Response = requests.get(
                url, headers=self.headers, timeout=self.timeout
            )
            if webpage_response.status_code != 200:
                return

            webpage_html: str = webpage_response.text
            soup: BeautifulSoup = BeautifulSoup(webpage_html, "html.parser")

            # Use response url in case of redirect
            document_url: str = url_normalize(webpage_response.url)
            # Prefer canonical link
            if (canonical_link := find_canonical_link(soup)) is not None:
                document_url = urljoin(self.webpage_url, canonical_link)

            # Due to redirects/canonical links we check for duplicates here
            if document_url in self.visited_urls:
                return
            # Add original url to avoid future duplicate redirect links
            self.visited_urls.add(url)
            self.visited_urls.add(document_url)
            # TODO: Replace with logging
            print("Crawling:", document_url)

            # Failure to get title means non-html document
            if soup.title is None:
                return
            document_title: str = soup.title.string

            # Extract metadata
            document_metadata: list[dict[str, str]] | None = extract_metadata(soup)

            # Remove header and footer from document
            for tag in soup.find_all(is_header_or_footer):
                tag.decompose()
            # Find where main content starts
            document_main_content: list[BeautifulSoup] = find_main_content(soup)

            # Extract image metadata
            document_image_metadata: list[dict[str, str | None]] = extract_image_metadata(
                document_main_content, document_url
            )

            # Prune non text tags from main content
            document_main_content = extract_main_content(document_main_content)
            # Extract plain text from main content
            document_plain_text: str = "\n".join(
                tag.get_text() for tag in document_main_content
            )
            document_plain_text = remove_duplicate_eol(document_plain_text)

            document_urls: list[str] = extract_urls(soup)
            document_urls = join_relative_urls(document_urls, document_url)
            document_urls = remove_outside_urls(document_urls, self.webpage_url)

            # Recursively visit each url in document_urls
            for url in document_urls:
                # Avoid already visited redirect links and check depth
                if url not in self.visited_urls and self.curr_depth <= self.max_depth:
                    self.curr_depth += 1
                    self.scrape(url)

            # Save document with UID filename
            with open("documents/" + str(uuid4()) + ".json", "w") as d:
                d.write(
                    jsonify_document(
                        document_url,
                        document_title,
                        document_metadata,
                        document_image_metadata,
                        document_plain_text,
                    )
                )
        except Exception as e:
            # Currently, only way to fail is for webpage to be unreachable.
            # Or, requests exceeds maximum amount of redirects, which is
            # is outside of our control and sign of bad document anyways.
            print(e)
        finally:
            self.curr_depth -= 1


def main():
    # Parse command line arguments
    parser = ArgumentParser(
        prog="Webpage crawler",
    )
    parser.add_argument(
        "url", help="Full url of webpage where to begin crawling.", type=str
    )
    args = parser.parse_args()

    # Normalize webpage url
    webpage_url: str = url_normalize(args.url)

    # Crawl webpage
    crawler = Crawler()
    crawler.scrape(webpage_url)

    print(f"Crawling complete.")


if __name__ == "__main__":
    main()
