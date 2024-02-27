# Yelp elite project

When a Yelp user publishes enough detailed reviews of restaurants, he can acquire the status of an [elite user](https://www.yelp.com/elite/lawest). Elite users are often invited to events to try food and drinks for free since their feedback is highly sought after by restaurants, chefs and chains.

This project is exploring how one could become a Yelp elite user quickly by generating fake reviews produced by chatGPT and how Yelp could defend its plateform from such malicious users.

# How to use the project

In order to use the project, you need:
- a Yelp account
- a Yelp API key
- an Open AI API key

First, clone the project. In the project folder, create a `user_credentials` folder. In this folder, create two files:
- one containing your Yelp account user credentials called `user_credentials.json` as follow
```JSON
{
    "email": "YOUR_EMAIL",
    "password": "YOUR_PASSWORD"
}
```
- one containing your Yelp API key and Open AI API key called `api_keys.json` as follow
```JSON
{
    "yelp_api_key": "YOUR_YELP_API_KEY",
    "openai_api_key": "YOUR_OPEN_AI_API_KEY"
}
```
It is important that these file are stored at the correct location `Yelp_elite\user_credentials\` with the correct name (more precisely `user_credentials.json` and `api_keys.json`). The code will automatically load the user credentials from this folder and will otherwise crash if it is stored somewhere else.

# Attack

The idea in the attack phase is to generate a new fake review based on existing reviews already published on the plateform by other users.

To do so, create a `YelpBot` and input a loction where you want to find restaurants to scrape reviews from, like so

```python
import json
from YelpBot import YelpBot

yelp_bot = YelpBot()
location = "Your location"
my_restaurants = yelp_bot.get_list_of_restaurants_from_location(location)
```

Once the list of restaurant is created, you can get a list of reviews for one of the restaurants, 

```python
# Get reviews for a restaurant
restaurant_reviews = yelp_bot.get_reviews_from_restaurant(
    restaurant=my_restaurants[0],
    number_of_pages=1
)
```

Yelp publishes ten reviews per page, so if you want to scrape twenty reviews for example, you would switch `number_of_pages=2`. The scraped reviews are stored in a JSON file with the following format

```JSON
{
    "Restaurant name": {
        "url": "https://www.yelp.com/restaurant_url",
        "reviews": {
            "0": {
                "text": "Sed consequuntur est voluptas accusantium possimus. Distinctio aperiam tempore et est excepturi exercitationem saepe. Deserunt veniam aliquid nemo nisi voluptas cumque ipsam vel. Aut occaecati quo labore. Repellat qui odio nam minus qui voluptatibus itaque.",
                "rating": 5.0
            },
            "1": {
                "text": "Sed consequuntur est voluptas accusantium possimus. Distinctio aperiam tempore et est excepturi exercitationem saepe. Deserunt veniam aliquid nemo nisi voluptas cumque ipsam vel. Aut occaecati quo labore. Repellat qui odio nam minus qui voluptatibus itaque.",
                "rating": 5.0
            },
            "2": {
                "text": "Sed consequuntur est voluptas accusantium possimus. Distinctio aperiam tempore et est excepturi exercitationem saepe. Deserunt veniam aliquid nemo nisi voluptas cumque ipsam vel. Aut occaecati quo labore. Repellat qui odio nam minus qui voluptatibus itaque.",
                "rating": 4.0
            },
            "..."
        }
    }
}
```

Then, the new review can be generated based on the scraped reviews

```python
# Generate a new review for a restaurant
new_review = yelp_bot.generate_new_review(
    restaurant_reviews,
    number_of_reviews=4
)
```

The `number_of_reviews` argument controls how many reviews are taken into account to generate the new review. The newly generated review is then stored in a JSON file with the following format

```JSON
{
    "Restaurant name": {
        "url": "https://www.yelp.com/restaurant_url",
        "text": "Sed consequuntur est voluptas accusantium possimus. Distinctio aperiam tempore et est excepturi exercitationem saepe. Deserunt veniam aliquid nemo nisi voluptas cumque ipsam vel. Aut occaecati quo labore. Repellat qui odio nam minus qui voluptatibus itaque.",
        "rating": 4
    }
}
```

Finally, to complete the attack, the program uses a [selenium](https://www.selenium.dev/) bot to post the review on Yelp. To create the bot and post the review, use the following code 

```python
# Posting reviews
name = next(iter(new_review))
restaurant_url = new_review[name]['url']

yelp_bot.create_bot(headless=False)
yelp_bot.open_yelp(restaurant_url)
yelp_bot.open_write_review()
yelp_bot.post_review(new_review)
```

This will have the effect to open a chrome web page at the restaurant's url, connect to your Yelp account using your user credential and input the text and rating on the posting page. The final result then looks like so 

![image](https://github.com/chagab/Yelp_elite/assets/28218716/22d9e258-cd9a-4280-8310-bfa708848f84)

At this point, you are one click away from completing the attack. This shows that this procedure could be automated to publish a large amount of fake reviews on a plateform like Yelp. Currently (February 2024), nohting is preventing this kind of attacks.

# Defense 

As you can see, the text shown above passes all the criterium on Yelp, nothing is checking if the text was written by a human. However, [tools](https://www.scribbr.com/ai-detector/) to detect AI generated text already exist

![image](https://github.com/chagab/Yelp_elite/assets/28218716/0b93d331-6074-4b9f-9e06-177063c40ec4)

and are [efficient](https://www.scribbr.com/ai-tools/best-ai-detector/) in their classification, even if the generated text is based on multiple real examples as you can see above. The idea in the defense phase is to use such an AI-detector while the user is writting his reviews in order to avoid such spaming, like so

![image140-modif](https://github.com/chagab/Yelp_elite/assets/28218716/b28955ed-f122-4c71-9d05-d6624e9b0146)








