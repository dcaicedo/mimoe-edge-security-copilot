from security_agent.domain.similarity import cosine_similarity


def test_similar_vectors_score_higher_than_unrelated():
    similar_a = [1.0, 1.0, 0.0]
    similar_b = [1.0, 0.9, 0.1]
    unrelated = [0.0, 0.0, 1.0]

    score_similar = cosine_similarity(similar_a, similar_b)
    score_unrelated = cosine_similarity(similar_a, unrelated)

    assert score_similar > score_unrelated
