# coding: utf-8
"""
write about this python script
"""
import os
import re
from gensim import corpora
from logging import getLogger, StreamHandler
from tqdm import tqdm

__author__ = "nyk510"

stop_chars = ['', '\n']

logger = getLogger(__name__)
logger.setLevel("DEBUG")
handler = StreamHandler()
handler.setLevel("DEBUG")
logger.addHandler(handler)


def load_feature(root_path="data", target="title"):
    """
    読書データの読み込み
    ユーザーごとに
    * author_{user-id}.txt
    * title_{user-id}.txt
    の命名でファイルがあって、その中にタブ区切りで値が入っているものとしています
    
    data
    ├── authors_100931.txt
    ├── authors_101171.txt
    ├── authors_101195.txt
    ├── authors_101373.txt
    ├── authors_102709.txt
    ├── authors_10277.txt
    ├── authors_102887.txt
    ├── authors_103416.txt
    ├── authors_10393.txt
    ├── authors_104421.txt
    ~~~
    
    :param str root_path: データが入っているディレクトリへのパス
    :param str target: `title` or `author`
    :return: list[list[str]]
    """
    data = []
    logger.info("Loading...")
    for fn in tqdm(os.listdir(root_path)):
        if target not in fn:
            continue
        fp = os.path.join(root_path, fn)
        with open(fp, "r") as f:
            d_i = f.read()

        d_i = re.split(r"[\t,]", d_i)
        d_i = [word.replace('\u3000', '').replace('\n', '').replace(' ', '') for word in d_i]
        d_i = [char for char in d_i if char not in stop_chars]
        if "," in d_i:
            data.extend(d_i.split(","))
        else:
            data.append(d_i)
    return data


def compile_corpus_and_dictionary(words, no_below=3, no_above=.3, save_to=None):
    """
    単語集合からコーパスと辞書 (gensim.Dictionary) を生成する
    
    :param list[list[str]] words: 単語の配列の配列. 第1次元が文章, 第2次元がその文章中の単語の配列
    :param int no_below: 単語へのフィルタ. これより出現回数の少ない単語を取り除く. 
    :param float no_above: 
        単語へのフィルタ. 文章全体でこれよりも出現回数の多いものは
        文章を特徴づける上で必要がない common word とみなして除去する. 
    :param save_to: この引数が与えられたとき作成した辞書を保存する. 
    :return: (corpus, gensim.Dictionary)
    """
    dictionary = corpora.Dictionary(words)
    dictionary.filter_extremes(no_below=no_below, no_above=no_above)
    if save_to:
        dictionary.save_as_text(save_to)

    cp = [dictionary.doc2bow(doc) for doc in words]
    return cp, dictionary


if __name__ == "__main__":
    data = load_feature("data")
    print(data[:10])
