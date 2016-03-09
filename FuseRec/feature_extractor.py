from __future__ import division
from json import loads as jl
from pickle import dump as pd
from math import log

import config

# Container for user vectors
user_vectors = dict()


# Natural log of total users / no. of users using function f in vector set v.
def get_inverse_user_freq(f, v):
    return log(len(v)/sum([f in data.keys() for data in v.itervalues()]))


def get_weighted_vectors(vectors):
    for (user, data) in vectors.iteritems():
        # Iterate through and normalize the each user vector.
        user_sum = sum([v for v in data.itervalues()])
        data.update((k, v/user_sum) for (k, v) in data.iteritems())

        # Now get the weighted vector values using inverse user frequency.
        data.update((k, config.tuning_param["alpha"] * v * get_inverse_user_freq(k, vectors))
                    for (k, v) in data.iteritems())

        vectors[user] = data
    return vectors


def update_vector(user_id, func_name, func_count):
    if func_count == 0:
        return

    # Find if there is one entry for the user ID.
    if user_id not in user_vectors.keys():
        # Create if the entry is not there.
        user_vectors[user_id] = dict({func_name: func_count})
        return

    # Update the vector.
    vector = user_vectors[user_id]
    if func_name not in vector.keys():
        vector[func_name] = func_count
    else:
        vector[func_name] += func_count

    user_vectors[user_id] = vector
    return


def process_json_metadata():
    with open(config.fuse["json_file"], 'r') as fd:
        # IMPORTANT: One json record per line, not an array of json objects.
        for line in fd:
            json_record = jl(line)

            # Find the user identifier, using created by from POI data or the domain name from domain data
            created_by = ""
            last_modified_by = ""
            if "POI" in json_record.keys():
                if json_record["POI"]["createdBy"] is not None:
                    created_by = json_record["POI"]["createdBy"].encode('ascii', 'ignore')
                if json_record["POI"]["lastModifiedBy"] is not None:
                    last_modified_by = json_record["POI"]["lastModifiedBy"].encode('ascii', 'ignore')

            domain_name = ""
            if "InternetDomainName" in json_record.keys() and json_record["InternetDomainName"]["Host"] is not None:
                domain_name = json_record["InternetDomainName"]["Host"].encode('ascii', 'ignore')

            user_id = created_by + "#" + last_modified_by + "#" + domain_name

            for function_key, value in json_record["POI"].iteritems():
                # Check if the key begins with prefix count.
                if function_key.startswith("count"):
                    function_count = int(value)
                    function_name = function_key[len("count"):]

                    if function_count > 0:
                        update_vector(user_id, str(function_name), function_count)

    # Dump the data to a file.
    with open(config.rec_data["vectors"], "w+") as output:
        pd(user_vectors, output)

    # Dump the weighted vectors if flag is on.
    if config.pickle_dump_weighted:
        with open(config.rec_data["vectors_weighted"], "w+") as weighted_output:
            pd(get_weighted_vectors(user_vectors), weighted_output)

    return


def main():
    process_json_metadata()
    return 0


if __name__ == '__main__':
    main()