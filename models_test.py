import datetime
from typing import List
import unittest
from unittest.mock import Mock, call, patch

from models import (
    Book,
    Cart,
    CartItem,
    ShippingInfo,
    Order,
    User,
    CardPaymentInfo,
    PaypalPaymentInfo,
    EmailService,
    PaymentResult,
    PaymentGateway,
)


class BookTest(unittest.TestCase):
    TITLE: str = "The Great Gatsby"
    CATEGORY: str = "Fiction"
    PRICE: float = 32.34
    IMAGE: str = "/images/books/some_image.jpg"

    # Successful initialization
    def test_success(self) -> None:
        Book(self.TITLE, self.CATEGORY, self.PRICE, self.IMAGE)

    # Failed initialization: Empty title
    def test_empty_title(self) -> None:
        with self.assertRaises(ValueError, msg="Book title cannot be empty"):
            Book("", self.CATEGORY, self.PRICE, self.IMAGE)

    # Failed initialization: Empty category
    def test_empty_category(self) -> None:
        with self.assertRaises(ValueError, msg="Book category cannot be empty"):
            Book(self.TITLE, "", self.PRICE, self.IMAGE)

    # Failed initialization: Price zero
    def test_price_zero(self) -> None:
        with self.assertRaises(
            ValueError, msg="Books must have a positive price. Received 0"
        ):
            Book(self.TITLE, self.CATEGORY, 0, self.IMAGE)

    # Failed initialization: Price negative
    def test_price_negative(self) -> None:
        with self.assertRaises(
            ValueError, msg="Books must have a positive price. Received -0.1"
        ):
            Book(self.TITLE, self.CATEGORY, -0.1, self.IMAGE)

    # Failed initialization: Empty image
    def test_empty_image(self) -> None:
        with self.assertRaises(ValueError, msg="Book image cannot be enpty"):
            Book(self.TITLE, self.CATEGORY, self.PRICE, "")


class CartItemTest(unittest.TestCase):
    BOOK: Book = Book("Title", "Category", 10.0, ".")

    # Successful initialization: No quantity
    def test_success_single_1(self) -> None:
        cart_item = CartItem(self.BOOK)
        self.assertEqual(cart_item.get_total_price(), 10.0)

    # Successful initialization: With quantity single
    def test_success_single_2(self) -> None:
        cart_item = CartItem(self.BOOK, quantity=1)
        self.assertEqual(cart_item.get_total_price(), 10.0)

    # Successful initialization: With quantity multiple
    def test_success_multiple(self) -> None:
        cart_item = CartItem(self.BOOK, quantity=5)
        self.assertEqual(cart_item.get_total_price(), 50.0)

    # Failed initialization: Quantity zero
    def test_quantity_zero(self) -> None:
        with self.assertRaises(ValueError, msg="Quantity must be positive. Received 0"):
            CartItem(self.BOOK, quantity=0)

    # Failed initialization: Quantity negative
    def test_quantity_negative(self) -> None:
        with self.assertRaises(
            ValueError, msg="Quantity must be positive. Received -3"
        ):
            CartItem(self.BOOK, quantity=-3)


class CartTest(unittest.TestCase):
    BOOK_1: Book = Book(
        "The Great Gatsby", "Fiction", 10.99, "/images/books/the_great_gatsby.jpg"
    )
    BOOK_2: Book = Book("1984", "Dystopia", 8.99, "/images/books/1984.jpg")
    BOOK_3: Book = Book("I Ching", "Traditional", 18.99, "/images/books/I-Ching.jpg")
    BOOK_4: Book = Book("Moby Dick", "Adventure", 12.49, "/images/books/moby_dick.jpg")

    # Successful initialization: Zero items
    def test_zero_books(self) -> None:
        cart = Cart()

        self.assertEqual(cart.get_total_price(), 0)
        self.assertEqual(cart.get_total_items(), 0)
        self.assertEqual(cart.get_items(), [])
        self.assertEqual(cart.is_empty(), True)

    # Failed add: Zero items
    def test_add_quantity_zero(self) -> None:
        cart = Cart()

        with self.assertRaises(ValueError, msg="Quantity must be positive. Received 0"):
            cart.add_book(self.BOOK_1, 0)

    # Failed add: Negative items
    def test_add_quantity_negative(self) -> None:
        cart = Cart()

        with self.assertRaises(
            ValueError, msg="Quantity must be positive. Received -5"
        ):
            cart.add_book(self.BOOK_1, -5)

    # Successful add: Add single items (multiple times)
    def test_add_book_single(self) -> None:
        cart = Cart()

        # Add a single book
        cart.add_book(self.BOOK_1, quantity=1)
        self.assertEqual(cart.get_total_price(), 10.99)
        self.assertEqual(cart.get_total_items(), 1)
        self.assertEqual(cart.get_items(), [CartItem(self.BOOK_1, 1)])
        self.assertEqual(cart.is_empty(), False)

        # Add the same book again
        cart.add_book(self.BOOK_1, quantity=1)
        self.assertEqual(cart.get_total_price(), 21.98)
        self.assertEqual(cart.get_total_items(), 2)
        self.assertEqual(cart.get_items(), [CartItem(self.BOOK_1, 2)])
        self.assertEqual(cart.is_empty(), False)

        # Add a different book
        cart.add_book(self.BOOK_2, quantity=1)
        self.assertEqual(cart.get_total_price(), 30.97)
        self.assertEqual(cart.get_total_items(), 3)
        self.assertEqual(
            cart.get_items(), [CartItem(self.BOOK_1, 2), CartItem(self.BOOK_2, 1)]
        )
        self.assertEqual(cart.is_empty(), False)

    # Successful add: Add multiple items (multiple times)
    def test_add_book_multiple(self) -> None:
        cart = Cart()

        # Add multiple of one book
        cart.add_book(self.BOOK_1, quantity=14)
        self.assertEqual(cart.get_total_price(), 153.86)
        self.assertEqual(cart.get_total_items(), 14)
        self.assertEqual(cart.get_items(), [CartItem(self.BOOK_1, 14)])
        self.assertEqual(cart.is_empty(), False)

        # Add multiple of a different book
        cart.add_book(self.BOOK_2, quantity=7)
        self.assertEqual(cart.get_total_price(), 216.79)
        self.assertEqual(cart.get_total_items(), 21)
        self.assertEqual(
            cart.get_items(), [CartItem(self.BOOK_1, 14), CartItem(self.BOOK_2, 7)]
        )
        self.assertEqual(cart.is_empty(), False)

        # Add multiple off the first book
        cart.add_book(self.BOOK_1, quantity=5)
        self.assertEqual(cart.get_total_price(), 271.74)
        self.assertEqual(cart.get_total_items(), 26)
        self.assertEqual(
            cart.get_items(), [CartItem(self.BOOK_1, 19), CartItem(self.BOOK_2, 7)]
        )
        self.assertEqual(cart.is_empty(), False)

    # Successful removal: Cart was empty
    def test_remove_book_empty_cart(self) -> None:
        cart = Cart()
        self.assertEqual(cart.get_items(), [])

        cart.remove_book(self.BOOK_1.title)
        self.assertEqual(cart.get_items(), [])

    # Successful removal: Item is not in cart
    def test_remove_noop(self) -> None:
        cart = Cart()

        cart.add_book(self.BOOK_1, 1)
        cart.add_book(self.BOOK_2, 2)
        self.assertEqual(
            cart.get_items(), [CartItem(self.BOOK_1, 1), CartItem(self.BOOK_2, 2)]
        )

        # There is no such book => Nothing is removed
        cart.remove_book(self.BOOK_3.title)
        self.assertEqual(
            cart.get_items(), [CartItem(self.BOOK_1, 1), CartItem(self.BOOK_2, 2)]
        )

    # Successful removal: Various items are removed
    def test_remove_books(self) -> None:
        cart = Cart()

        cart.add_book(self.BOOK_1, 1)
        cart.add_book(self.BOOK_2, 2)
        cart.add_book(self.BOOK_3, 3)
        self.assertEqual(
            cart.get_items(),
            [
                CartItem(self.BOOK_1, 1),
                CartItem(self.BOOK_2, 2),
                CartItem(self.BOOK_3, 3),
            ],
        )

        # Remove the middle book
        cart.remove_book(self.BOOK_2.title)
        self.assertEqual(
            cart.get_items(), [CartItem(self.BOOK_1, 1), CartItem(self.BOOK_3, 3)]
        )

        # Remove the first book
        cart.remove_book(self.BOOK_1.title)
        self.assertEqual(cart.get_items(), [CartItem(self.BOOK_3, 3)])

        # Remove the last book
        cart.remove_book(self.BOOK_3.title)
        self.assertEqual(cart.get_items(), [])

    # Successful update: No such book
    def test_update_quantity_empty(self) -> None:
        cart = Cart()
        self.assertEqual(cart.get_items(), [])

        # There is no such book
        cart.update_quantity(self.BOOK_1.title, 0)
        self.assertEqual(cart.get_items(), [])

        # There is no such book
        cart.update_quantity(self.BOOK_1.title, 1)
        self.assertEqual(cart.get_items(), [])

    # Successful update: No quantity stays the same
    def test_update_quantity_noop(self) -> None:
        cart = Cart()
        cart.add_book(self.BOOK_1, 1)
        self.assertEqual(cart.get_items(), [CartItem(self.BOOK_1, 1)])

        # There is no such book
        cart.update_quantity(self.BOOK_2.title, 0)
        self.assertEqual(cart.get_items(), [CartItem(self.BOOK_1, 1)])

        # There is no such book
        cart.update_quantity(self.BOOK_2.title, 1)
        self.assertEqual(cart.get_items(), [CartItem(self.BOOK_1, 1)])

    # Successful update: Quantity changes
    def test_update_quantity(self) -> None:
        cart = Cart()
        cart.add_book(self.BOOK_1, 1)
        cart.add_book(self.BOOK_2, 2)
        self.assertEqual(
            cart.get_items(), [CartItem(self.BOOK_1, 1), CartItem(self.BOOK_2, 2)]
        )

        # Increase the quantity of book 1
        cart.update_quantity(self.BOOK_1.title, 4)
        self.assertEqual(
            cart.get_items(), [CartItem(self.BOOK_1, 4), CartItem(self.BOOK_2, 2)]
        )

        # Don't change the quantity of book 2
        cart.update_quantity(self.BOOK_2.title, 2)
        self.assertEqual(
            cart.get_items(), [CartItem(self.BOOK_1, 4), CartItem(self.BOOK_2, 2)]
        )

        # Decrease the quantity of book 2
        cart.update_quantity(self.BOOK_2.title, 1)
        self.assertEqual(
            cart.get_items(), [CartItem(self.BOOK_1, 4), CartItem(self.BOOK_2, 1)]
        )

    # Successful clear: Cart was already empty
    def test_clear_empty(self) -> None:
        cart = Cart()
        self.assertEqual(cart.get_items(), [])

        cart.clear()
        self.assertEqual(cart.get_items(), [])

    # Successful clear: Cart is cleared
    def test_clear_items(self) -> None:
        cart = Cart()
        cart.add_book(self.BOOK_1, 1)
        cart.add_book(self.BOOK_2, 2)
        self.assertEqual(
            cart.get_items(), [CartItem(self.BOOK_1, 1), CartItem(self.BOOK_2, 2)]
        )

        cart.clear()
        self.assertEqual(cart.get_items(), [])


class ShippingInfoTest(unittest.TestCase):
    NAME: str = "John Doe"
    EMAIL: str = "john.doe@gmail.com"
    ADDRESS: str = "Some Street 42"
    CITY: str = "London"
    ZIP_CODE: str = "ABC DEF"

    # Successful initialization
    def test_success(self) -> None:
        self.assertEqual(
            ShippingInfo.from_opt_values(
                self.NAME, self.EMAIL, self.ADDRESS, self.CITY, self.ZIP_CODE
            ),
            ShippingInfo(self.NAME, self.EMAIL, self.ADDRESS, self.CITY, self.ZIP_CODE),
        )

    # Failed initialization: Name is None
    def test_name_none(self) -> None:
        self.assertEqual(
            "Name cannot be empty",
            ShippingInfo.from_opt_values(
                None, self.EMAIL, self.ADDRESS, self.CITY, self.ZIP_CODE
            ),
        )

    # Failed initialization: Name is empty
    def test_name_empty(self) -> None:
        self.assertEqual(
            "Name cannot be empty",
            ShippingInfo.from_opt_values(
                "", self.EMAIL, self.ADDRESS, self.CITY, self.ZIP_CODE
            ),
        )

    # Failed initialization: Email is None
    def test_email_none(self) -> None:
        self.assertEqual(
            "Email cannot be empty",
            ShippingInfo.from_opt_values(
                self.NAME, None, self.ADDRESS, self.CITY, self.ZIP_CODE
            ),
        )

    # Failed initialization: Email is empty
    def test_email_empty(self) -> None:
        self.assertEqual(
            "Email cannot be empty",
            ShippingInfo.from_opt_values(
                self.NAME, "", self.ADDRESS, self.CITY, self.ZIP_CODE
            ),
        )

    # Failed initialization: Email does not contain @
    def test_email_no_at(self) -> None:
        self.assertEqual(
            "Email must contain `@`. Received john.doe.com",
            ShippingInfo.from_opt_values(
                self.NAME, "john.doe.com", self.ADDRESS, self.CITY, self.ZIP_CODE
            ),
        )

    # Failed initialization: Address is None
    def test_address_none(self) -> None:
        self.assertEqual(
            "Address cannot be empty",
            ShippingInfo.from_opt_values(
                self.NAME, self.EMAIL, None, self.CITY, self.ZIP_CODE
            ),
        )

    # Failed initialization: Address is empty
    def test_address_empty(self) -> None:
        self.assertEqual(
            "Address cannot be empty",
            ShippingInfo.from_opt_values(
                self.NAME, self.EMAIL, "", self.CITY, self.ZIP_CODE
            ),
        )

    # Failed initialization: City is None
    def test_city_none(self) -> None:
        self.assertEqual(
            "City cannot be empty",
            ShippingInfo.from_opt_values(
                self.NAME, self.EMAIL, self.ADDRESS, None, self.ZIP_CODE
            ),
        )

    # Failed initialization: City is empty
    def test_city_empty(self) -> None:
        self.assertEqual(
            "City cannot be empty",
            ShippingInfo.from_opt_values(
                self.NAME, self.EMAIL, self.ADDRESS, "", self.ZIP_CODE
            ),
        )

    # Failed initialization: Zip Code is None
    def test_zip_code_none(self) -> None:
        self.assertEqual(
            "Zip code cannot be empty",
            ShippingInfo.from_opt_values(
                self.NAME, self.EMAIL, self.ADDRESS, self.CITY, None
            ),
        )

    # Failed initialization: Zip Code is empty
    def test_zip_code_empty(self) -> None:
        self.assertEqual(
            "Zip code cannot be empty",
            ShippingInfo.from_opt_values(
                self.NAME, self.EMAIL, self.ADDRESS, self.CITY, ""
            ),
        )


class OrderTest(unittest.TestCase):
    CART_ITEM_1: CartItem = CartItem(Book("Title 1", "Category 1", 10.0, "Image 1"), 1)
    CART_ITEM_2: CartItem = CartItem(Book("Title 2", "Category 2", 20.0, "Image 2"), 2)

    ID: str = "order-1"
    EMAIL: str = "john.doe@gmail.com"
    SHIPPING_INFO: ShippingInfo = ShippingInfo(
        "John Doe", "john.doe@gmail.com", "Some address", "London", "Some ZIP"
    )
    PAYMENT_METHOD: str = "credit_card"
    TRANSACTION_ID: str = "trans-2"
    TOTAL_AMOUNT: float = 12.34

    def create_order(self, dt: datetime.datetime, items: List[CartItem]) -> Order:
        # Create order with fixed date and items
        with patch("datetime.datetime") as datetime_mock:
            datetime_mock.now.return_value = dt
            return Order(
                self.ID,
                self.EMAIL,
                items,
                self.SHIPPING_INFO,
                self.PAYMENT_METHOD,
                self.TRANSACTION_ID,
                self.TOTAL_AMOUNT,
            )

    # Failed initialization: Order has no items
    def test_init_empty_items(self) -> None:
        dt = datetime.datetime(2025, 10, 10, 12, 5, 0)
        with self.assertRaises(ValueError, msg="Cannot create an order without items"):
            self.create_order(dt, [])

    # Successful initialization: Order has no items
    def test_order_with_items(self) -> None:
        dt = datetime.datetime(2025, 10, 10, 12, 5, 0)
        items = [self.CART_ITEM_1, self.CART_ITEM_2]
        order = self.create_order(dt, items)

        # Validate that the order was created with the expected values
        self.assertEqual(order.order_id, self.ID)
        self.assertEqual(order.user_email, self.EMAIL)
        self.assertEqual(order.items, items)
        self.assertEqual(order.shipping_info, self.SHIPPING_INFO)
        self.assertEqual(order.payment_method, self.PAYMENT_METHOD)
        self.assertEqual(order.transaction_id, self.TRANSACTION_ID)
        self.assertEqual(order.total_amount, self.TOTAL_AMOUNT)
        self.assertEqual(order.order_date, dt)
        self.assertEqual(order.status, "Confirmed")

    # Successful sorting by creation time
    def test_sorting(self) -> None:
        # Create order objects with increasing creation time
        order_1 = self.create_order(
            datetime.datetime(2025, 10, 10, 12, 5, 1), [self.CART_ITEM_1]
        )
        order_2 = self.create_order(
            datetime.datetime(2025, 10, 10, 12, 5, 2), [self.CART_ITEM_2]
        )
        order_3 = self.create_order(
            datetime.datetime(2025, 10, 10, 12, 5, 3), [self.CART_ITEM_1]
        )
        order_4 = self.create_order(
            datetime.datetime(2025, 10, 10, 12, 5, 4), [self.CART_ITEM_2]
        )
        order_5 = self.create_order(
            datetime.datetime(2025, 10, 10, 12, 5, 5), [self.CART_ITEM_1]
        )

        # Add the orders into a list
        orders = [order_1, order_5, order_3, order_2, order_4]

        # The orders are sorted by creation time
        self.assertEqual(sorted(orders), [order_1, order_2, order_3, order_4, order_5])

    # Successful transformation to dictionary
    def test_to_dict(self) -> None:
        dt = datetime.datetime(2025, 10, 10, 12, 5, 0)
        items = [self.CART_ITEM_1, self.CART_ITEM_2]
        order = self.create_order(dt, items)

        self.assertEqual(
            order.to_dict(),
            {
                "items": [
                    {"price": 10.0, "quantity": 1, "title": "Title 1"},
                    {"price": 20.0, "quantity": 2, "title": "Title 2"},
                ],
                "order_date": "2025-10-10 12:05:00",
                "order_id": "order-1",
                "shipping_info": {
                    "address": "Some address",
                    "city": "London",
                    "email": "john.doe@gmail.com",
                    "name": "John Doe",
                    "zip_code": "Some ZIP",
                },
                "status": "Confirmed",
                "total_amount": 12.34,
                "user_email": "john.doe@gmail.com",
            },
        )


class UserTest(unittest.TestCase):
    EMAIL: str = "john.doe@gmail.com"
    NAME: str = "John Doe"
    ADDRESS: str = "Some address"

    def create_user(self, password: str) -> User:
        return User(self.EMAIL, password, self.NAME, self.ADDRESS)

    # Successful initialization
    def test_success(self) -> None:
        password = "12345"
        user = self.create_user(password)

        self.assertEqual(user.email, self.EMAIL)
        self.assertTrue(user.check_password(password))
        self.assertEqual(user.name, self.NAME)
        self.assertEqual(user.address, self.ADDRESS)
        self.assertEqual(user.orders, [])

    # Successfully set password: Same password is set
    def test_set_check_password_1(self) -> None:
        password = "12345"

        # Create user with password 12345
        user = self.create_user(password)
        self.assertTrue(user.check_password(password))
        hash_1 = user.password

        # Override the password with the same value
        user.set_password(password)
        self.assertTrue(user.check_password(password))
        hash_2 = user.password

        # The hash is generated using a random salt. Even though we set
        # the same password, its hash is different
        self.assertNotEqual(hash_1, hash_2)

    # Successfully set password: Different password is set
    def test_set_check_password_2(self) -> None:
        password_1 = "12345"
        password_2 = "67890"

        # Set password_1
        user = self.create_user(password_1)
        self.assertTrue(user.check_password(password_1))
        self.assertFalse(user.check_password(password_2))

        # Set password_2
        user.set_password(password_2)
        self.assertFalse(user.check_password(password_1))
        self.assertTrue(user.check_password(password_2))

    def create_order(self, id: int, dt: datetime.datetime) -> Order:
        items = [CartItem(Book(f"title{id}", "category", id, "image"))]
        shipping_info = ShippingInfo(
            "John Doe",
            "john.doe@gmail.com",
            "Some address",
            "London",
            "Some ZIP",
        )

        # Create order with fixed ID and items
        with patch("datetime.datetime") as datetime_mock:
            datetime_mock.now.return_value = dt
            return Order(
                f"order-{id}",
                self.EMAIL,
                items,
                shipping_info,
                "credit-card",
                f"trans-{id}",
                id,
            )

    # Successfully set order
    def test_add_get_order(self) -> None:
        # New user doesn't have any orders
        user = self.create_user("12345")
        self.assertEqual(user.get_order_history(), [])

        # Create orders
        order_1 = self.create_order(1, datetime.datetime(2025, 10, 10, 12, 5, 1))
        order_2 = self.create_order(2, datetime.datetime(2025, 10, 10, 12, 5, 2))
        order_3 = self.create_order(3, datetime.datetime(2025, 10, 10, 12, 5, 3))
        order_4 = self.create_order(4, datetime.datetime(2025, 10, 10, 12, 5, 4))
        order_5 = self.create_order(5, datetime.datetime(2025, 10, 10, 12, 5, 5))

        # Add order 2
        user.add_order(order_2)
        self.assertEqual(user.get_order_history(), [order_2])

        # Order 4 is added after order 2
        user.add_order(order_4)
        self.assertEqual(user.get_order_history(), [order_2, order_4])

        # Order 3 is added between order 2 and 4
        user.add_order(order_3)
        self.assertEqual(user.get_order_history(), [order_2, order_3, order_4])

        # Order 1 is added at the start
        user.add_order(order_1)
        self.assertEqual(user.get_order_history(), [order_1, order_2, order_3, order_4])

        # Order 5 is added at the end
        user.add_order(order_5)
        self.assertEqual(
            user.get_order_history(), [order_1, order_2, order_3, order_4, order_5]
        )


class CardPaymentInfoTest(unittest.TestCase):
    PAYMENT_METHOD: str = "credit_card"
    CARD_NUMBER: str = "123456789012345"
    EXPIRY_DATE: str = "12/25"
    CCV: str = "123"

    # Successful init: Card number has 13 digits
    def test_card_number_13_digits(self) -> None:
        card_number = "1234567890123"
        self.assertEqual(
            CardPaymentInfo.from_opt_values(card_number, self.EXPIRY_DATE, self.CCV),
            CardPaymentInfo(
                self.PAYMENT_METHOD, card_number, self.EXPIRY_DATE, self.CCV
            ),
        )

    # Successful init: Card number has 19 digits
    def test_card_number_19_digits(self) -> None:
        card_number = "1234567890123456789"
        self.assertEqual(
            CardPaymentInfo.from_opt_values(card_number, self.EXPIRY_DATE, self.CCV),
            CardPaymentInfo(
                self.PAYMENT_METHOD, card_number, self.EXPIRY_DATE, self.CCV
            ),
        )

    # Successful init: CCV has 3 digits
    def test_ccv_3_digits(self) -> None:
        self.assertEqual(
            CardPaymentInfo.from_opt_values(self.CARD_NUMBER, self.EXPIRY_DATE, "123"),
            CardPaymentInfo(
                self.PAYMENT_METHOD, self.CARD_NUMBER, self.EXPIRY_DATE, "123"
            ),
        )

    # Successful init: CCV has 4 digits
    def test_ccv_4_digits(self) -> None:
        self.assertEqual(
            CardPaymentInfo.from_opt_values(self.CARD_NUMBER, self.EXPIRY_DATE, "1234"),
            CardPaymentInfo(
                self.PAYMENT_METHOD, self.CARD_NUMBER, self.EXPIRY_DATE, "1234"
            ),
        )

    # Failed init: Card number is None
    def test_card_number_none(self) -> None:
        self.assertEqual(
            CardPaymentInfo.from_opt_values(None, self.EXPIRY_DATE, self.CCV),
            "Please provide a valid card number",
        )

    # Failed init: Card number empty
    def test_card_number_empty(self) -> None:
        self.assertEqual(
            CardPaymentInfo.from_opt_values("", self.EXPIRY_DATE, self.CCV),
            "Please provide a valid card number",
        )

    # Failed init: Card number is not a digit string
    def test_card_number_not_digit_string(self) -> None:
        self.assertEqual(
            CardPaymentInfo.from_opt_values(
                "1234567890AAA", self.EXPIRY_DATE, self.CCV
            ),
            "Please provide a valid card number",
        )

    # Failed init: Card number has 12 digits
    def test_card_number_12_digits(self) -> None:
        self.assertEqual(
            CardPaymentInfo.from_opt_values("123456789012", self.EXPIRY_DATE, self.CCV),
            "Please provide a valid card number",
        )

    # Failed init: Card number has 20 digits
    def test_card_number_20_digits(self) -> None:
        self.assertEqual(
            CardPaymentInfo.from_opt_values(
                "12345678901234567890", self.EXPIRY_DATE, self.CCV
            ),
            "Please provide a valid card number",
        )

    # Failed init: Expiry date has invalid format
    def test_expiry_date_invalid(self) -> None:
        self.assertEqual(
            CardPaymentInfo.from_opt_values(self.CARD_NUMBER, "AB/CD", self.CCV),
            "Please provide a valid expiry date",
        )

    # Failed init: CCV is None
    def test_ccv_none(self) -> None:
        self.assertEqual(
            CardPaymentInfo.from_opt_values(self.CARD_NUMBER, self.EXPIRY_DATE, None),
            "Please provide a valid cvv",
        )

    # Failed init: CCV is empty
    def test_ccv_empty(self) -> None:
        self.assertEqual(
            CardPaymentInfo.from_opt_values(self.CARD_NUMBER, self.EXPIRY_DATE, ""),
            "Please provide a valid cvv",
        )

    # Failed init: CCV is not a digit string
    def test_ccv_not_digit_string(self) -> None:
        self.assertEqual(
            CardPaymentInfo.from_opt_values(self.CARD_NUMBER, self.EXPIRY_DATE, "AAA"),
            "Please provide a valid cvv",
        )

    # Failed init: CCV has 2 digits
    def test_ccv_2_digits(self) -> None:
        self.assertEqual(
            CardPaymentInfo.from_opt_values(self.CARD_NUMBER, self.EXPIRY_DATE, "12"),
            "Please provide a valid cvv",
        )

    # Failed init: CCV has 5 digits
    def test_ccv_5_digits(self) -> None:
        self.assertEqual(
            CardPaymentInfo.from_opt_values(
                self.CARD_NUMBER, self.EXPIRY_DATE, "12345"
            ),
            "Please provide a valid cvv",
        )


class PaypalPaymentInfoTest(unittest.TestCase):
    PAYMENT_METHOD: str = "paypal"
    EMAIL: str = "john.doe@gmail.com"

    # Successful init
    def test_success(self) -> None:
        self.assertEqual(
            PaypalPaymentInfo.from_opt_values(self.EMAIL),
            PaypalPaymentInfo(self.PAYMENT_METHOD, self.EMAIL),
        )

    # Failed init: Email is None
    def test_email_none(self) -> None:
        self.assertEqual(
            PaypalPaymentInfo.from_opt_values(None), "Please provide a valid email"
        )

    # Failed init: Email is empty
    def test_email_empty(self) -> None:
        self.assertEqual(
            PaypalPaymentInfo.from_opt_values(""), "Please provide a valid email"
        )

    # Failed init: Email does not contain @
    def test_email_no_at(self) -> None:
        self.assertEqual(
            PaypalPaymentInfo.from_opt_values("john.doe.com"),
            "Please provide a valid email",
        )


@patch("uuid.uuid4", return_value="some_uuid4")
class PaymentGatewayTest(unittest.TestCase):
    # Successful payment: Card number does not end with 1111
    def test_success_card(self, uuid4_mock: Mock) -> None:
        self.assertEqual(
            PaymentGateway.process_payment(
                CardPaymentInfo("credit_card", "123456789012345", "12/25", "123")
            ),
            PaymentResult("Payment processed successfully", "TXNsome_uuid4"),
        )

        uuid4_mock.assert_called_once()

    # Successful payment: Paypal payments always succeed
    def test_success_paypal(self, uuid4_mock: Mock) -> None:
        self.assertEqual(
            PaymentGateway.process_payment(
                CardPaymentInfo("credit_card", "123456789012345", "12/25", "123")
            ),
            PaymentResult("Payment processed successfully", "TXNsome_uuid4"),
        )

        uuid4_mock.assert_called_once()

    # Failed payment: Card number ends with 1111
    def test_success(self, uuid4_mock: Mock) -> None:
        self.assertEqual(
            PaymentGateway.process_payment(
                CardPaymentInfo("credit_card", "123456789011111", "12/25", "123")
            ),
            PaymentResult("Payment failed: Invalid card number", None),
        )

        uuid4_mock.assert_not_called()


class EmailServiceTest(unittest.TestCase):
    # Order confirmation is printed successfully
    @patch("datetime.datetime")
    @patch("builtins.print")
    def test_success(self, print_mock: Mock, datetime_mock: Mock) -> None:
        # Fix the order date
        dt = datetime.datetime(2025, 10, 10, 12, 5, 0)
        datetime_mock.now.return_value = dt
        order = Order(
            f"order-1",
            "john.doe@gmail.com",
            [
                CartItem(Book(f"title 1", "category 1", 10, "image 1")),
                CartItem(Book(f"title 2", "category 2", 20, "image 2"), 2),
            ],
            ShippingInfo(
                "John Doe",
                "john.doe@gmail.com",
                "Some address",
                "London",
                "Some ZIP",
            ),
            "credit_card",
            f"trans-1",
            50,
        )
        EmailService.send_order_confirmation("john.doe@gmail.com", order)

        print_mock.assert_has_calls(
            [
                call("\n=== EMAIL SENT ==="),
                call("To: john.doe@gmail.com"),
                call("Subject: Order Confirmation - Order #order-1"),
                call(f"Order Date: {dt}"),
                call("Total Amount: $50.00"),
                call("Items:"),
                call("  - title 1 x1 @ $10.00"),
                call("  - title 2 x2 @ $20.00"),
                call("Shipping Address: Some address"),
                call("==================\n"),
            ]
        )
