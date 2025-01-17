##############################
# QUEST APP METADATA SCRAPER #
##############################
# Created by Ethan https://github.com/threethan/
# for https://github.com/threethan/LightningLauncher
# based on code by Ellie https://github.com/basti564

from __future__ import annotations
import time
from typing import NamedTuple, List, Optional, Callable
import json
import logging
import os
import requests
import re
import concurrent.futures

logging.basicConfig(level=logging.INFO)
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
logging.getLogger("requests_ratelimiter.requests_ratelimiter").setLevel(logging.WARNING)

session = requests.Session()

from requests.adapters import HTTPAdapter
adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100)
session.mount('http://', adapter)
session.mount('https://', adapter)

class App(NamedTuple):
    appName: str
    packageName: str
    id: str

AppList = List[App]

#############
# Constants #
#############

OUTPUT_DIRS = ["data/oculus", "data/oculus_public", "data/sidequest", "data/common"]

OCULUS_TEMPLATE = "data/oculus/{}.json"
OCULUS_PUBLIC_TEMPLATE = "data/oculus_public/{}.json"
SIDEQUEST_TEMPLATE = "data/sidequest/{}.json"
COMMON_TEMPLATE = "data/common/{}.json"
KNOWN_OCULUS_APPS = "data/known_oculus_apps.json"
KNOWN_SIDEQUEST_APPS = "data/known_sidequest_apps.json"

IMAGE_MAPPINGS_OCULUS = {
    "APP_IMG_COVER_LANDSCAPE": "landscape",
    "APP_IMG_COVER_PORTRAIT": "portrait",
    "APP_IMG_COVER_SQUARE": "square",
    "APP_IMG_ICON": "icon",
    "APP_IMG_HERO": "hero",
    "APP_IMG_LOGO_TRANSPARENT": "logo"
}
IMAGE_MAPPINGS_OCULUS_PUBLIC = {
    "cover_landscape_image" : "landscape",
    "cover_square_image" : "square",
    "cover_portrait_image" : "portrait",
    "icon_image" : "icon",
}
IMAGE_MAPPINGS_SIDEQUEST = {
    "image_url": "landscape",
    "app_banner": "hero",
}

OCULUS_SPECIAL_PACKAGE_NAMES = {
     "1916519981771802" : "com.oculus.browser", # Otherwise returns a null binary
}

OCULUS_DB_URL = "https://oculusdb.rui2015.me/api/v1/allapps"
OCULUS_GRAPHQL_URL = "https://graph.oculus.com/graphql"
META_GRAPHQL_URL = "https://www.meta.com/ocapi/graphql"
SIDEQUEST_URL = "https://api.sidequestvr.com/search-apps"

OCULUS_SECTION_IDS = ["1888816384764129", "174868819587665"]

############
# FILE OPS #
############

def dump_applist(filename: str, data: AppList) -> None:
    try:
        dict_data = [app._asdict() for app in data]
        with open(filename, "w") as file:
            json.dump(dict_data, file)
        logging.info(f"App list saved to {filename}")
    except IOError as e:
        logging.error(f"Failed to save app list to {filename}")
        
def dump_json(filename: str, data) -> None:
    try:
        with open(filename, "w") as file:
            json.dump(data, file)
    except IOError as e:
        logging.error(f"Failed to save data to {filename}")


def load_applist(filename: str) -> AppList:
    try:
        with open(filename) as file:
            dict_data = json.load(file)
            return [App(**app_dict) for app_dict in dict_data]
    except FileNotFoundError:
        return []

###########
# UTILITY #
###########

def merge_apps(existing_apps: AppList, new_apps: AppList) -> AppList:
    existing_packages = {app.packageName for app in existing_apps}
    merged_data = existing_apps[:]
    for new_app in new_apps:
        package_name = new_app.packageName
        if package_name not in existing_packages:
            logging.debug(f"NEW: {new_app}")
            merged_data.append(new_app)
    return merged_data


def merge_app_ids(*id_lists: List[str]) -> List[str]:
    merged_ids = set()
    for id_list in id_lists:
        merged_ids.update(id_list)
    return list(merged_ids)

def fetch_apps_concurrently(app_ids: List[str], fetch_function: Callable[[str], Optional[App]]) -> AppList:
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_app_id = {executor.submit(fetch_function, app_id): app_id for app_id in app_ids}

        for future in concurrent.futures.as_completed(future_to_app_id):
            app_id = future_to_app_id[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
                    if (result % 100 == 0)
                        print(f"Processing Oculus Apps [{len(results)}/{len(app_ids)}] ({len(results)/len(app_ids)*100:2.0f}%)", end="\r")
                    logging.debug(f"Processed app ID: {app_id}")
            except Exception as exc:
                logging.warning(f"App ID {app_id} generated an exception: {exc}")
        print(f"Processing Oculus Apps [{len(results)}/{len(app_ids)}] (Done)")
    return results

##########
# OCULUS #
##########

def fetch_oculusdb_oculus_app_ids() -> AppList:
    logging.info("Fetching OculusDB apps...")

    response = session.get(OCULUS_DB_URL)
    if response.status_code != 200:
        return []
        
    data = response.json()

    sidequest_apps = [
        App(
            appName=app.get("appName", ""),
            packageName=app.get("packageName", ""),
            id=app.get("id", ""),
        )
        for app in data
        if app.get("packageName") and "rift" not in app.get("packageName")
    ]

    logging.info(f"Fetched {len(sidequest_apps)} apps from OculusDB.")

    return sidequest_apps

def fetch_oculus_section_items(section_id: str, section_cursor: str = "0", page_num: int= 1) -> list:
    variables = {
        "ageRatingFilter":[],
        "controllerFilter":[],
        "cursor":section_cursor,
        "first":128,
        "interactionModeFilter":[],
        "languageFilter":[],
        "playerModeFilter":[],
        "priceRangeFilter":[],
        "ratingAboveFilter":0,"saleTypeFilter":[],
        "sortOrder":[],
        "topicIdFilter":[],
        "id":section_id,
        "__relay_internal__pv__MDCAppStoreShowRatingCountrelayprovider":False
    }

    data = {
        'lsd': 'AVqMsnyvi0U',
        'variables': json.dumps(variables),
        'doc_id': '28462698003329119',
    }

    headers = {'X-FB-LSD': 'AVqMsnyvi0U'}
    response = session.post(META_GRAPHQL_URL, headers=headers, data=data)

    json_text = response.text.split("}\r\n")[0] + '}'
    response_data =  json.loads(json_text)
    
    apps = response_data.get("data", {}).get("node", {}).get("all_items", {}).get("edges", [])
    if not apps:
        logging.error(f"Failed to fetch Oculus Store apps from {section_id} ({section_cursor})")
        return []
    
    meta_store_data_by_id = [{app["node"]["id"] : app} for app in apps]
        
    page_info = response_data.get('data', {}).get('node', {}).get( 'all_items', {}).get('page_info', {})

    if page_info["has_next_page"]:
        logging.info(f"Fetching next Oculus Store page ({page_num})...")
        meta_store_data_by_id.extend(fetch_oculus_section_items(section_id, page_info["end_cursor"], page_num=page_num+1))

    return meta_store_data_by_id


def fetch_oculus_oculus_app_ids(section_id: str) -> list:
    logging.info(f"Fetching Oculus Store apps for section {OCULUS_SECTION_IDS.index(section_id)}...")

    rv = fetch_oculus_section_items(section_id)     
    logging.info(f"Fetched {len(rv)} apps from Oculus Store from section {OCULUS_SECTION_IDS.index(section_id)}.")

    return rv

# Intentionally unused due to rate limit
def get_oculus_public_json(id:str) -> dict:
    text = session.get('https://www.meta.com/experiences/{}/'.format(id)).text
    script_tag_start = text.find('<script type="application/ld+json"')
    if (script_tag_start == -1):
        if ("<title>Error</title>" in text):
            logging.debug(f"Oculus app {id} does not have a store page")
        else:
            logging.error(f"Failed to fetch public info for Oculus app {id} (Store page fetched without json data)  ({s} : {f})")
        return {}
    script_tag_start = text.find('>', script_tag_start)+1
    script_tag_end = text.find('</script>', script_tag_start)
    return json.loads(text[script_tag_start:script_tag_end])

def fetch_and_store_oculus_app_info_by_id(oculus_app_id: str) -> App | None:
    if (oculus_app_id == "1265732843505431"):
        logging.debug("Skipping old oculus avatar editor to prevent exception")
        return None

    store_stuff_variables = {"applicationID": oculus_app_id}
    store_stuff_payload = {
        "doc_id": "8571881679548867",
        "access_token": "OC|1076686279105243|",
        "variables": json.dumps(store_stuff_variables)
    }
    store_stuff_response = session.post(OCULUS_GRAPHQL_URL, data=store_stuff_payload)
    store_format_data = store_stuff_response.json()
    if store_format_data["data"]["node"] == None:
        logging.debug(f"{oculus_app_id} returned invalid, empty data")
        return None
    
    # App details        
    app_details_variables = {
        "applicationID": oculus_app_id
    }
    app_details_payload = {
        "doc_id": "3828663700542720",
        "access_token": "OC|1076686279105243|",
        "variables": json.dumps(app_details_variables)
    }

    app_details_response = session.post(OCULUS_GRAPHQL_URL,
                                        data=app_details_payload)
    app_details_data = app_details_response.json()
    
    latest_supported_binary = app_details_data["data"]["node"][
        "release_channels"
    ]["nodes"][0]["latest_supported_binary"]
        
    if latest_supported_binary is not None:
        app_binary_info_variables = {
            "params": {
                "app_params": [
                    {
                        "app_id": oculus_app_id,
                        "version_code": latest_supported_binary['version_code']
                    }
                ]
            }
        }

        app_binary_info_payload = {
            "doc": """
                query ($params: AppBinaryInfoArgs!) {
                    app_binary_info(args: $params) {
                        info {
                            binary {
                                ... on AndroidBinary {
                                    id
                                    package_name
                                    version_code
                                    asset_files {
                                        edges {
                                            node {
                                                ... on AssetFile {
                                                    file_name
                                                    uri
                                                    size
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            """,
            "variables": json.dumps(app_binary_info_variables),
            "access_token": "OC|1317831034909742|"
        }

        app_binary_info_response = session.post(OCULUS_GRAPHQL_URL,
                                                json=app_binary_info_payload)
        app_binary_info_data = app_binary_info_response.json()
        
        if oculus_app_id in OCULUS_SPECIAL_PACKAGE_NAMES:
            package_name = OCULUS_SPECIAL_PACKAGE_NAMES[oculus_app_id]
        else:
            package_name = app_binary_info_data["data"]["app_binary_info"]["info"][0]\
            ["binary"]["package_name"]
    else:
        return
    
    public_data = oculus_public_info_by_id.get(oculus_app_id, {}).get("node", {})
    dump_json(OCULUS_TEMPLATE.format(package_name), store_format_data)
    
    if public_data != {}:
        dump_json(OCULUS_PUBLIC_TEMPLATE.format(package_name), public_data)
    
    app_name = store_format_data["data"]["node"]["display_name"] if "display_name" in store_format_data["data"]["node"] else package_name

    if "display_name" in public_data:
        app_name = public_data["display_name"]


    common_format_data = {"name":app_name,
                        "version":latest_supported_binary['version'],
                        "versioncode":latest_supported_binary['version_code']}
    
    if "category_name" in public_data:
        common_format_data["category"] = public_data["category_name"]
        
    if "genre_names" in public_data and len(public_data["genre_names"]) > 0:
        common_format_data["genre"] = public_data["genre_names"][0]
    
    translations = []
    try:
        translations.extend(store_format_data["data"]["node"]["lastRevision"]["nodes"][0]["pdp_metadata"]["translations"]["nodes"])
    except:
        pass
    try:
        translations.extend(store_format_data["data"]["node"]["firstRevision"]["nodes"][0]["pdp_metadata"]["translations"]["nodes"])
    except:
        pass
    
    for translation in translations:
        if translation["locale"] == "en_US": # Only english has images
            for image in translation["images"]["nodes"]:
                image_type = image["image_type"]
                if image_type not in IMAGE_MAPPINGS_OCULUS:
                    continue
                
                common_format_data[IMAGE_MAPPINGS_OCULUS[image_type]] = image["uri"]

    for k, v in IMAGE_MAPPINGS_OCULUS_PUBLIC.items():
        if k in public_data:
            common_format_data[v] = public_data[k]["uri"]
                    
    logging.debug(f"Finished {package_name}")
    dump_json(COMMON_TEMPLATE.format(package_name), common_format_data)
    
    return App(appName=app_name, packageName=package_name, id=oculus_app_id)

#############
# SIDEQUEST #
#############

def fetch_sidequest_basic_data():
    logging.info("Fetching Sidequest apps...")

    page = 0
    has_more = True
    app_data_list = []

    headers = {
        "Origin": "https://sidequestvr.com",
    }

    while has_more:
        logging.debug(f"Fetching Sidequest apps from page {page}")
        params = {
            "search": "",
            "page": page,
            "order": "created",
            "direction": "desc",
            "app_categories_id": 1,
            "tag": None,
            "users_id": None,
            "limit": 100,
            "device_filter": "all",
            "license_filter": "all",
            "download_filter": "all",
        }

        response = session.get(SIDEQUEST_URL, params=params, headers=headers)
        data = response.json()

        if not data["data"]:
            break

        app_data_list.extend(data["data"])
        page += 1

    logging.info(f"Fetched {len(app_data_list)}")
    return app_data_list

class SideQuestResult(NamedTuple):
    sidequest_apps: AppList
    oculus_app_ids: list
    
def fetch_and_store_sidequest(sidequest_data = fetch_sidequest_basic_data()) -> SideQuestResult:
    sidequest_apps : AppList = []
    oculus_apps_ids = []
    for app in sidequest_data:
        app_id = str(app["apps_id"])
        app_name = app["name"]
        package_name = app["packagename"]
        
        dump_json(SIDEQUEST_TEMPLATE.format(package_name), app)
        
        if package_name.startswith("com.autogen.") and "labrador_url" in app and app["labrador_url"].startswith(
                "https://www.oculus.com/experiences/quest/"):
            labrador_url = app["labrador_url"]
            oculus_app_id = re.search(r'/quest/(\d+)', labrador_url).group(1)
            oculus_apps_ids.append(oculus_app_id)
        else:
            # Common format data
            common_format_data = {"name":app_name, "versioncode":app['versioncode']}
            for key, val in IMAGE_MAPPINGS_SIDEQUEST.items():
                common_format_data[val] = app[key]
            dump_json(COMMON_TEMPLATE.format(package_name), common_format_data)
            
            new_app = App(appName=app_name, packageName=package_name, id=app_id)
            sidequest_apps.append(new_app)
            
    logging.info(f"SideQuest had {len(oculus_apps_ids)} oculus apps, {len(sidequest_apps)} of its own.")
    return SideQuestResult(sidequest_apps=sidequest_apps, oculus_app_ids=oculus_apps_ids)

########
# MAIN #
########

if __name__ == "__main__":
    global oculus_public_info_by_id
      
    for dir in OUTPUT_DIRS:
        os.makedirs(dir, exist_ok=True)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        
        future_oculusdb = executor.submit(fetch_oculusdb_oculus_app_ids)
        future_sidequest = executor.submit(fetch_and_store_sidequest)
                
        oculusdb_apps = future_oculusdb.result()
        sidequest_result = future_sidequest.result()
        
    oculus_public_info:list = []
    oculus_sectional_public_info = [fetch_oculus_oculus_app_ids(section) for section in OCULUS_SECTION_IDS]
    for section_public_info in oculus_sectional_public_info:
        oculus_public_info.extend(section_public_info)

    
    oculus_public_info_by_id = {}
    for entry in oculus_public_info:
        oculus_public_info_by_id.update(entry)

    logging.info("Loading known app list...")
    existing_oculus_apps = load_applist(KNOWN_OCULUS_APPS)

    all_app_ids = merge_app_ids(sidequest_result.oculus_app_ids,
                                [app.id for app in existing_oculus_apps],
                                [app.id for app in oculusdb_apps],
                                oculus_public_info_by_id.keys())

    logging.info("Fetching apps concurrently...")
    new_oculus_apps = fetch_apps_concurrently(all_app_ids, fetch_and_store_oculus_app_info_by_id)
    merged_oculus_apps = merge_apps(existing_oculus_apps, new_oculus_apps)
    dump_applist(KNOWN_OCULUS_APPS, merged_oculus_apps)
    
    # Merge sidequest
    logging.info("Handling sidequest data...")
    existing_sidequest_apps = load_applist(KNOWN_SIDEQUEST_APPS)
    merged_sidequest_apps = merge_apps(existing_sidequest_apps, sidequest_result.sidequest_apps)
    dump_applist(KNOWN_SIDEQUEST_APPS, merged_sidequest_apps)
