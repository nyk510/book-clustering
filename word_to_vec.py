# coding: utf-8
"""
Word2Vec によるクラスタ分類
"""

from logging import getLogger, StreamHandler
from gensim.models import Word2Vec
import os

from features import load_feature

__author__ = "nyk510"

logger = getLogger(__name__)
logger.setLevel("DEBUG")
handler = StreamHandler()
handler.setLevel("DEBUG")
logger.addHandler(handler)


class W2VTrainer(object):
    """
    
    :param str output_dir: 保存するディレクトリ
    :param str name_format: 保存するときの名前のフォーマット. 
    """

    def __init__(self, output_dir, name_format="{model_type}_{size}_{window}_{epochs}_{negative_size}_{loss}.wv.txt"):
        if os.path.exists(output_dir) is False:
            os.makedirs(output_dir)

        self.output_dir = output_dir
        self.model = None
        self.name = ""
        self.name_format = name_format

    def run(self, sentences, model_type="skipgram", approximation="negative", size=64, window=20, epochs=10,
            negative_size=5):
        """
        word2vec を実行する関数
        :param List[List[str]] sentences: 単語ごとに分かち書きされた文章の配列. 
        :param str model_type: `"skipgram"` or `"cbow"`
        :param str approximation: softmax関数の近似方法. `"negative"` or `"hierarchical"`
        :param int size: 表現ベクトルの数. 4の倍数にすると良いらしい (gensim公式見解)
        :param int window: ウィンドウ幅
        :param int epochs: エポック数
        :param int negative_size: ネガティブサンプリングを行う際のサンプル数. model_type が `approximation` が negative のときのみ有効
        :return: 
        """
        if model_type == "skipgram":
            sg = 1
        elif model_type == "cbow":
            sg = 0
        else:
            raise ValueError("invalid model_type.")

        if approximation == "hierarchical":
            hs = 1
        else:
            hs = 0

        logger.info("Start Word2Vec Training")
        self.model = Word2Vec(sentences, sg=sg, hs=hs, negative=negative_size, size=size, window=window, iter=epochs,
                              compute_loss=True
                              )
        loss = self.model.get_latest_training_loss()

        # 名前を更新する
        self.name = self.name_format.format(**locals())

        logger.info("Completed!!")

        # モデルの保存
        self.save()

        return self.model

    def save(self, name=None):
        """
        モデルを output_dir に保存する
        :param str name: ファイル名. None のとき name_format によって作成する. 
        :return: 
        """
        if name is None:
            name = self.name
        path = os.path.join(self.output_dir, name)
        logger.info("save to {path}".format(**locals()))
        self.model.wv.save_word2vec_format(path, binary=False)
        return self.model


def main():
    docs = load_feature()
    trainer = W2VTrainer(output_dir="data/checkpoints")
    trainer.run(docs[:1000])


if __name__ == "__main__":
    main()
