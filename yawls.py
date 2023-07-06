#!/usr/bin/python

# Author: Kevin Riley - July, 2023
# Requires Python3


import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
import argparse
import validators
import sys

def validate_url(url):
    if not validators.url(url):
        raise ValueError(f"Invalid URL: {url}")
    return url

# Create the parser
parser = argparse.ArgumentParser(description="Scrape a website and create a word list")

# Add the arguments
parser.add_argument('url', type=validate_url, help='The URL to scrape')
parser.add_argument('-min', '--min_length', type=int, default=1, help='The minimum word length')
parser.add_argument('-max', '--max_length', type=int, default=sys.maxsize, help='The maximum word length')
parser.add_argument('-o', '--output', type=str, default='wordlist.txt', help='The output file name')
parser.add_argument('-l', '--limit', type=int, default=50, help='The maximum number of pages to scrape')

# Parse the arguments
args = parser.parse_args()

url = args.url
parsed_url = urlparse(url)
base_url = parsed_url.netloc

# Send a GET request to the URL
response = requests.get(url)

# If the GET request is successful, the status code will be 200
if response.status_code == 200:
    # Get the content of the response
    content = response.content

    # Create a BeautifulSoup object and specify the parser
    soup = BeautifulSoup(content, 'html.parser')

    # Create a set to hold the unique words and links
    unique_words = set()
    links_to_visit = set([url])
    visited_links = set()

    while links_to_visit and len(visited_links) < args.limit:
        current_url = links_to_visit.pop()
        visited_links.add(current_url)

        response = requests.get(current_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Get all the text
        text = soup.get_text()

        # Get all the words in the text
        words = re.findall('\w+', text)

        # Process each word
        for word in words:
            # Filter out words that are too short or too long and add them to the set
            if args.min_length <= len(word) <= args.max_length:
                unique_words.add(word)

        # Find all the links on the page
        for link in soup.find_all('a', href=True):
            new_url = urljoin(url, link['href'])
            parsed_new_url = urlparse(new_url)

            # If the new URL's domain ends with the base URL's domain
            # and it's not in the visited_links set, add it to the links_to_visit set
            if parsed_new_url.netloc.endswith(base_url) and new_url not in visited_links:
                links_to_visit.add(new_url)

    print(f"Found {len(unique_words)} unique words")

    # Write the unique words to the specified output file
    with open(args.output, 'w') as f:
        for word in unique_words:
            f.write(word + '\n')

else:
    print(f"Failed to scrape {url}. Status code: {response.status_code}")
