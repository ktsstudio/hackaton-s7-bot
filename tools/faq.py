import pymorphy2
import numpy as np

from data import prepare, FAQ_RAW, FAQ

morph = pymorphy2.MorphAnalyzer()


def prepare_sim_func(dataset, w2v):
    # jaccard

    def jaccard_similarity(words1, words2):
        if len(words1) == 0 or len(words2) == 0:
            return 0
        return len(set(words1) & set(words2)) / len(set(words1) | set(words2))

    words_count = {}
    for i, words in enumerate(dataset):
        for w in words:
            words_count[w] = words_count.get(w, 0) + 1

    # tfidf

    import collections
    import math
    from scipy.spatial.distance import cosine

    def compute_tf(words):
        tf_text = collections.Counter(words)
        for i in tf_text:
            tf_text[i] /= len(words)
        return tf_text

    def compute_idf(word, words_count):
        wc = words_count.get(word, 0)
        if wc == 0:
            return 0
        return math.log10(len(dataset) / wc)

    def vectorize(w1, w2, words_count) -> tuple:
        words = list(set(w1) | set(w2))
        v1 = np.array([])
        v2 = np.array([])
        text1_tf = compute_tf(w1)
        text2_tf = compute_tf(w2)
        for word in words:
            idf = compute_idf(word, words_count)
            tfidf = text1_tf.get(word, 0) * idf
            v1 = np.append(v1, [tfidf])
            tfidf = text2_tf.get(word, 0) * idf
            v2 = np.append(v2, [tfidf])
        return v1, v2

    def tfidf_similarity(text1, text2):
        v1, v2 = vectorize(text1, text2, words_count)
        if len(v1) == 0 or len(v2) == 0:
            return 0
        return 1 - cosine(v1, v2)

    # TF-IDF WordMatch Share

    def get_weight(count, eps=10000, min_count=2):
        if count < min_count:
            return 0
        else:
            return 1 / (count + eps)

    weights1 = {}

    def recalculate_weights_count():
        nonlocal weights1
        eps = 5000
        counts = words_count
        for i, (word, count) in enumerate(counts.items()):
            weights1[word] = get_weight(count)

    recalculate_weights_count()

    def tfidf_word_match_share(words1, words2, weights):
        q1words = {}
        q2words = {}
        #     for word in str(row['question1']).lower().split():
        for word in words1:
            #         if word not in stops:
            q1words[word] = 1

        # for word in str(row['question2']).lower().split():
        for word in words2:
            #         if word not in stops:
            q2words[word] = 1
        if len(q1words) == 0 or len(q2words) == 0:
            return 0

        shared_weights = [weights.get(w, 0) for w in q1words.keys() if
                          w in q2words] + [weights.get(w, 0) for w in
                                           q2words.keys()
                                           if w in q1words]
        total_weights = [weights.get(w, 0) for w in q1words] + [
            weights.get(w, 0)
            for w in q2words]

        R = np.sum(shared_weights) / np.sum(total_weights)
        return R

    def tfidf_word_match_share_similarity(text1, text2):
        return tfidf_word_match_share(text1, text2, weights1)

    # wmd

    def wmd(text1, text2):
        q1 = ' '.join(text1)
        q2 = ' '.join(text2)
        return w2v.wmdistance(q1, q2)

    def wmd_similarity(text1, text2):
        return 1 - wmd(text1, text2)

    import math

    tf = dict()
    docf = dict()
    total_docs = 0
    for toks in dataset:
        total_docs += 1
        uniq_toks = set(toks)
        for i in toks:
            tf[i] = tf.get(i, 0) + 1
        for i in uniq_toks:
            docf[i] = docf.get(i, 0) + 1

    def idf(word):
        return 1 - math.sqrt(docf[word] / total_docs)

    def weighted_w2v(w1, w2, except_value=0.0):
        try:
            return w2v.similarity(w1, w2) * idf(w1) * idf(w2)
        except Exception:
            return except_value

    def get_similarities(text1, text2, except_value=0.0):
        q1 = text1
        q2 = text2
        similarities = []
        for w1 in q1:
            max_similar = 0
            for w2 in q2:
                similar = weighted_w2v(w1, w2, except_value)
                if similar > max_similar:
                    max_similar = similar
            similarities.append(max_similar)
        return similarities

    def ww2v(text1, text2):
        similarities = get_similarities(text1, text2)
        return np.array(similarities).mean()

    def ww2v_max_similarity(text1, text2):
        similarities = get_similarities(text1, text2)
        if len(similarities) == 0:
            return 0
        return np.array(similarities).max()

    # words share

    def word_match_share(words1, words2):
        q1words = {}
        q2words = {}
        for word in words1:
            q1words[word] = 1
        for word in words2:
            q2words[word] = 1
        if len(q1words) == 0 or len(q2words) == 0:
            # The computer-generated chaff includes a few questions that are nothing but stopwords
            return 0
        shared_words_in_q1 = [w for w in q1words.keys() if w in q2words]
        shared_words_in_q2 = [w for w in q2words.keys() if w in q1words]
        R = (len(shared_words_in_q1) + len(shared_words_in_q2)) / (
        len(q1words) + len(q2words))
        return R

    def word_match_share_similarity(text1, text2):
        return word_match_share(text1, text2)

    def similarity(text1, text2):
        sims = [
            jaccard_similarity,
            tfidf_similarity,
            tfidf_word_match_share_similarity,
            ww2v,
            # ww2v_max_similarity,
            word_match_share_similarity,
            wmd_similarity
        ]
        results = []
        for sim in sims:
            results.append(sim(text1, text2))

        return results

    return similarity


def find_similar_faq(text, dataset, dataset_raw, sim_func, top=5):
    query = prepare(text)
    sims = []
    for q in dataset:
        s = sim_func(q, query)
        s = np.mean(s)
        sims.append(s)

    indices = np.array(sims).argsort()[::-1][:top]
    res = dataset_raw.loc[indices][['title', 'text']]
    result = []
    for _, row in res.iterrows():
        result.append({
            'title': row['title'],
            'text': row['text']
        })

    return result
