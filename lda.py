# coding: utf-8
"""
LDA (latent dirichlet allocation) による分類
"""
from gensim import models
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from logging import getLogger, StreamHandler

__author__ = "nyk510"

logger = getLogger(__name__)
logger.setLevel("DEBUG")
handler = StreamHandler()
handler.setLevel("DEBUG")
logger.addHandler(handler)


class LDATrainer(object):
    def __init__(self, output_dir):
        self.model = None
        self.output_dir = output_dir

    def run(self, corpus, dictionary, topics=5):
        """
        LDA の学習を実行する. 
        :param corpus: 
        :param gensim.Dictionary dictionary: 
        :param int topics:
        :return: 
        """
        model_params = {
            "corpus": corpus,
            "num_topics": topics,
            "alpha": "asymmetric",
            "id2word": dictionary,
            "iterations": 30
        }
        logger.info("*" * 30 + "\nStart LDA Learning. ")
        self.model = models.LdaMulticore(**model_params)
        logger.info("Complete!!")
        return self.model

    def show_topics(self, save_to_dir="./data", num_words=20):
        lda_model = self.model
        for topic_id in range(lda_model.num_topics):
            data_i = np.array(lda_model.show_topic(topic_id, topn=num_words))
            fig, ax1 = plt.subplots(1, 1, figsize=(6, int(num_words * .5)))
            df_i = pd.DataFrame(data_i[:, 1].astype(np.float)[::-1] * 100, index=data_i[:, 0][::-1],
                                columns=["probability"])
            df_i.plot(kind="barh", ax=ax1)
            cls_prob = lda_model.alpha[topic_id]
            ax1.set_title("クラスタ{topic_id} クラスタ選択確率{cls_prob:.3f}".format(**locals()))
            ax1.set_xlabel("確率(%)")
            fig.tight_layout()
            fname = "cluster_{0}.png".format(topic_id)
            fpath = os.path.join(save_to_dir, fname)
            fig.savefig(fpath, dpi=150)


if __name__ == "__main__":
    from features import load_feature, compile_corpus_and_dictionary

    data = load_feature()
    corpus, dictionary = compile_corpus_and_dictionary(data)
    trainer = LDATrainer(output_dir="./data/checkpoint")
    trainer.run(corpus, dictionary)
    trainer.show_topics(save_to_dir="./")
