from dataclasses import asdict, dataclass
import heapq
import re
from typing import Any, Dict, List, Union, Optional
import datetime
import uuid


class Book:
    def __init__(self, title: str, category: str, price: float, image: str):
        if price <= 0:
            raise ValueError(f"Books must have a positive price. Received {price}")

        self.title = title
        self.category = category
        self.price = price
        self.image = image


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
        if quantity <= 0:
            self.remove_book(book_title)
        elif book_title in self.items:
            self.items[book_title].quantity = quantity

    def get_total_price(self) -> float:
        return sum(item.get_total_price() for item in self.items.values())

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

    @classmethod
    def from_opt_values(
        cls,
        name: Optional[str],
        email: Optional[str],
        address: Optional[str],
        city: Optional[str],
        zip_code: Optional[str],
    ) -> Union["ShippingInfo", str]:
        if not name:
            return "Please provide a valid name"
        if not email or "@" not in email:
            return "Please provide a valid email"
        # Depending on whether we're shipping internationally or not
        # we may know more about the address format (e.g. pgeocode)
        if not address:
            return "Please provide a valid address"
        if not city:
            return "Please provide a valid city"
        if not zip_code:
            return "Please provide a valid zip_code"

        return cls(
            name=name, email=email, address=address, city=city, zip_code=zip_code
        )


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

        self.order_id = order_id
        self.user_email = user_email
        self.items = items.copy()  # Copy of cart items
        self.shipping_info = shipping_info
        self.payment_method = payment_method
        self.transaction_id = transaction_id
        self.total_amount = total_amount
        self.order_date = datetime.datetime.now()
        self.status = "Confirmed"

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
        self.password = password
        self.name = name
        self.address = address
        self.orders: List[Order] = []
        heapq.heapify(self.orders)

    def add_order(self, order: Order):
        # Push Order objects sorted by order date
        heapq.heappush(self.orders, order)

    def get_order_history(self):
        return self.orders


@dataclass
class CardPaymentInfo:
    payment_method: str
    card_number: str
    expiry_date: str
    cvv: str

    @classmethod
    def from_opt_values(
        cls,
        payment_method: str,
        card_number: Optional[str],
        expiry_date: Optional[str],
        cvv: Optional[str],
    ) -> Union["CardPaymentInfo", str]:
        if (
            not card_number
            or not card_number.isdigit()
            or not (13 <= len(card_number) <= 19)
        ):
            return "Please provide a valid card number"

        # The month is between 01 and 12
        if not expiry_date or not re.match(r"^(0[1-9]|1[0-2])\/\d{2}$", expiry_date):
            return "Please provide a valid expiry date"

        if not cvv or not cvv.isdigit() or not (3 <= len(cvv) <= 4):
            return "Please provide a valid cvv"

        return CardPaymentInfo(
            payment_method=payment_method,
            card_number=card_number,
            expiry_date=expiry_date,
            cvv=cvv,
        )


@dataclass
class PaypalPaymentInfo:
    payment_method: str
    email: str

    @classmethod
    def from_opt_values(
        cls, payment_method: str, email: Optional[str]
    ) -> Union["PaypalPaymentInfo", str]:
        if not email or "@" not in email:
            return "Please provide a valid email"

        return PaypalPaymentInfo(payment_method, email)


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
