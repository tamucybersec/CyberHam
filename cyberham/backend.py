import random
import string

from typing import Literal
from datetime import datetime
from pytz import timezone

from cyberham import es_conf
from cyberham.google_apis import GoogleClient, EmailPending
from elasticsearch import Elasticsearch

pending_emails = {}
google_client = GoogleClient()
client = Elasticsearch(es_conf.endpoints, api_key=(es_conf.id, es_conf.api_key), verify_certs=False)

def init_db():
    # Create tables if they do not exist
    if not client.indices.exists(index=f"users-{es_conf.index_postfix}"):
        mappings = {
            "properties": {
                "name": {"type": "text"},
                "points": {"type": "integer"},
                "attended": {"type": "integer"},
                "grad_year": {"type": "integer"},
                "email": {"type": "text"},
                "discord_id": {"type": "text"},
                "dietary_restriction.vegetarian": {"type": "boolean"},
                "dietary_restriction.allergy": {"type": "text"},
            }
        }
        client.indices.create(index = f"events-{es_conf.index_postfix}", mappings = mappings)

    # Create tables if they do not exist
    if not client.indices.exists(index = f"events-{es_conf.index_postfix}"):
        mappings = {
            "properties": {
                "code": {"type": "keyword"},
                "points": {"type": "integer"},
                "type": {"type": "keyword"},
                "time.start": {"type": "date"}, 
                "time.end": {"type": "date"},
                "description": {"type": "text"},
                "location": {"type": "keyword"},
            }
        }
        client.indices.create(index = f"events-{es_conf.index_postfix}", mappings = mappings)

    if not client.indecies.exists(index = f"events-attendance-{es_conf.index_postfix}"):
        mappings = {
            "properties": {
                "event_code": {"type": "keyword"},
                "user_id": {"type": "keyword"},
            }
        }
        client.indices.create(index = f"events-attendance-{es_conf.index_postfix}", mappings = mappings)

    if not client.indices.exists(index = f"rsvp-{es_conf.index_postfix}"):
        mappings = {
            "properties": {
                "event_code": {"type": "keyword"},
                "user_id": {"type": "keyword"},
                "attending": {"type": "boolean"},
            }
        }
        client.indices.create(index = f"rsvp-{es_conf.index_postfix}", mappings = mappings)
        
    


def create_event(name: str, points: int, date: str, resources: str, user_id: int):
    code = ""
    code_list = [0]
    # Check if code already exists, if not generate a new one
    while code_list is not None:
        code = "".join([random.choice(string.ascii_uppercase) for _ in range(5)])
    
    # Insert event into database
    client.index(
        index = f"events-{es_conf.index_postfix}",
        id = code,
        document = {
            "name": name,
            "code": code,
            "points": points,
            "date": date,
            "resources": resources,
        }
    )

    # Update user's points and attended events
    new_id = client.search(index = f"events_{es_conf.index_postfix}",
            query = {"match" :
                     {"user_id" : user_id}})
    curr_user_doc = new_id["hits"]["hits"][0]
    new_points = curr_user_doc["_source"]["points"] + points
    new_attended = curr_user_doc["_source"]["attended"] + 1
    client.update(
        index = f"users_{es_conf.index_postfix}",
        id = curr_user_doc["_source"]["user_id"],
        doc = {
            "points": new_points,
            "attended": new_attended,
        }
    )
    return code

def unwrapping (data):
    return (data["hits"]["hits"][0]["_source"]["name"],
            data["hits"]["hits"][0]["_source"]["points"],
            data["hits"]["hits"][0]["_source"]["date"],
            data["hits"]["hits"][0]["_source"]["resources"])

def attend_event(code: str, user_id: int, user_name: str):
    code = code.upper()
    query = {
        "query": {
            "match": {
                "user_id": user_id,
            }
        }
    }
    user = client.search(index = f"users-{es_conf.index_postfix}", body = query)
    if user["hits"]["total"]["value"] == 0:
        return "Please use /register to make a profile!"
    code_query = {
        "query": {
            "match": {
                "code": code,
            }
        }
    }
    if client.search(index = f"events-{es_conf.index_postfix}", body = code_query)["hits"]["total"]["value"] == 0:
        return "This event does not exist or has passed!"
    elif client.search(index = f"events-{es_conf.index_postfix}", body = code_query)["hits"]["total"]["value"] == 1:
        return "You have already attended this event!"
    
    cst_tz = timezone('US/Central')
    current_day = datetime.now(cst_tz).date() 
    event_day = datetime.strptime(client.search(index = f"events-{es_conf.index_postfix}", body = code_query)["hits"]["hits"][0]["_source"]["date"], "%m/%d/%Y").date()
    if current_day > event_day:
        return "This event has passed!"
    elif current_day < event_day:
        return "This event has not occurred yet!"
    elif current_day == event_day:
        client.update(
            index = f"events-{es_conf.index_postfix}",
            id = code,
            doc = {
                "attended": user["hits"]["hits"][0]["_source"]["attended"] + 1,
                "points": user["hits"]["hits"][0]["_source"]["points"] + client.search(index = f"events-{es_conf.index_postfix}", body = code_query)["hits"]["hits"][0]["_source"]["points"],
            }
        )
        # return f"Successfully registered for {code} {client.search(index = f"events-{es_conf.index_postfix}", body = code_query)}!", (
        #     unwrapping(user),
        # )


def leaderboard(axis: Literal["points", "attended"], lim: int = 10):
    if axis == "points":
        leaderboard_point_query = {
            "query": {
                "match_all": {}
            },
            "sort": [
                {
                    "points": {
                        "order": "desc"
                    }
                }
            ],
            "size": lim
        }
    elif axis == "attended":
        leaderboard_attended_query = {
            "query": {
                "match_all": {}
            },
            "sort": [
                {
                    "attended": {
                        "order": "desc"
                    }
                }
            ],
            "size": lim
        }
    return leaderboard_point_query, leaderboard_attended_query

# needs reviewing
def leaderboard_search(activity: str):
    counts = {}
    if activity == "points":
        query = {
            "query": {
                "match_all": {}
            }
        }
        data = client.search(index = f"users-{es_conf.index_postfix}", body = query)
        for user in data["hits"]["hits"]:
            counts[user["_source"]["name"]] = user["_source"]["points"]
    elif activity == "attended":
        query = {
            "query": {
                "match_all": {}
            }
        }
        data = client.search(index = f"users-{es_conf.index_postfix}", body = query)
        for user in data["hits"]["hits"]:
            counts[user["_source"]["name"]] = user["_source"]["attended"]
    return counts


def register(name: str, grad_year: int, email: str, user_id: int, user_name: str, guild_id: int):
    user = client.search(index = f"users-{es_conf.index_postfix}",
            query = {"match" :
                     {"user_id" : user_id}})
    try:
        grad_year = int(grad_year)
    except ValueError:
        return "Please set your graduation year in the format YYYY (e.g. 2022)"
    if not datetime.now().year - 100 < grad_year < datetime.now().year + 5:
        return "Please set your graduation year in the format YYYY (e.g. 2022)"
    email = email.lower()
    if (
        "," in email
        or ";" in email
        or email.count("@") != 1
        or not email.endswith("tamu.edu")
    ):
        return "Please set a proper TAMU email address"
    ask_to_verify = register_email(user_id, email, guild_id)
    client.update(
        index = f"users_{es_conf.index_postfix}",
        id = user["hits"]["hits"][0]["_id"],
        doc = {
            "name": name,
            "grad_year": grad_year,
            "user_id": user_id,
        }
    )
    return f"You have successfully updated your profile! {ask_to_verify}"

def register_email(user_id, email, guild_id):
    query = {
        "query": {
            "match": {
                "user_id": user_id
            }
        },
        "_source": ["email"]
    }
    temp = client.search(index = f"users-{es_conf.index_postfix}", body = query)
    if temp["hits"]["total"]["value"] == 0 and user_id not in pending_emails:
        return ""
    elif user_id in pending_emails:
        flagged = client.search(index = f"flagged-{es_conf.index_postfix}", query = {"match": {"user_id": user_id}})
        if flagged["hits"]["total"]["value"] == 0:
            client.index(index = f"flagged-{es_conf.index_postfix}", body = {"user_id": user_id, "offences": 1})
        else:
            client.update(index = f"flagged-{es_conf.index_postfix}", id = flagged["hits"]["hits"][0]["_id"], body = {"script": {"source": "ctx._source.offences += 1"}})
            flagged = client.search(index = f"flagged-{es_conf.index_postfix}", query = {"match": {"user_id": user_id}})
            if flagged["hits"]["hits"][0]["_source"]["offences"] >= 3:
                return "Too many failed attempts to email verification, please contact an officer"
    query2 = {
        "query": {
            "match": {
                "email": email
            }
        },
        "_source": ["user_id"]
    }
    temp2 = client.search(index = f"users-{es_conf.index_postfix}", body = query2)  
    if temp2["hits"]["total"]["value"] != 0:
        client.update(
            index = f"flagged-{es_conf.index_postfix}", 
            id = flagged["hits"]["hits"][0]["_id"], 
            body = {"script": {"source": "ctx._source.offences += 1"}})
        return "This email has already been registered"
    verification = EmailPending(
        user_id = user_id,
        email = email,
        code = random.randint(1000, 10000),
        date = datetime.now()
    )
    pending_emails[user_id] = verification
    google_client.send_email(email, str(verification.code),
                              'Texas A&M Cybersecurity Club' if guild_id == 631254092332662805 else 'TAMUctf')
    return "Please use /verify with the code you received in your email."


def verify_email(code: int, user_id: int):
    if user_id in pending_emails:
        pend_email = pending_emails[user_id]
        if pend_email.code == code:
            my_id = client.search(index = f"users-{es_conf.index_postfix}",
                client = {
                    "user_id": user_id
                })

            client.update(index = f"users-{es_conf.index_postfix}",
                id  = my_id["hits"]["hits"][0]["_source"]["user_id"],
                doc = {
                    "email": pend_email.email,
                })
            pending_emails.pop(user_id)
            return "Email verified! It is now visible on your /profile"
        else:
            return "This code is not correct!"
    else:
        return "Please use /register to submit your email"


def remove_pending(user_id: int = 0):
    del pending_emails[user_id]


def profile(user_id: int):
    document = client.search(index = f"users-{es_conf.index_postfix}",
        query = {
            "user_id":user_id
        })
    numDocs = document['hits']['total']['value']
    if numDocs == 0:
        return "Your profile does not exist", None
    return "", document["hits"]["hits"][0]["_source"]



def find_event(code: str = "", name: str = ""):
    data={}
    if name == "" and code == "":
        return "Please include an event name or code.", None

    elif code == "":
        data = client.search(index = f"events-{es_conf.index_postfix}",
            query = {"name": name})
    elif name == "":
        data = client.search(index=f"events-{es_conf.index_postfix}",
            query = {"code": code})
    else:
        data = client.search(index=f"events-{es_conf.index_postfix}",
            query = {"name": name, "code": code})

    docs_found = data['hits']['total']['value']
    if docs_found ==0:
        return "This event does not exist", None
    else:
        return "", data['hits']['hits'][0]['_source']
    

def event_list():
    data = client.search(index=f"events-{es_conf.index_postfix}",
        query={"match_all": {}})
    return data['hits']['hits']


def award(user_id: int, user_name: str, points: int):
    id  = client.search(index = f"users-{es_conf.index_postfix}",
        query = {"match": {"user_id": user_id}})
    results = id["hits"]["total"]["value"]
    name = ""
    new_points = 0
    if results == 0:
        return "This user has not registered yet!"
    else:
        name = id['hits']["hits"][0]["_source"]["name"]
        new_points = id['hits']["hits"][0]["_source"]["points"] + points
    client.update(
        index = f"users-{es_conf.index_postfix}",
        id = id["hits"]["hits"][0]["_source"]["user_id"],
        doc = {
            "points": new_points
        }
    )
    return f"Successfully added {points} points to {user_name} - {name}"


def calendar_events():
    return google_client.get_events()
