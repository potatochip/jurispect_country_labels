def independent_either_probability(oldp, newp):
    probability_non_occurrence = (1-oldp) * (1-newp)
    new_probability = 1 - probability_non_occurrence
    return new_probability
