#!/usr/bin/python

# Author: Kevin Riley - July, 2023
# Requires Python3

import requests
import string
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
import argparse
import validators
import sys
from collections import deque

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
parser.add_argument('-l', '--limit', type=int, default=3, help='The maximum number of levels to follow')
parser.add_argument('-v', '--verbose', action='store_true', help='Print out each link being followed')
parser.add_argument('-e', '--email', action='store_true', help='Discover and parse email addresses found on the web pages')

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

    # Create a set to hold the unique words and a queue for links to visit
    unique_words = set()
    links_to_visit = deque([(url, 0)])  # each item is a tuple (url, depth)
    visited_links = set()

    while links_to_visit:
        current_url, depth = links_to_visit.popleft()
        visited_links.add(current_url)

        if args.verbose:
            print(f"Following link: {current_url}")

        if depth > args.limit: 
            continue

        response = requests.get(current_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        if args.email:
        # Find all email addresses on the page
            email_addresses = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)

        # Write the email addresses to a separate file
            with open('emails.txt', 'a', encoding='utf-8') as f:
                for email in email_addresses:
                    f.write(email + '\n')
               
         # Get all the text
         text = soup.get_text()

        # Get all the words in the text
        words = re.findall('\w+', text)

        # Process each word
        for word in words:
            # Filter out words that are too short, too long, or contain non-ASCII characters and add them to the set
            if args.min_length <= len(word) <= args.max_length and all(char in string.ascii_letters for char in word):
                unique_words.add(word)

        # Find all the links on the page
        for link in soup.find_all('a', href=True):
            new_url = urljoin(url, link['href'])
            parsed_new_url = urlparse(new_url)

            # If the new URL's domain ends with the base URL's domain
            # and it's not in the visited_links set, add it to the links_to_visit set
            if parsed_new_url.netloc.endswith(base_url) and new_url not in visited_links:
                links_to_visit.append((new_url, depth + 1))

    print(f"Found {len(unique_words)} unique words")

    # sort the unique words by length (descending) and then alphabetically
    sorted_words = sorted(unique_words, key=lambda word: (-len(word), word), reverse=True)

    # Write the sorted words to the specified output file
    with open(args.output, 'w', encoding='utf-8') as f:
        for word in sorted_words:
            try:
             # try encoding and decoding the word
                word.encode('utf-8').decode('utf-8')
                f.write(word + '\n')
            except UnicodeError:
                print(f"Skipping word: {word} - Cannot be encoded or decoded")

else:
    print(f"Failed to scrape {url}. Status code: {response.status_code}")
