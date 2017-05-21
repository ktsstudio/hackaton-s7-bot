import abc
import os

import numpy as np

from gensim.models import KeyedVectors, Word2Vec

__all__ = (
    'GoogleWordVectors',
    'GloveWordVectors',
    'load'
)


class WordVectors:
    def __init__(self, model):
        self.model = model
        self._dim = self.get('word').shape[0]

    @classmethod
    @abc.abstractmethod
    def load(cls, *args):
        raise NotImplementedError

    @property
    def dim(self):
        return self._dim

    @abc.abstractmethod
    def get(self, word):
        raise NotImplementedError

    def map_to_words(self, word_index):
        embedding_matrix = np.zeros((len(word_index) + 1, self.dim))
        for word, i in word_index.items():
            embedding_vector = self.get(word)
            if embedding_vector is not None:
                embedding_matrix[i] = embedding_vector

        return embedding_matrix


class GensimWordVectors(WordVectors):
    @classmethod
    def load(cls, root_dir, path, *args):
        model = Word2Vec.load(os.path.join(root_dir, path))
        return cls(model)

    def get(self, word):
        try:
            return self.model.wv[word]
        except KeyError:
            return None


class GoogleWordVectors(GensimWordVectors):
    @classmethod
    def load(cls, root_dir, *args):
        embeddings_index = KeyedVectors.load_word2vec_format(
            os.path.join(root_dir, 'GoogleNews-vectors-negative300.bin'),
            binary=True
        )

        return cls(embeddings_index)

    def get(self, word):
        try:
            return self.model[word]
        except KeyError:
            return None


class GloveWordVectors(WordVectors):
    @classmethod
    def load(cls, root_dir, glove_dim=300):
        glove_dim = int(glove_dim)

        embeddings_index = {}
        glove_path = os.path.join(root_dir,
                                  'glove.6B.{}d.txt'.format(glove_dim))
        with open(glove_path, 'r') as f:
            for line in f:
                values = line.split()
                word = values[0]
                coefs = np.asarray(values[1:], dtype=np.float32)
                embeddings_index[word] = coefs

        return cls(embeddings_index)

    def get(self, word):
        return self.model.get(word)


_word_vectors_cache = {}


def load(name, root_dir, reload=False):
    if name is None:
        return None

    if not reload and name in _word_vectors_cache:
        return _word_vectors_cache[name]

    if name.startswith('.' + os.path.sep):
        path = os.path.join(root_dir, name)
        assert os.path.exists(path), 'Path {} does not exist'.format(path)
        res = GensimWordVectors.load(root_dir, name)
    else:
        args = name.split(':')
        name = args[0]
        args = args[1:]

        if name == 'glove':
            res = GloveWordVectors.load(root_dir, *args)
        elif name == 'word2vec':
            res = GoogleWordVectors.load(root_dir, *args)
        else:
            raise AssertionError('Unknown word vectors type: {}'.format(name))

    _word_vectors_cache[name] = res
    return res
