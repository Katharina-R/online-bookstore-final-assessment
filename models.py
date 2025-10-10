from dataclasses import asdict, dataclass
import re
from typing import Any, Dict, List, Union, Optional
import datetime
import bcrypt
import uuid
import bisect


class Book:
    def __init__(self, title: str, category: str, price: float, image: str):
        if not title:
            raise ValueError("Book title cannot be empty")

        if not category:
            raise ValueError("Book category cannot be empty")

        if price <= 0:
            raise ValueError(f"Books must have a positive price. Received {price}")

        if not image:
            raise ValueError("Book image cannot be enpty")

        self.title = title
        self.category = category
        self.price = price
        self.image = image

    # Without this printing books does not work as expected, e.g.
    # {'The Great Gatsby': CartItem(book=<models.Book object at 0x000002A8E185C910>, quantity=2)}
    def __repr__(self) -> str:
        return f"Book(title={self.title}, category={self.category}, price={self.price}, image={self.image})"


class CartItem:
    def __init__(self, book: Book, quantity: int = 1):
        if quantity <= 0:
            raise ValueError(
                f"Cart items must have a positive quantity. Received {quantity}"
            )

        self.book = book
        self.quantity = quantity

    def get_total_price(self):
        return self.book.price * self.quantity

    # Without this the equality check for List[CartItem] does not work as expected, e.g.
    # [<models.CartItem object at 0x000001FF2221BD10>] != [<models.CartItem object at 0x000001FF221BE7A0>]
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, CartItem):
            return False

        return self.book == other.book and self.quantity == other.quantity

    # Without this printing (for debugging) does not work as expected, e.g.
    # F{'The Great Gatsby': <models.CartItem object at 0x0000024CB636F570>}
    def __repr__(self) -> str:
        return f"CartItem(book={self.book}, quantity={self.quantity})"


class Cart:
    """
    A shopping cart class that holds book items and their quantities.

    The Cart uses a dictionary with book titles as keys for efficient lookups,
    allowing operations like adding, removing, and updating book quantities.

    Attributes:
        items (dict): Dictionary storing CartItem objects with book titles as keys.

    Methods:
        add_book(book, quantity=1): Add a book to the cart with specified quantity.
        remove_book(book_title): Remove a book from the cart by title.
        update_quantity(book_title, quantity): Update quantity of a book in the cart.
        get_total_price(): Calculate total price of all items in the cart.
        get_total_items(): Get the total count of all books in the cart.
        clear(): Remove all items from the cart.
        get_items(): Return a list of all CartItem objects in the cart.
        is_empty(): Check if the cart has no items.
    """

    def __init__(self):
        # Using dict with book title as key for easy lookup
        self.items: Dict[str, CartItem] = {}

    def add_book(self, book: Book, quantity: int = 1):
        if quantity <= 0:
            raise ValueError(
                f"Must provide a postivie quantity when adding books to cart. Received {quantity}"
            )

        if book.title in self.items:
            self.items[book.title].quantity += quantity
        else:
            self.items[book.title] = CartItem(book, quantity)

    def remove_book(self, book_title: str):
        if book_title in self.items:
            del self.items[book_title]

    def update_quantity(self, book_title: str, quantity: int):
        if book_title not in self.items:
            raise ValueError(
                f"Cannot update quantity for book '{book_title}' as it is not in cart"
            )
        if quantity <= 0:
            self.remove_book(book_title)
        elif book_title in self.items:
            self.items[book_title].quantity = quantity

    def get_total_price(self) -> float:
        # Round total price to the nearest number with 2 decimal points
        # (in case of floating point rounding errors)
        return round(sum(item.get_total_price() for item in self.items.values()), 2)

    def get_total_items(self):
        return sum(item.quantity for item in self.items.values())

    def clear(self):
        self.items = {}

    def get_items(self):
        return list(self.items.values())

    def is_empty(self):
        return len(self.items) == 0


@dataclass
class ShippingInfo:
    name: str
    email: str
    address: str
    city: str
    zip_code: str

    def __init__(
        self,
        name: Optional[str],
        email: Optional[str],
        address: Optional[str],
        city: Optional[str],
        zip_code: Optional[str],
    ) -> None:
        if not name:
            raise ValueError("Name cannot be empty")
        if not email:
            raise ValueError("Email cannot be empty")
        if "@" not in email:
            raise ValueError(f"Email must contain `@`. Received {email}")
        # Depending on whether we're shipping internationally or not
        # we may know more about the address format (e.g. pgeocode)
        if not address:
            raise ValueError("Address cannot be empty")
        if not city:
            raise ValueError("City cannot be empty")
        if not zip_code:
            raise ValueError("Zip code cannot be empty")

        self.name = name
        self.email = email
        self.address = address
        self.city = city
        self.zip_code = zip_code


class Order:
    """Order management class"""

    def __init__(
        self,
        order_id: str,
        user_email: str,
        items: List[CartItem],
        shipping_info: ShippingInfo,
        payment_method: str,
        transaction_id: str,
        total_amount: float,
    ):
        if not items:
            raise ValueError("Cannot create an order without items")

        self.order_id = order_id
        self.user_email = user_email
        self.items = items.copy()  # Copy of cart items
        self.shipping_info = shipping_info
        self.payment_method = payment_method
        self.transaction_id = transaction_id
        self.total_amount = total_amount
        self.order_date = datetime.datetime.now()
        self.status = "Confirmed"

    # Without this printing order does not work as expected, e.g.
    # <models.Order object at 0x000001EE0DCDDD10>
    def __repr__(self) -> str:
        return str(self.to_dict())

    # Without this python will check if two Order objects are identical
    # rather than checking if their content is equal
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Order):
            return False
        return self.to_dict() == other.to_dict()

    # This method allows us to store Order objects inside a heap
    def __lt__(self, other: "Order") -> bool:
        return self.order_date < other.order_date

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "user_email": self.user_email,
            "items": [
                {
                    "title": item.book.title,
                    "quantity": item.quantity,
                    "price": item.book.price,
                }
                for item in self.items
            ],
            "shipping_info": asdict(self.shipping_info),
            "total_amount": self.total_amount,
            "order_date": self.order_date.strftime("%Y-%m-%d %H:%M:%S"),
            "status": self.status,
        }


class User:
    """User account management class"""

    def __init__(self, email: str, password: str, name: str = "", address: str = ""):
        self.email = email
        self.password = User.hash_password(password)
        self.name = name
        self.address = address
        self.orders: List[Order] = []

    # Without this printing users does not work as expected, e.g. <models.User object at 0x0000019C59B47A80>
    def __repr__(self) -> str:
        return f"User(email={self.email}, password={self.password}, name={self.name}, address={self.address}, orders={self.orders})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return False

        # Don't compare the password as it is hashed with a random salt
        return (
            self.email == other.email
            and self.name == other.name
            and self.address == other.address
            and self.orders == other.orders
        )

    @classmethod
    def hash_password(cls, plain_password: str) -> bytes:
        salt = bcrypt.gensalt()
        # bcrypt requires bytes input, so encode string to bytes
        return bcrypt.hashpw(plain_password.encode("utf-8"), salt)

    def set_password(self, password: str) -> None:
        self.password = User.hash_password(password)

    def check_password(self, password: Optional[str]) -> bool:
        if not password:
            return False

        return bcrypt.checkpw(password.encode("utf-8"), self.password)

    def add_order(self, order: Order):
        # Push Order objects sorted by order date
        bisect.insort(self.orders, order)

    def get_order_history(self):
        return self.orders


@dataclass
class CardPaymentInfo:
    payment_method: str
    card_number: str
    expiry_date: str
    cvv: str

    def __init__(
        self, card_number: Optional[str], expiry_date: Optional[str], cvv: Optional[str]
    ) -> None:
        if (
            not card_number
            or not card_number.isdigit()
            or not (13 <= len(card_number) <= 19)
        ):
            raise ValueError("Please provide a valid card number")

        # The month is between 01 and 12
        if not expiry_date or not re.match(r"^(0[1-9]|1[0-2])\/\d{2}$", expiry_date):
            raise ValueError("Please provide a valid expiry date")

        if not cvv or not cvv.isdigit() or not (3 <= len(cvv) <= 4):
            raise ValueError("Please provide a valid cvv")

        self.payment_method = "credit_card"
        self.card_number = card_number
        self.expiry_date = expiry_date
        self.cvv = cvv


@dataclass
class PaypalPaymentInfo:
    payment_method: str
    email: str

    def __init__(self, email: Optional[str]) -> None:
        if not email or "@" not in email:
            raise ValueError("Please provide a valid email")

        self.payment_method = "paypal"
        self.email = email


@dataclass
class PaymentResult:
    message: str
    transaction_id: Optional[str]


class PaymentGateway:
    """Mock payment gateway for processing payments"""

    @staticmethod
    def process_payment(
        payment_info: Union[CardPaymentInfo, PaypalPaymentInfo],
    ) -> PaymentResult:
        """Mock payment processing - returns success/failure with mock logic"""
        if isinstance(payment_info, CardPaymentInfo):

            # Mock logic: cards ending in '1111' fail, others succeed
            if payment_info.card_number.endswith("1111"):
                return PaymentResult(
                    message="Payment failed: Invalid card number",
                    transaction_id=None,
                )
        else:
            # Mock logic: Do nothing for paypal transactions
            pass

        transaction_id = f"TXN{uuid.uuid4()}"

        return PaymentResult(
            message="Payment processed successfully",
            transaction_id=transaction_id,
        )


class EmailService:
    """Mock email service for sending order confirmations"""

    @staticmethod
    def send_order_confirmation(user_email: str, order: Order):
        """Mock email sending - just prints to console in this implementation"""
        print(f"\n=== EMAIL SENT ===")
        print(f"To: {user_email}")
        print(f"Subject: Order Confirmation - Order #{order.order_id}")
        print(f"Order Date: {order.order_date}")
        print(f"Total Amount: ${order.total_amount:.2f}")
        print(f"Items:")
        for item in order.items:
            print(f"  - {item.book.title} x{item.quantity} @ ${item.book.price:.2f}")
        print(f"Shipping Address: {order.shipping_info.address}")
        print(f"==================\n")

        return True
