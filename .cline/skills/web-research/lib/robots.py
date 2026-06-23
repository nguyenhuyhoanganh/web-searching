"""robots.txt checking via the stdlib urllib.robotparser, fetched through lib.http."""
import urllib.robotparser
from urllib.parse import urlparse

from lib import http


def make_checker(robots_text, user_agent="*"):
    """Return a callable allowed(url) -> bool built from robots.txt text."""
    parser = urllib.robotparser.RobotFileParser()
    parser.parse((robots_text or "").splitlines())
    return lambda url: parser.can_fetch(user_agent, url)


def fetch_checker(start_url, user_agent="*"):
    """Fetch <origin>/robots.txt and return allowed(url).

    A missing or unreachable robots.txt means "allow all", matching standard crawler behaviour.
    """
    parsed = urlparse(start_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        text = http.get(robots_url).text
    except Exception:
        return lambda url: True
    return make_checker(text, user_agent)
