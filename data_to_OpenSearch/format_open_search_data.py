import json

cuisines = [ "italian-restaurant", "french-restaurant", "chinese-restaurant", "spanish-restaurant",
            "japanese-restaurant", "greek-restaurant", "turkish-restaurant", "american-restaurant"]
metadata = '{"index": {"_index": "restaurants", "_type": "restaurant"}}'

for cuisine in cuisines:
    file_name = cuisine + '.json'
    with open(file_name) as json_file:
        businesses = json.load(json_file)
        for business in businesses:
            restaurant_id = business["id"]
            restaurant_info = '{"id": "' + restaurant_id +'", "cuisine": "' + cuisine + '"}'
            print(metadata)
            print(restaurant_info)