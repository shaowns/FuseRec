from __future__ import division
from random import choice

import utility
import config


# For a given user u, get back a list of tuples (user_id, cosine distances from given user).
def get_cosine_similarity_for_user(vw, user):
    sims = [(key, utility.get_cosine_similarity(vw[user], data))
            for (key, data) in vw.iteritems() if key != user]
    return sorted(sims, key=lambda x: x[1], reverse=True)


# Get a list of recommendations for a given user ID.
def get_recommendations(data, user):
    # Get the weighted vector for current data.
    vw = utility.get_weighted_vectors(data)

    # Get the sorted similarity values for the given user.
    sims = get_cosine_similarity_for_user(vw, user)

    sims_exp_freq = dict()

    # Only look into the number of similars permitted.
    for sim in sims[0:config.tuning_param["num_sims"]]:
        # Add recommendations with expected frequency, basically the cumulative relative frequency of the similars.
        # Recommendations are those functions that are in the similars but not in the input user vector functions.
        sim_user = sim[0]
        sim_values = data[sim_user]
        c_sum = sum(v for v in sim_values.itervalues())
        sims_exp_freq.update((k, sims_exp_freq.get(k, 0) + config.tuning_param["expected_freq_weight"] * (v/c_sum))
                             for (k, v) in sim_values.iteritems() if k not in data[user].keys())

    # Sort based on the expected frequency.
    recs = sorted(sims_exp_freq, key=sims_exp_freq.get, reverse=True)

    # Limit to number of recommendations in config.
    if len(recs) > config.tuning_param["num_recs"]:
        recs = recs[0: config.tuning_param["num_recs"]]

    return recs


def do_cv():
    # Load the user vectors.
    data = utility.load_vectors()

    # Storage for the success rate.
    rates = list()
    for i in range(config.num_slices):
        train, test = utility.get_data_split(data, i)
        success = do_user_cf(train, test)
        rates.append((success, len(test)))

    return rates


def do_user_cf(train, test):
    success = 0
    for (user, data) in test.iteritems():
        # The function to be removed at random.
        test_func = choice(data.keys())
        data.pop(test_func)

        # Add this modified vector to the training set.
        train[user] = data

        # Get the recommendation for the user in training data.
        if test_func in get_recommendations(train, user):
            success += 1

        # Removed the test user from the training data for next iteration.
        train.pop(user)

    return success


def main():
    do_cv()
    return


if __name__ == "__main__":
    main()
