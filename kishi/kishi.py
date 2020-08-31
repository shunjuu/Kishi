import re
import requests

from ayumi import Ayumi

_ANILIST_API_URL = "https://graphql.anilist.co"

_USER_ANIME_QUERY = '''
query ($userName: String) {
    MediaListCollection(userName: $userName, type: ANIME) {
        lists {
            name
            entries {
                media {
                    id
                    title {
                        romaji
                        english
                        native
                        userPreferred
                    }
                }
            }
        }
    }
}
'''

def _check_equality(name1, name2) -> bool:
    Ayumi.debug("Regex comparing: {} | {}".format(name1, name2))
    try:
        # Anilist sometimes has weird leading/trailing spaces
        re_str1 = re.sub(r'[^\w]', '', name1)
        Ayumi.debug("Name 1 without puncutation: {}".format(re_str1))
        re_str2 = re.sub(r'[^\w]', '', name2)
        Ayumi.debug("Name 2 without puncutation: {}".format(re_str2))

        if re_str1 == re_str2:
            Ayumi.debug("Both show names are matching, returning True.")
            return True
        else:
            Ayumi.debug("Show names do not match, returning False.")
            return False
    except:
        Ayumi.debug("Error occured while matching show names, returning False.")
        return False

def _add_list_entries(list_name, list_json):
    """
    Helper method to add all list entries into a medialist (watching/paused/ptw)
    Params:
        list_name: the name that the list appears to be from Anilist ("Watching")
        list_json: anilist's raw api response (json format) {'data':'MediaListCollection'}

    Returns: A list with populated Anilist Media entries (a list of dicts)
    """
    try:

        entries = list()

        media_lists = list_json['data']['MediaListCollection']['lists']
        for media_list in media_lists:
            if list_name.lower() == media_list['name'].lower():
                for entry in media_list['entries']:
                    entries.append(entry['media'])

        return entries

    except:
        Ayumi.warning("Kishi was unable to process list entries for {}".format(list_name))
        raise Exception()

def _kishi_list(user):
    """
    Helper method to get all of a user's anime list.

    Params:
        user: String, username of Anilist user

    Returns: A tuple of three lists.
        The first list is all the Watching
        The second list is all the PTW
        The third list is all the Paused

    Throws an exception if anything goes wrong. This should be caught by any method using this.
    """

    watching = list()
    paused = list()
    ptw = list()

    # Anilist API is much nicer to play with. 
    try:
        # Make the request to Anilist, and pass in the userName as the user query
        anilist_res = requests.post(_ANILIST_API_URL,
            json={'query': _USER_ANIME_QUERY, 'variables': {'userName': user}})

        if anilist_res.status_code != 200:
            Ayumi.error("Anilist returned a bad status code when attempting to get {}'s lists".format(user))
            raise Exception()

        try:
            anilist_res_json = anilist_res.json()
        except:
            Ayumi.error("Anilist returned a response that was not parseable into JSON")
            raise Exception()

        watching = _add_list_entries("Watching", anilist_res_json)
        paused = _add_list_entries("Paused", anilist_res_json)
        ptw = _add_list_entries("Planning", anilist_res_json)

    except:
        Ayumi.critical("Kishi was unable to properly contact Anilist")
        raise Exception()
        
    return (watching, paused, ptw)


def is_user_watching_names(user, show_name):
    """
    Determines whether or not an Anilist user is watching a show
    Checks by show name

    Params:
        user: username to look up
        show_name: name of the show to look up. this should already be the anilist name.

    Returns: a boolean - True if watching, False if not
    """
    try:
        watching, paused, ptw = _kishi_list(user)

        for show in watching:
            for title in show['title'].values():
                if _check_equality(title, show_name):
                    Ayumi.debug("Matched {} to {} in {}".format(title, show_name, "watching"))
                    return True 

        for show in paused:
            for title in show['title'].values():
                if _check_equality(title, show_name):
                    Ayumi.debug("Matched {} to {} in {}".format(title, show_name, "paused"))
                    return True 

        for show in ptw:
            for title in show['title'].values():
                if _check_equality(title, show_name):
                    Ayumi.debug("Matched {} to {} in {}".format(title, show_name, "planning"))
                    return True 

        Ayumi.debug("Didn't find a match for {}".format(show_name))
        return False

    except:
        # If any errors are encountered, return True (default assumption)
        Ayumi.warning("An error was encountered while contacting Anilist. Defaulting to TRUE")
        return True

def is_user_watching_id(user, show_id):
    """
    Determines whether or not an Anilist user is watching a show
    Checks by show ID

    Params:
        user: username to look up
        id: id of the show to look up

    Returns: a boolean - True if watching, False if not
    """

    try:
        show_id = int(show_id) # Get the int equivalent value of the ID
    except:
        # Why would you not pass an integer in?
        Ayumi.critical("Kishi ID search requires an input that can be converted to an int. Returning FALSE")
        return False

    try:

        watching, paused, ptw = _kishi_list(user)

        for show in watching:
            if show_id == show['id']:
                Ayumi.debug("Found show ID {} in {}".format(show_id, "watching"))
                return True

        for show in paused:
            if show_id == show['id']:
                Ayumi.debug("Found show ID {} in {}".format(show_id, "paused"))
                return True

        for show in ptw:
            if show_id == show['id']:
                Ayumi.debug("Found show ID {} in {}".format(show_id, "planning"))
                return True

        Ayumi.debug("Didn't find a match for {}".format(show_id))
        return False

    except:
        # If any errors are encountered, return True (default assumption)
        Ayumi.warning("An error was encountered while contacting Anilist. Defaulting to TRUE")
        return True