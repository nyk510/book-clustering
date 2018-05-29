# coding: utf-8
"""
book meter から読書記録をスクレイピングするモジュール
"""

import json
import os
from collections import namedtuple

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from joblib import Parallel, delayed
from tqdm import tqdm
from time import sleep
from .settings import OUTPUT_DIR
from .utils import get_logger

__author__ = "nyk510"

BASE_URL = "https://bookmeter.com"
logger = get_logger(__name__)

reading_log_record = namedtuple("reading_log", ("book_id", "author_id", "read_date", "user_id"))
book_record = namedtuple("book", ("id", "title"))
author_record = namedtuple("author", ("id", "name"))


def get_max_pages(soup):
    """
    ページネーションがあるページのdomからページめくりの最大数を取得する
    :param BeautifulSoup soup:
    :return: 最大ページ数
    :rtype int
    """
    try:
        a = soup.find_all("a", class_="bm-pagination__link")[-1]
    except IndexError:
        return 1
    pages = a.get_attribute_list("href")[0].split("=")[-1]
    pages = int(pages)
    return pages


def fetch_communities(page=1):
    """
    コミュニティ情報を取得する
    コミュニティページは js によって生成されており request で取得した値は meta データとなっている
    そのためメタデータ部分を取得し json として parse することでデータを取得する

    返り値の dict は `"responses"` にコミュニティの情報が配列として入っている

    ```json
    {'metadata':
        {'count': 1909,
        'limit': 20,
        'offset': 0,
        'order': 'desc',
        'sort': 'member_count'},
    'resources': [{'created_at': '2013/05/29',
        'id': 331614,
        'image': 'https://img.bookmeter.com/comm/s120/1/1430909149873826.jpg',
        'member_count': 5335,
        'path': '/communities/331614',
        'title': 'もっと読書友達がほしいよ！！の会',
        'updated_at': '2018/05/27 21:05',
        'user': {'id': 116513,
        'image': 'https://img.bookmeter.com/profile_image/normals/117/1481470050845085.jpg',
        'name': 'うがり@もっと読書友達がほしいよ！！の会コミュ管理人',
        'path': '/users/116513'}},
        {...}
    ]
    }
    ```

    :param int page:
    :return:
    :rtype dict
    """
    res = requests.get("https://bookmeter.com/communities?filter=none&sort=member_count", params=dict(page=page))
    soup = BeautifulSoup(res.text, "lxml")
    community_data = json.loads(soup.find("p").text)
    return community_data


def fetch_users(community_url):
    """
    コミュニティの url から所属するすべてのユーザーの id の配列を取得する

    :param str community_url:
    :return:
    :rtype: list[str]
    """
    members_url = os.path.join(community_url, "members")

    res = requests.get(os.path.join(community_url, "members"), params=dict(page=1))

    soup = BeautifulSoup(res.text, "lxml")
    pages = get_max_pages(soup)

    def fetch_user_ids(url, page=1):
        res = requests.get(url, params=dict(page=page))
        soup = BeautifulSoup(res.text, "lxml")
        user_doms = [div.find("a") for div in soup.find_all(class_="item__username")]

        def find_user_id(dom):
            return dom.get_attribute_list("href")[0].split("/")[-1]

        user_ids = [find_user_id(d) for d in user_doms]

        return user_ids

    user_ids = []
    for page in tqdm(range(pages), total=pages):
        uids = fetch_user_ids(members_url, page)
        user_ids.extend(uids)
    return user_ids


def fetch_reading_logs(user_id):
    """
    user_id にひもづく読書記録を取得する
    [note] user_id のページがない場合などの例外処理は行っていない.要追加実装.

    :param str user_id:
    :return:
    """
    url = BASE_URL + "/users/{user_id}/books/read".format(**locals())
    res = requests.get(url, params=dict(page=1))
    soup = BeautifulSoup(res.text, "lxml")
    max_pages = get_max_pages(soup)
    logger.info("max pages\t{}".format(max_pages))

    for page in range(max_pages):
        res = requests.get(url, params=dict(page=page))
        logger.info(res.url + "\tpage: {}".format(page))
        soup = BeautifulSoup(res.text, "lxml")
        sleep(.5)
        dates = [div.text for div in soup.find_all("div", class_="detail__date")]
        authors = [ul.find("a") for ul in soup.find_all("ul", class_="detail__authors")]
        titles = [ul.find("a") for ul in soup.find_all(class_="detail__title")]

        for author, title, date in zip(authors, titles, dates):
            author_id = author.get_attribute_list("href")[0].split("=")[-1]
            book_id = title.get_attribute_list("href")[0].split("/")[-1]
            read_log = reading_log_record(book_id=book_id, author_id=author_id, user_id=user_id, read_date=date)
            book = book_record(id=book_id, title=title.text)
            author = author_record(id=author_id, name=author.text)
            yield read_log, book, author


def run_fetch_logs(num_communities=5, force=False):
    user_ids = []
    logger.info("start fetch community data")
    for page in tqdm(range(num_communities), total=num_communities):
        community_data = fetch_communities(page)
        urls = [BASE_URL + "/" + community["path"] for community in community_data["resources"]]
        user_id_arrays = Parallel(n_jobs=5)(delayed(fetch_users)(url) for url in urls)
        for arr in user_id_arrays:
            user_ids.extend(arr)

    user_ids = np.unique(user_ids)
    logger.info("total users: {}".format(len(user_ids)))

    for user_id in tqdm(user_ids, total=len(user_ids)):
        output_dir = os.path.join(OUTPUT_DIR, user_id)
        if force is False:
            already_exist = os.path.exists(output_dir)
            if already_exist:
                continue

        books, authors, reading_logs = [], [], []
        for l, b, a in fetch_reading_logs(user_id):
            books.append(b)
            authors.append(a)
            reading_logs.append(l)

        if os.path.exists(output_dir) is False:
            os.makedirs(output_dir)

        for name, arr in zip(("books", "authors", "reading_logs"), (books, authors, reading_logs)):
            df = pd.DataFrame.from_records([item._asdict() for item in arr])
            fpath = os.path.join(output_dir, "{user_id}-{name}.tsv".format(**locals()))
            df.to_csv(fpath, sep="\t", index=False)
