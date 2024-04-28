import codecs
import os
import json

def get_azure_profile_filepath():
    return "{}/.azure/azureProfile.json".format(os.environ["HOME"])

def load_profile():
    with codecs.open(get_azure_profile_filepath(), 'r', 'utf-8-sig') as fi:
        profile_data = json.load(fi)

    return profile_data

def store_profile(profile_data):
    with codecs.open(get_azure_profile_filepath(), 'w', 'utf-8-sig') as fo:
        json.dump(profile_data, fo)
