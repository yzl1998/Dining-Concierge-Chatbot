import requests
import json
import time

cuisines = ["italian-restaurant", "french-restaurant", "chinese-restaurant", "spanish-restaurant",
            "japanese-restaurant", "greek-restaurant", "turkish-restaurant", "american-restaurant"]

def request(term, location = "New York City", limit = 50):
    api_key = 'cC5tHerCFqDGm6SJw0e4DWrfBgPpJ8Jc9FS0yfctVUnJ7VMIkCO-T6fQ1yCOghPQlKwOZeoS3FpsvyUafMH807N4Y9Gcr6Fd2C9Wum1nHVpqUMfn1AaT-tcepHEUYnYx'
    headers = {'Authorization': 'Bearer %s' % api_key}
    url = 'https://api.yelp.com/v3/businesses/search'

    offset = 0
    businesses = []
    for i in range(20):
        params = {'term':term,'location': location, 'limit': limit, 'offset': offset}
        req = requests.get(url, params = params, headers = headers)
        offset += 50
        if(req.status_code == 200):
            parsed = json.loads(req.text)
            businesses.extend(parsed["businesses"])

        print(term + ": " + str(len(businesses)))

    file_name = term + '.json'
    with open(file_name, 'w') as openfile:
        json.dump(businesses, openfile, indent = 4)

def main():
    for cuisine in cuisines:
        request(cuisine)
        time.sleep(10)

if __name__ == '__main__':
    main()
