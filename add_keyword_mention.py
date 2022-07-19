"""
Use the Solr API to add keyword mentions to a document
Should be faster than regular expressions

Note: keyword-field and contains-keywords-field should be created in
the schema before running this script

Author: Alexandra DeLucia
"""
from tqdm import tqdm
import logging
from argparse import ArgumentParser
from solr_utils import SolrHelper


##########
# Settings
##########
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

CHECK_FIELDS = ["title", "body", "selftext"]


def update_doc(document, keyword, keywords_field, contains_keywords_field, number_of_keywords_field, remove=False):
    new_doc = {}
    if remove:
        doc_keywords = document.get(keywords_field, [])
        if keyword in doc_keywords:
            new_doc[keywords_field] = {"remove": keyword}
            # Update number of keywords in document
            new_doc[number_of_keywords_field] = {"set": len(doc_keywords) - 1}
            # Check if keywords are left
            if new_doc[number_of_keywords_field] == 0:
                new_doc[contains_keywords_field] = {"set": False}
    else:
        if keyword not in document.get(keywords_field, []):
            new_doc[keywords_field] = {"add": keyword}
        if not document.get(contains_keywords_field):
            new_doc[contains_keywords_field] = {"set": True}
        new_doc[number_of_keywords_field] = {"set": len(document.get(keywords_field, [])) + 1}
    if len(new_doc) != 0:
        new_doc["id"] = document["id"]
    return new_doc


##########
# Main
##########
def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--solr-endpoint", required=True, help="URL for Solr. Ex: http://localhost:8983/solr/cersi-reddit")
    parser.add_argument("--keywords-file", required=True, help="Path to newline-separated list of keywords to query")
    parser.add_argument("--keywords-field", required=True, help="Solr fieldname to store the found keywords")
    parser.add_argument("--contains-keywords-field", required=True, help="Solr fieldname to store the boolean that a keyword was found")
    parser.add_argument("--number-of-keywords-field", required=True, help="Solr fieldname to store the number of keywords in the document")
    parser.add_argument("--num-rows", default=10, type=int, help="Number of rows to return per query")
    parser.add_argument("--num-processes", default=2, type=int, help="Number of processes for multiprocessing")
    parser.add_argument("--clear-fields", action="store_true",
                        help="Clear values in provided fields before updating them")
    parser.add_argument("--remove-keywords", action="store_true",
                        help="Remove --keywords-file words from --keywords-field and update "
                             "--contains-keywords-field accordingly")
    parser.add_argument("--fields", nargs="+",
                        help=f"Fields to check for keyword presence. Default is {CHECK_FIELDS}.")
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if not args.fields:
        args.fields = CHECK_FIELDS
    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Connect to Solr
    solr = SolrHelper(endpoint=args.solr_endpoint, logger=logger)

    if args.clear_fields:
        logger.info(f"Clearing fields '{args.keywords_field}' and '{args.contains_keywords_field}'")
        for document_ids in tqdm(solr.get_loaded_documents(num_rows=100000), total=226):  # estimate
            updated_docs = []
            for doc_id in document_ids:
                new_doc = {
                    "id": doc_id,
                    args.keywords_field: {"set": []},
                    args.contains_keywords_field: {"set": False},
                }
                updated_docs.append(new_doc)
            # Send to server in batches
            for batch in solr.split_every(10000, updated_docs):
                success = solr.send_to_server(batch, atomic_update=True)
                if not success:
                    logger.error(f"Error with payload. Check Solr logs at http://localhost:8983/solr/#/~logging")
                    exit(1)

    # Load keywords
    with open(args.keywords_file) as f:
        keywords_list = [i.strip().lower() for i in f.readlines()]
    keywords_list.sort()
    logger.info(f"Loaded {len(keywords_list):,} keywords")

    if args.remove_keywords:
        for keyword in tqdm(keywords_list, desc="Keyword"):
            query = {
                "params": {
                    "q": "*:*",
                    "fq": [f"{args.keywords_field}:{keyword}", f"{args.contains_keywords_field}:true"],
                    "rows": args.num_rows
                }
            }
            response = solr.query_server(query)
            res = response.get("response")
            num_found = int(res["numFound"])
            params = response.get("responseHeader", {}).get("params")
            logger.info(f"{keyword} {num_found} {params}")
            if num_found == 0:
                continue

            updated_docs = []
            for doc in res["docs"]:
                d = update_doc(doc, keyword, args.keywords_field, args.contains_keywords_field, args.number_of_keywords_field, remove=True)
                if d:
                    updated_docs.append(d)

            # Send to server in batches
            for batch in solr.split_every(100, updated_docs):
                success = solr.send_to_server(batch, atomic_update=True)
                if not success:
                    logger.error(f"Error with payload. Check Solr logs at http://localhost:8983/solr/#/~logging")
                    exit(1)
        solr.force_commit()
        exit(0)

    # For each keyword
    max_found = 0
    for keyword in tqdm(keywords_list, desc="Keyword"):
        # Query the posts with the keyword
        # use quotes to keep phrases in order
        query = {
            "params": {
                "defType": "edismax",
                "q.op": "AND",
                "q": keyword if len(keyword.split()) == 1 else f"\"{keyword}\"",
                "qf": " ".join(args.fields),
                "fl": ["id", args.keywords_field, args.contains_keywords_field, args.number_of_keywords_field],
                "rows": args.num_rows,
                "mm": 100
            }
        }
        response = solr.query_server(query)
        params = response.get("responseHeader", {}).get("params")
        res = response.get("response")

        # Check empty
        num_found = int(res["numFound"])
        logger.debug(f"{keyword}\t{params}\t{num_found:,}")
        if num_found == 0:
            logger.warning(f"No posts found for {keyword}")
            continue
        if num_found > args.num_rows:
            logger.warning(f"Keyword '{keyword}' has {num_found:,} entries but only {args.num_rows:,} were returned")
        if num_found > max_found:
            max_found = num_found
        logger.debug(f"Example post: {res['docs'][0]['id']}")

        # Only update the entries that need updating
        updated_docs = []
        for doc in res["docs"]:
            d = update_doc(doc, keyword, args.keywords_field, args.contains_keywords_field, args.number_of_keywords_field)
            if d:
                updated_docs.append(d)

        # Send to server in batches
        for batch in solr.split_every(100, updated_docs):
            success = solr.send_to_server(batch, atomic_update=True)
            if not success:
                logger.error(f"Error with payload. Check Solr logs at http://localhost:8983/solr/#/~logging")
                exit(1)

        if args.debug:
            break

    logger.debug(max_found)
