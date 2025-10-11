from locust import HttpUser, task, between
import random

BOOK_TITLES = [
    "The Great Gatsby",
    "1984",
    "I Ching",
    "Moby Dick",
]


class BookstoreUser(HttpUser):
    wait_time = between(1, 3)  # type: ignore

    @task(3)
    def view_homepage(self):
        self.client.get("/")

    @task(1)
    def add_to_cart(self):
        book_title = random.choice(BOOK_TITLES)
        quantity = random.randint(1, 3)
        self.client.post(
            "/add-to-cart", data={"title": book_title, "quantity": quantity}
        )
