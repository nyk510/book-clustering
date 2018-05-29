# coding: utf-8
"""
write about this python script
"""
from argparse import ArgumentParser

from scraper.bookmeter import run_fetch_logs


def get_arguments():
    parser = ArgumentParser(description="scrape reading log and related books and authors")
    parser.add_argument("-n", "--num-communities", default=1, type=int)
    parser.add_argument("--start", default=1, type=int, help="start community number")
    return parser.parse_args()


if __name__ == '__main__':
    args = get_arguments()
    print(args)
    run_fetch_logs(num_communities=args.num_communities, start=args.start)
