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


def get_profile_subscriptions(profile=None):
    profile = profile or load_profile()
    return profile["subscriptions"]

def get_profile_default_subscription(subs=None, profile=None):
    subs = subs or get_profile_subscriptions(profile)
    for s in subs:
        if s.get("isDefault", False):
            return s

    raise KeyError("No default subscription found")

