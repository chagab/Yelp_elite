import os
import json
import random
import requests
from openai import OpenAI

from fake_useragent import UserAgent
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException
)
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver


class YelpBot:

    _all = []

    short_sleep_time = 3
    long_sleep_time = 10
    _current_location = ''

    def __init__(
        self,
        yelp_api_key=None,
        # TODO - add an argument for the openAI key
        user_credentials_folder=None
    ) -> None:

        if yelp_api_key is None:

            if user_credentials_folder is None:
                self.user_credentials_folder = 'user_credentials'
            else:
                self.user_credentials_folder = user_credentials_folder

            api_key_path = os.path.join(
                self.user_credentials_folder,
                'api_keys.json'
            )

            with open(api_key_path) as f:
                keys = json.load(f)
                yelp_api_key = keys['yelp_api_key']
                openai_api_key = keys['openai_api_key']
        else:
            err_message = "Expecting they API to be a string, got "
            err_message += f"{yelp_api_key}"
            assert type(yelp_api_key) == str, err_message
            yelp_api_key = yelp_api_key

        self.headers = {'Authorization': f'Bearer {yelp_api_key}'}
        self.base_url = f'https://api.yelp.com/v3/businesses/'

        self.openAI_client = OpenAI(api_key=openai_api_key)
        self.store_folder = 'res'

        YelpBot._all.append(self)

    def get_list_of_restaurants_from_location(
        self,
        location,
        store=False
    ) -> list[dict]:
        """
        Get the list of restaurants for a given location.

        arg:
            - location [str]: location where to get restaurant from.

        return [list[dict]]:
            - a list of dictionaries containing all the informations
            about the restaurants.

        """

        # Define the URL for the Yelp Fusion API to search for restaurants
        url = self.base_url + f'search?term=restaurants&location={location}'

        # Send a request to the API and get the response
        response = requests.get(url, headers=self.headers)

        # Extract the list of restaurants from the response
        list_of_restaurants = response.json()
        restaurants = list_of_restaurants['businesses']

        if store:
            if not os.path.isdir(self.store_folder):
                os.makedirs(self.store_folder)

            store_path = os.path.join(
                self.store_folder,
                "list_of_restaurants.json"
            )

            json.dump(
                list_of_restaurants,
                open(store_path, 'w'),
                indent=2
            )
        return restaurants

    def get_reviews_from_restaurant(self, restaurant: str) -> dict:
        """
        Get the list of reviews of a single restaurant.

        arg:
            - restaurant [str]: name of the restaurant.

        return [dict]:
            - a dictionary containing the restaurant's url, reviews and
            ratings.
        """
        # Define the URL for the Yelp Fusion API to get reviews
        # for the restaurant
        business_id = restaurant['id']
        url = self.base_url + f'{business_id}/reviews'

        # Send a request to the API and get the response
        response = requests.get(url, headers=self.headers)
        response_data = response.json()
        reviews = response_data['reviews']

        # Extract the list of reviews and their ratings from the response
        restaurant_reviews = {}
        name = restaurant['name']
        restaurant_reviews[name] = {}
        restaurant_reviews[name]['url'] = restaurant['url']
        restaurant_reviews[name]['reviews'] = {}
        for i, review in enumerate(reviews):
            restaurant_reviews[name]['reviews'][i] = {
                'text': review['text'],
                'rating': review['rating']
            }

        return restaurant_reviews

    def get_reviews_from_restaurants(
        self,
        restaurants: list[dict],
        store=True
    ) -> list[str]:
        """
        Get a list of reviews for a list of restaurants.

        arg:
            - restaurants [list[dict]]: a list of dictionaries containing the
            information about the restaurants.
            - store [bool]: If true, the result of the function will be stored
            in a json file named true_reviews.json in the file directory.

        return [list[str]]:
            - a dictionary where each field name is a restaurant name, each 
            value is a dictionary containing the reviews and rating of the
            given restaurant.
        """

        restaurants_reviews = {}

        for restaurant in restaurants:
            reviews = self.get_reviews_from_restaurant(restaurant)
            restaurants_reviews |= reviews

        if store:
            if not os.path.isdir(self.store_folder):
                os.makedirs(self.store_folder)

            store_path = os.path.join(self.store_folder, "true_reviews.json")

            json.dump(
                restaurants_reviews,
                open(store_path, 'w'),
                indent=2
            )

        return restaurants_reviews

    def generate_new_review_text(self, restaurant_reviews: dict) -> str:
        """
        Generate a new review's text with OpenAI's GPT-3.5 model based
        on a list of reviews.

        arg:
            - restaurant_reviews [dict]: a dictionary containing a list of 
            reviews for a given restaurant.

        return [str]:
            - the new review's text
        """
        restaurant_name = next(iter(restaurant_reviews))
        prompt = f'Generate a new review for {restaurant_name} based on the '
        prompt += 'following reviews:\n'

        reviews = restaurant_reviews[restaurant_name]['reviews']
        for review in reviews.values():
            prompt += f"- {review['text']}\n"

        prompt += 'Make the new review about a specific dish that was '
        prompt += 'mentionned in the given reviews.\n'
        prompt += 'New review:'

        messages = [{"role": "user", "content": prompt}]

        response = self.openAI_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1024,
        )

        review_text = response.choices[0].message.content.strip()
        return review_text

    def generate_new_review_rating(self, restaurant_reviews: dict) -> int:
        """
        Generate a new review's rating by computing the avreage of a list
        of reviews.

        arg:
            - restaurant_reviews [dict]: a dictionary containing a list of 
            reviews for a given restaurant.

        return [int]:
            - the new review's rating
        """
        restaurant_name = next(iter(restaurant_reviews))
        reviews = restaurant_reviews[restaurant_name]['reviews']
        restaurant_ratings = [review['rating'] for review in reviews.values()]
        avg_rating = int(sum(restaurant_ratings) / len(restaurant_ratings))

        return avg_rating

    def generate_new_review(self, restaurant_reviews: dict) -> dict:
        """
        Generate a new review with OpenAI's GPT-3.5 model based on a list of
        reviews and ratings.

        arg:
            - restaurant_reviews [dict]: a dictionary containing a list of 
            reviews for a given restaurant.

        return [dict]:
            - a dictionary containing the name of the restaurant, it's URL,
            a new review text and rating
        """
        restaurant_name = next(iter(restaurant_reviews))
        new_text = self.generate_new_review_text(restaurant_reviews)
        new_rating = self.generate_new_review_rating(restaurant_reviews)
        new_review = {
            restaurant_name:
            {
                'url': restaurant_reviews[restaurant_name]['url'],
                'text': new_text,
                'rating': new_rating
            }
        }

        return new_review

    def generate_new_reviews(
        self,
        restaurants_reviews: dict,
        n_per_restaurant=4,
        store=False
    ) -> dict:
        """
        Generate a list of new reviews with OpenAI's GPT-3.5 model based
        on a list of reviews and ratings for multiple restaurants.

        arg:
            - restaurant_reviews [dict]: a dictionary containing a list of 
            reviews for multiple restaurants.
            - n_per_restaurant [int]: how many new reviews to generate per
            restaurant.
            - store [bool]: if true the result of the function will be 
            stored in a json file called new_reviews.json in the working
            directory.

        return [dict]:
            - a dictionary containing the list of new reviews 
        """
        rating_fluctuations = [-1, 0, 1]

        new_reviews = {}
        for name, reviews in restaurants_reviews.items():
            new_reviews[name] = {}
            new_reviews[name]['url'] = reviews['url']
            new_reviews[name]['reviews'] = {}

            for i in range(n_per_restaurant):
                new_reviews[name]['reviews'][i] = {
                    'text': self.generate_new_review_text({name: reviews}),
                    'rating': self.generate_new_review_rating({name: reviews}) +
                    random.choice(rating_fluctuations)
                }

        if store:
            if not os.path.isdir(self.store_folder):
                os.makedirs(self.store_folder)

            store_path = os.path.join(self.store_folder, "new_reviews.json")

            json.dump(
                new_reviews,
                open(store_path, 'w'),
                indent=2
            )

        return new_reviews

    def create_bot(self, headless=True) -> None:
        options = webdriver.ChromeOptions()
        ua = UserAgent()
        user_agent = ua.random
        if headless:
            options.add_argument("--headless=new")
        else:
            options.add_argument("start-maximized")
        options.add_argument(f'--user-agent={user_agent}')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        print(self.driver.execute_script("return navigator.userAgent;"))

    def open_yelp(self) -> None:

        self.driver.get('https://www.yelp.com/')
        try:
            WebDriverWait(self.driver, self.long_sleep_time).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "/html/body/yelp-react-root/div[1]/div[2]/div[2]/div/header/div/div[1]/div[3]/nav/div/div[2]/div/span[3]/button/span"
                ))
            ).click()

        except ElementClickInterceptedException:
            # TODO - implement excpetion handling
            pass

        self.email_login()

    def email_login(self) -> None:
        user_credentials_path = os.path.join(
            self.user_credentials_folder,
            'user_credentials.json'
        )

        with open(user_credentials_path) as f:
            user_credentials = json.load(f)
            email = user_credentials['email']
            password = user_credentials['password']

        # Input user email into email input field
        inputMail = WebDriverWait(self.driver, self.long_sleep_time).until(
            EC.presence_of_element_located((
                By.XPATH,
                "/html/body/yelp-react-root/div[1]/div[2]/div[2]/div/header/div/div[1]/div[3]/nav/div/div[2]/div/div/div/div/div/div[2]/div/div/div[4]/form/div[1]/div/label/input"
            ))
        )
        inputMail.send_keys(email)
        inputMail.send_keys(Keys.RETURN)

        # Input user password into password input field
        inputPassword = WebDriverWait(self.driver, self.long_sleep_time).until(
            EC.presence_of_element_located((
                By.XPATH,
                "/html/body/yelp-react-root/div[1]/div[2]/div[2]/div/header/div/div[1]/div[3]/nav/div/div[2]/div/div/div/div/div/div[2]/div/div/div[4]/form/div[2]/div/label/input"
            ))
        )
        inputPassword.send_keys(password)
        inputPassword.send_keys(Keys.RETURN)
