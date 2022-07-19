"""
Import Reddit data into existing Solr core

Author: Alexandra DeLucia
"""
import pandas as pd
import json
from tqdm import tqdm
import time
import re
import datetime as dt
from argparse import ArgumentParser
import logging
from solr_utils import SolrHelper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

#############
# Settings
#############
with open("reddit_object_datatypes.json") as f:
    reddit_data_types = json.load(f)

################
# Compile regex
################
# matches all posts that were deleted or removed
DELETED_RE = re.compile(r"\[(deleted)|(removed)\]")
# removes zero-width spaces
ZERO_SPACE_RE = re.compile(r"&#x200B;")
# removes plain URLs
URL_RE = re.compile(r"https?:\/\/[\w\.\/\?\=\d&#%_:/-]+")
# removes markdown links
MARKDOWN_URL_RE = re.compile(r"\[([^\]\(\)]+)\]\((\S*)\)")
# removes asterisks used for *emphasis*
MARKDOWN_ASTERISKS_RE = re.compile(r"\*\**\**([^\*]+)\*\**\**")
# removes underscores used for _emphasis_
MARKDOWN_UNDERSCORES_RE = re.compile(r"\_\_*\_*([^\_]+)\_\_*\_*")
# removes ~~strikethroughs~~
MARKDOWN_STRIKE_RE = re.compile(r"~+([^~]+)~+")
# removes >!spoiler tags!<
MARKDOWN_SPOILER_RE = re.compile(r">!([^!<]+)!<")
# removes superscripts
MARKDOWN_CARAT_RE = re.compile(r"\^")
# removes block quotes
MARKDOWN_QUOTE_RE = re.compile(r">")
# removes parentheses
PARENTHESES_RE = re.compile(r"\(|\)")
# removes brackets
BRACKETS_RE = re.compile(r"\[|\]")
# removes slashes
SLASH_RE = re.compile(r"[\\/]")


def clean_text(text):
    """Remove Markdown from text"""
    if DELETED_RE.search(text):
        return []
    text = ZERO_SPACE_RE.sub("", text)
    text = URL_RE.sub(" ", text)
    text = MARKDOWN_URL_RE.sub(r"\1", text)
    text = BRACKETS_RE.sub("", text)
    text = MARKDOWN_ASTERISKS_RE.sub(r"\1 ", text)
    text = MARKDOWN_UNDERSCORES_RE.sub(r"\1 ", text)
    text = MARKDOWN_STRIKE_RE.sub(r"\1 ", text)
    text = MARKDOWN_SPOILER_RE.sub(r"\1 ", text)
    text = MARKDOWN_CARAT_RE.sub("", text)
    text = MARKDOWN_QUOTE_RE.sub("", text)
    text = PARENTHESES_RE.sub("", text)
    text = SLASH_RE.sub("", text)
    return text


def parse_timestamp(timestamp):
    """
    UTC timestamp to Solr-compatible datestring
    YYYY-MM-DDThh:mm:ssZ
    """
    date = dt.datetime.fromtimestamp(timestamp)
    date = date.strftime("%Y-%m-%dT%H:%M:%SZ")
    return date


def construct_permalink(row):
    """
    https://www.reddit.com/r/redditdev/comments/2f2dj9/how_to_construct_the_permalink_for_a_comment/
    """
    # Return full link
    if "permalink" in row:
        return f"https://www.reddit.com{row['permalink']}"
    # Create link
    comment_link_id = row['link_id'].split("_")[-1]
    return f"https://www.reddit.com/comments/{comment_link_id}/x/{row['id']}"


def is_submission(columns):
    """Boolean of whether dataframe contains submissions or comments"""
    return ("selftext" in columns) and ("title" in columns)


def fill_gildings(x):
    """Fix gildings object NaNs"""
    if pd.isna(x):
        return {'gid_1': 0, 'gid_2': 0, 'gid_3': 0}
    return x


##########
# Main
##########
def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--solr-endpoint", required=True,
                        help="URL for Solr. Ex: http://localhost:8983/solr/cersi-reddit")
    parser.add_argument("--reddit-files", nargs="+", required=True,
                        help="List of json.gz files from Retriever/PushShift")
    parser.add_argument("--jsonlines", action="store_true", help="Files are in JSONLines format")
    parser.add_argument("--skip-completed", action="store_true", help="Do not re-index data. Only index new data.")
    parser.add_argument("--debug", action="store_true", help="Display debugging information")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Connect to Solr
    solr = SolrHelper(endpoint=args.solr_endpoint, logger=logger)

    # Skip documents already loaded
    completed_ids = set()
    if args.skip_completed:
        s = time.time()
        completed_ids = set(solr.get_loaded_documents())
        e = time.time()
        logger.debug(f"Retrieved all {len(completed_ids):,} document IDs in {(e-s)/60} minutes")

    # Load data
    num_errors = 0
    for i, input_file in tqdm(enumerate(args.reddit_files), total=len(args.reddit_files), desc="Loading"):
        # Load data
        try:
            df = pd.read_json(
                input_file,
                dtype=reddit_data_types,
                lines=args.jsonlines
            )
            logger.debug(f"{input_file=} {len(df)=}")
        except (OSError, ValueError) as err:
            logger.error(f"Failed reading file {input_file}:\n{err}")
            continue
        if df.empty:
            logger.debug(f"{input_file} is empty. Skipping.")
            continue
        if args.skip_completed:
            # Remove documents that are already done
            df = df[~df.id.isin(completed_ids)]
            if df.empty:
                continue
        # Drop unneeded columns
        df.drop(columns=[c for c in df.columns if c not in reddit_data_types], inplace=True)
        # Conflict with the field "score" and the Solr relevance "score"
        df.rename(columns={"score": "post_score"}, inplace=True)

        # Add submission vs comment field
        df["is_submission"] = is_submission(df.columns)

        # Parse dates
        date_columns = [c for c in df.columns if reddit_data_types.get(c, "") == "datetime64"]
        df.loc[:, date_columns].fillna(0, inplace=True)
        for date_col in date_columns:
            df[date_col] = df[date_col].map(parse_timestamp)

        # Fix NaNs
        integer_columns = [c for c in df.columns if reddit_data_types.get(c, "") == "int"]
        df.loc[:, integer_columns].fillna(0, inplace=True)
        if "gildings" in df.columns:
            df["gildings"] = df["gildings"].map(fill_gildings)

        # Construct permalink
        df["permalink"] = df.apply(construct_permalink, axis="columns")

        # Send to server
        payload = df.to_json(orient="records", lines=True)
        success = solr.send_to_server(payload)
        if not success:
            logger.error(f"Error on file {input_file}. Continuing.")
            # Exit to debug errors
            if args.debug:
                logger.debug(f"Exiting.")
                exit(1)
        if args.debug and i > 5:
            break
