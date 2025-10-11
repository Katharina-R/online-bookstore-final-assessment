from typing import Dict
import unittest
from unittest.mock import Mock, call, patch

from app import (
    app,
    checkout,
    clear_cart,
    index,
    BOOKS,
    add_to_cart,
    logout,
    update_profile,
    remove_from_cart,
    cart,
    users,
    orders,
    account,
    process_checkout,
    register,
    update_cart,
    order_confirmation,
    login,
    view_cart,
    get_current_user,
)
from flask import session
from models import (
    Book,
    User,
    PaymentResult,
    CardPaymentInfo,
    PaypalPaymentInfo,
    Order,
    CartItem,
    ShippingInfo,
)

BOOK: Book = Book(
    "The Great Gatsby",
    "Fiction",
    10.99,
    "/images/books/the_great_gatsby.jpg",
)


# Add 7 versions of "The Great Gatsby" to the cart if it is empty
def add_the_great_gatsby() -> None:
    for item in cart.get_items():
        if item.book == BOOK:
            return
    cart.add_book(BOOK, 7)


NAME: str = "John Doe"
EMAIL: str = "john.doe@gmail.com"
ADDRESS: str = "Waldegrave Rd, Twickenham TW1 4SX"
PASSWORD: str = "12345"
USER: User = User(EMAIL, PASSWORD, NAME, ADDRESS)
SHIPPING_INFO: ShippingInfo = ShippingInfo(NAME, EMAIL, ADDRESS, "London", "Some ZIP")


class GetCurrentUserTest(unittest.TestCase):
    # Success: Current user was found
    def test_success(self) -> None:
        with app.test_request_context():
            session["user_email"] = EMAIL
            users[EMAIL] = USER
            self.assertEqual(get_current_user(), USER)

    # Failure: User email is not in sessions
    def test_email_not_in_session(self) -> None:
        with app.test_request_context():
            session = {}  # type: ignore
            users[EMAIL] = USER
            self.assertEqual(get_current_user(), None)

    # Failure: There is no user with this email
    def test_email_no_in_users(self) -> None:
        with app.test_request_context():
            session["user_email"] = EMAIL
            self.assertEqual(get_current_user(), None)


@patch("app.get_current_user")
@patch("app.render_template", return_value=None)
class IndexTest(unittest.TestCase):
    # Success: Current user does not exist
    def test_no_current_user(
        self, render_template_mock: Mock, get_current_user_mock: Mock
    ) -> None:
        get_current_user_mock.return_value = None
        with app.test_request_context():
            index()

        render_template_mock.assert_called_once_with(
            "index.html", books=list(BOOKS.values()), cart=cart, current_user=None
        )

    # Success: Current user exists
    def test_current_user(
        self, render_template_mock: Mock, get_current_user_mock: Mock
    ) -> None:
        get_current_user_mock.return_value = USER
        with app.test_request_context():
            index()

        render_template_mock.assert_called_once_with(
            "index.html", books=list(BOOKS.values()), cart=cart, current_user=USER
        )


@patch("app.redirect", return_value=None)
@patch("app.url_for", return_value="url")
@patch("app.flash", return_value=None)
class AddToCartTest(unittest.TestCase):
    # Failure: Book title is not in form
    def test_no_title(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        with app.test_request_context("/add-to-cart", method="POST", data={}):
            add_to_cart()

        flash_mock.assert_called_once_with("Book 'None' not found!", "error")
        url_for_mock.assert_called_once_with("index")
        redirect_mock.assert_called_once_with("url")

    # Failure: Book title is not in BOOKS
    def test_unknown_title(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/add-to-cart", method="POST", data={"title": "Unknown_title"}
        ):
            add_to_cart()

        flash_mock.assert_called_once_with("Book 'Unknown_title' not found!", "error")
        url_for_mock.assert_called_once_with("index")
        redirect_mock.assert_called_once_with("url")

    # Failure: Quantity cannot be converted to an int
    def test_invalid_quantity(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/add-to-cart",
            method="POST",
            data={"title": "The Great Gatsby", "quantity": "oops"},
        ):
            add_to_cart()

        flash_mock.assert_called_once_with("Received non-numeric quantity oops")
        url_for_mock.assert_called_once_with("view_cart")
        redirect_mock.assert_called_once_with("url")

    # Failure: Quantity is provided and negative
    def test_quantity_negative(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/add-to-cart",
            method="POST",
            data={"title": "The Great Gatsby", "quantity": -12},
        ):
            add_to_cart()

        flash_mock.assert_called_once_with(
            "Failed to add book to cart: Must provide a postivie quantity when adding books to cart. Received -12",
            "error",
        )
        url_for_mock.assert_called_once_with("index")
        redirect_mock.assert_called_once_with("url")

    # Failure: Quantity is provided and zero
    def test_quantity_zero(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/add-to-cart",
            method="POST",
            data={"title": "The Great Gatsby", "quantity": 0},
        ):
            add_to_cart()

        flash_mock.assert_called_once_with(
            "Failed to add book to cart: Must provide a postivie quantity when adding books to cart. Received 0",
            "error",
        )
        url_for_mock.assert_called_once_with("index")
        redirect_mock.assert_called_once_with("url")

    # Success: Quantity is provided and positive
    def test_quantity_positive(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/add-to-cart",
            method="POST",
            data={"title": "The Great Gatsby", "quantity": 42},
        ):
            add_to_cart()

        flash_mock.assert_called_once_with(
            'Added 42 "The Great Gatsby" to cart!', "success"
        )
        url_for_mock.assert_called_once_with("index")
        redirect_mock.assert_called_once_with("url")

    # Success: Quantity is not provided
    def test_quantity_missing(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/add-to-cart", method="POST", data={"title": "The Great Gatsby"}
        ):
            add_to_cart()

        flash_mock.assert_called_once_with(
            'Added 1 "The Great Gatsby" to cart!', "success"
        )
        url_for_mock.assert_called_once_with("index")
        redirect_mock.assert_called_once_with("url")


@patch("app.redirect", return_value=None)
@patch("app.url_for", return_value="url")
@patch("app.flash", return_value=None)
class RemoveFromCartTest(unittest.TestCase):
    # Failure: Book title is not in form
    def test_no_title(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/remove-from-cart",
            method="POST",
            data={},
        ):
            remove_from_cart()

        flash_mock.assert_called_once_with(
            "Cannot remove book with unknown book_title", "error"
        )
        url_for_mock.assert_called_once_with("view_cart")
        redirect_mock.assert_called_once_with("url")

    # Success: Deleting book from empty cart
    def test_no_books(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/remove-from-cart",
            method="POST",
            data={"title": "The Great Gatsby"},
        ):
            remove_from_cart()

        flash_mock.assert_called_once_with(
            'Removed "The Great Gatsby" from cart!', "success"
        )
        url_for_mock.assert_called_once_with("view_cart")
        redirect_mock.assert_called_once_with("url")

    # Success: Deleting book that is not in cart
    def test_book_not_in_cart(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        add_the_great_gatsby()

        with app.test_request_context(
            "/remove-from-cart",
            method="POST",
            data={"title": "1984"},
        ):
            remove_from_cart()

        flash_mock.assert_called_once_with('Removed "1984" from cart!', "success")
        url_for_mock.assert_called_once_with("view_cart")
        redirect_mock.assert_called_once_with("url")

    # Success: Deleting book that is in cart
    def test_book_in_cart(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        add_the_great_gatsby()

        with app.test_request_context(
            "/remove-from-cart",
            method="POST",
            data={"title": "The Great Gatsby"},
        ):
            remove_from_cart()

        flash_mock.assert_called_once_with(
            'Removed "The Great Gatsby" from cart!', "success"
        )
        url_for_mock.assert_called_once_with("view_cart")
        redirect_mock.assert_called_once_with("url")


@patch("app.redirect", return_value=None)
@patch("app.url_for", return_value="url")
@patch("app.flash", return_value=None)
class UpdateCartTest(unittest.TestCase):
    # Failure: Book title is not in form
    def test_no_title(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/remove-from-cart",
            method="POST",
            data={},
        ):
            update_cart()

        flash_mock.assert_called_once_with(
            "Cannot update quantity for unknown book_title", "error"
        )
        url_for_mock.assert_called_once_with("view_cart")
        redirect_mock.assert_called_once_with("url")

    # Failure: Book title is empty
    def test_empty_title(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/remove-from-cart",
            method="POST",
            data={"title": ""},
        ):
            update_cart()

        flash_mock.assert_called_once_with(
            "Cannot update quantity for unknown book_title", "error"
        )
        url_for_mock.assert_called_once_with("view_cart")
        redirect_mock.assert_called_once_with("url")

    # Failure: Update book that is not in cart
    def test_empty_cart(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/remove-from-cart",
            method="POST",
            data={"title": "1984"},
        ):
            update_cart()

        flash_mock.assert_called_once_with(
            "Failed to udpate quantity: Cannot update quantity for book '1984' as it is not in cart",
            "error",
        )
        url_for_mock.assert_called_once_with("view_cart")
        redirect_mock.assert_called_once_with("url")

    # Success: Quantity is in form and negative
    def test_quantity_negative(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        add_the_great_gatsby()

        with app.test_request_context(
            "/remove-from-cart",
            method="POST",
            data={"title": "The Great Gatsby", "quantity": -1},
        ):
            update_cart()

        flash_mock.assert_called_once_with(
            'Removed "The Great Gatsby" from cart!',
            "success",
        )
        url_for_mock.assert_called_once_with("view_cart")
        redirect_mock.assert_called_once_with("url")

    # Success: Quantity is in form and zero
    def test_remove_from_cart(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        add_the_great_gatsby()

        with app.test_request_context(
            "/remove-from-cart",
            method="POST",
            data={"title": "The Great Gatsby", "quantity": 0},
        ):
            update_cart()

        flash_mock.assert_called_once_with(
            'Removed "The Great Gatsby" from cart!',
            "success",
        )
        url_for_mock.assert_called_once_with("view_cart")
        redirect_mock.assert_called_once_with("url")

    # Success: Quantity is decreased
    def test_decrease_quantity(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        add_the_great_gatsby()

        with app.test_request_context(
            "/remove-from-cart",
            method="POST",
            data={"title": "The Great Gatsby"},
        ):
            update_cart()

        flash_mock.assert_called_once_with(
            'Updated "The Great Gatsby" quantity to 1!', "success"
        )
        url_for_mock.assert_called_once_with("view_cart")
        redirect_mock.assert_called_once_with("url")

    # Success: Quantity is increased
    def test_increase_quantity(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        add_the_great_gatsby()

        with app.test_request_context(
            "/remove-from-cart",
            method="POST",
            data={"title": "The Great Gatsby", "quantity": 8},
        ):
            update_cart()

        flash_mock.assert_called_once_with(
            'Updated "The Great Gatsby" quantity to 8!', "success"
        )
        url_for_mock.assert_called_once_with("view_cart")
        redirect_mock.assert_called_once_with("url")

    # Success: Quantity is not in form
    def test_quantity_not_in_form(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        add_the_great_gatsby()

        with app.test_request_context(
            "/remove-from-cart",
            method="POST",
            data={"title": "The Great Gatsby"},
        ):
            update_cart()

        flash_mock.assert_called_once_with(
            'Updated "The Great Gatsby" quantity to 1!', "success"
        )
        url_for_mock.assert_called_once_with("view_cart")
        redirect_mock.assert_called_once_with("url")


@patch("app.get_current_user")
@patch("app.render_template", return_value=None)
class ViewCartTest(unittest.TestCase):
    # Success: Current user is not set
    def test_current_user_not_set(
        self, render_template_mock: Mock, get_current_user_mock: Mock
    ) -> None:
        get_current_user_mock.return_value = None

        with app.test_request_context():
            view_cart()

        render_template_mock.assert_called_once_with(
            "cart.html", cart=cart, current_user=None
        )

    # Success: Current user is set
    def test_current_user_set(
        self, render_template_mock: Mock, get_current_user_mock: Mock
    ) -> None:
        get_current_user_mock.return_value = USER

        with app.test_request_context():
            view_cart()

        render_template_mock.assert_called_once_with(
            "cart.html", cart=cart, current_user=USER
        )


@patch("app.redirect", return_value=None)
@patch("app.url_for", return_value="url")
@patch("app.flash", return_value=None)
class ClearCartTest(unittest.TestCase):
    # Success: Current user is not set
    def test_success(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        with app.test_request_context():
            clear_cart()

        self.assertEqual(cart.get_items(), [])
        flash_mock.assert_called_once_with("Cart cleared!", "success")
        url_for_mock.assert_called_once_with("view_cart")
        redirect_mock.assert_called_once_with("url")


@patch("app.redirect", return_value=None)
@patch("app.url_for", return_value="url")
@patch("app.flash", return_value=None)
class CheckoutTest(unittest.TestCase):
    # Failure: Cart is empty
    def test_empty_cart(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        with app.test_request_context():
            cart.clear()
            checkout()

        flash_mock.assert_called_once_with("Your cart is empty!", "error")
        url_for_mock.assert_called_once_with("index")
        redirect_mock.assert_called_once_with("url")

    # Success: Cart has items & no current user is set
    @patch("app.get_current_user")
    @patch("app.render_template", return_value=None)
    def test_full_cart_no_user(
        self,
        render_template_mock: Mock,
        get_current_user_mock: Mock,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        with app.test_request_context():
            get_current_user_mock.return_value = None

            add_the_great_gatsby()
            checkout()

        render_template_mock.assert_called_once_with(
            "checkout.html",
            cart=cart,
            total_price=cart.get_total_price(),
            current_user=None,
        )
        flash_mock.assert_not_called()
        url_for_mock.assert_not_called()
        redirect_mock.assert_not_called()

    # Success: Cart has items & a current user is set
    @patch("app.get_current_user")
    @patch("app.render_template", return_value=None)
    def test_full_cart_user(
        self,
        render_template_mock: Mock,
        get_current_user_mock: Mock,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
    ) -> None:
        with app.test_request_context():
            get_current_user_mock.return_value = USER

            add_the_great_gatsby()
            checkout()

        render_template_mock.assert_called_once_with(
            "checkout.html",
            cart=cart,
            total_price=cart.get_total_price(),
            current_user=USER,
        )
        flash_mock.assert_not_called()
        url_for_mock.assert_not_called()
        redirect_mock.assert_not_called()


@patch("models.EmailService.send_order_confirmation")
@patch("uuid.uuid4", return_value="1234567890")
@patch(
    "models.PaymentGateway.process_payment",
    return_value=PaymentResult("Payment processed successfully", "TXN12345"),
)
@patch("app.redirect", return_value=None)
@patch("app.url_for", return_value="url")
@patch("app.flash", return_value=None)
class ProcessCheckoutTest(unittest.TestCase):
    CREDIT_CARD_INFO: CardPaymentInfo = CardPaymentInfo(
        "123456789012345", "12/25", "123"
    )
    PAYPAL_INFO: PaypalPaymentInfo = PaypalPaymentInfo(EMAIL)
    ORDER_ID: str = "12345678"
    TRANSACTION_ID: str = "TXN12345"

    def get_data(
        self,
        discount_code: str = "",
        payment_method: str = "credit_card",
        has_credit_card_info: bool = True,
        has_paypal_info: bool = True,
    ) -> Dict[str, str]:
        data = {
            "name": NAME,
            "email": EMAIL,
            "address": ADDRESS,
            "city": "London",
            "zip_code": "Some ZIP",
            "discount_code": discount_code,
            "payment_method": payment_method,
        }

        if has_credit_card_info:
            data["card_number"] = "123456789012345"
            data["expiry_date"] = "12/25"
            data["cvv"] = "123"

        if has_paypal_info:
            data["paypal_email"] = EMAIL

        return data

    def get_order(self, payment_method: str, discount: float) -> Order:
        return Order(
            self.ORDER_ID,
            EMAIL,
            [CartItem(BOOK, 7)],
            SHIPPING_INFO,
            payment_method,
            self.TRANSACTION_ID,
            total_amount=round(76.93 * (1 - discount), 2),
        )

    # Failure: Cart is empty
    def test_empty_cart(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        process_payment_mock: Mock,
        uuid4_mock: Mock,
        send_order_confirmation_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/process-checkout",
            method="POST",
            data={},
        ):
            cart.clear()
            process_checkout()

        flash_mock.assert_called_once_with("Your cart is empty!", "error")
        url_for_mock.assert_called_once_with("index")
        redirect_mock.assert_called_once_with("url")
        process_payment_mock.assert_not_called()
        uuid4_mock.assert_not_called()
        send_order_confirmation_mock.assert_not_called()

    # Failure: Shipping information is invalid
    def test_invalid_shipping_information(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        process_payment_mock: Mock,
        uuid4_mock: Mock,
        send_order_confirmation_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/process-checkout",
            method="POST",
            data={},
        ):
            add_the_great_gatsby()
            process_checkout()

        flash_mock.assert_called_once_with("Name cannot be empty", "error")
        url_for_mock.assert_called_once_with("checkout")
        redirect_mock.assert_called_once_with("url")
        process_payment_mock.assert_not_called()
        uuid4_mock.assert_not_called()
        send_order_confirmation_mock.assert_not_called()

    # Failure: Invalid discount code
    def test_invalid_discount_code(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        process_payment_mock: Mock,
        uuid4_mock: Mock,
        send_order_confirmation_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/process-checkout",
            method="POST",
            data=self.get_data(discount_code="oops"),
        ):
            add_the_great_gatsby()
            process_checkout()

        flash_mock.assert_called_once_with("Invalid discount code", "error")
        url_for_mock.assert_called_once_with("checkout")
        redirect_mock.assert_called_once_with("url")
        process_payment_mock.assert_not_called()
        uuid4_mock.assert_not_called()
        send_order_confirmation_mock.assert_not_called()

    # Failure: Invalid payment method
    def test_invalid_payment_method(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        process_payment_mock: Mock,
        uuid4_mock: Mock,
        send_order_confirmation_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/process-checkout",
            method="POST",
            data=self.get_data(payment_method="oops"),
        ):
            add_the_great_gatsby()
            process_checkout()

        flash_mock.assert_called_once_with(
            "Received invalid payment method oops", "error"
        )
        url_for_mock.assert_called_once_with("checkout")
        redirect_mock.assert_called_once_with("url")
        process_payment_mock.assert_not_called()
        uuid4_mock.assert_not_called()
        send_order_confirmation_mock.assert_not_called()

    # Failure: Invalid card payment info
    def test_invalid_card_payment_info(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        process_payment_mock: Mock,
        uuid4_mock: Mock,
        send_order_confirmation_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/process-checkout",
            method="POST",
            data=self.get_data(
                payment_method="credit_card", has_credit_card_info=False
            ),
        ):
            add_the_great_gatsby()
            process_checkout()

        flash_mock.assert_called_with("Please provide a valid card number", "error")
        url_for_mock.assert_called_once_with("checkout")
        redirect_mock.assert_called_once_with("url")
        process_payment_mock.assert_not_called()
        uuid4_mock.assert_not_called()
        send_order_confirmation_mock.assert_not_called()

    # Failure: Invalid paypal payment info
    def test_invalid_paypal_payment_info(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        process_payment_mock: Mock,
        uuid4_mock: Mock,
        send_order_confirmation_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/process-checkout",
            method="POST",
            data=self.get_data(payment_method="paypal", has_paypal_info=False),
        ):
            add_the_great_gatsby()
            process_checkout()

        flash_mock.assert_called_with("Please provide a valid email", "error")
        url_for_mock.assert_called_once_with("checkout")
        redirect_mock.assert_called_once_with("url")
        process_payment_mock.assert_not_called()
        uuid4_mock.assert_not_called()
        send_order_confirmation_mock.assert_not_called()

    # Failure: Payment result has no transaction ID
    def test_no_transaction_id(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        process_payment_mock: Mock,
        uuid4_mock: Mock,
        send_order_confirmation_mock: Mock,
    ) -> None:
        process_payment_mock.return_value = PaymentResult(
            "Payment failed: Invalid card number", None
        )

        with app.test_request_context(
            "/process-checkout",
            method="POST",
            data=self.get_data(payment_method="paypal", has_paypal_info=False),
        ):
            add_the_great_gatsby()
            process_checkout()

        flash_mock.assert_called_with("Please provide a valid email", "error")
        url_for_mock.assert_called_once_with("checkout")
        redirect_mock.assert_called_once_with("url")
        process_payment_mock.assert_not_called()
        uuid4_mock.assert_not_called()
        send_order_confirmation_mock.assert_not_called()

    # Success: Credit card checkout without discount
    def test_no_discount_code(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        process_payment_mock: Mock,
        uuid4_mock: Mock,
        send_order_confirmation_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/process-checkout",
            method="POST",
            data=self.get_data(payment_method="credit_card", discount_code=""),
        ):
            add_the_great_gatsby()
            process_checkout()
            self.assertEqual(session["last_order_id"], self.ORDER_ID)

        flash_mock.assert_called_once_with(
            "Payment successful! Your order has been confirmed.", "success"
        )
        url_for_mock.assert_called_once_with(
            "order_confirmation", order_id=self.ORDER_ID
        )
        redirect_mock.assert_called_once_with("url")
        process_payment_mock.assert_called_with(self.CREDIT_CARD_INFO)
        uuid4_mock.assert_called_once_with()
        order = self.get_order("credit_card", 0)
        self.assertEqual(orders[self.ORDER_ID], order)
        send_order_confirmation_mock.assert_called_once_with(EMAIL, order)

    # Success: Credit card checkout with 10% discount
    # The discount has invalid capitalization and trailing spaces
    def test_10_percent_discount_code(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        process_payment_mock: Mock,
        uuid4_mock: Mock,
        send_order_confirmation_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/process-checkout",
            method="POST",
            data=self.get_data(
                payment_method="credit_card", discount_code="Save10    "
            ),
        ):
            add_the_great_gatsby()
            process_checkout()
            self.assertEqual(session["last_order_id"], self.ORDER_ID)

        flash_mock.assert_has_calls(
            [
                call("Discount applied! You saved $7.69", "success"),
                call("Payment successful! Your order has been confirmed.", "success"),
            ]
        )
        url_for_mock.assert_called_once_with(
            "order_confirmation", order_id=self.ORDER_ID
        )
        redirect_mock.assert_called_once_with("url")
        process_payment_mock.assert_called_with(self.CREDIT_CARD_INFO)
        uuid4_mock.assert_called_once_with()
        order = self.get_order("credit_card", 0.1)
        self.assertEqual(orders[self.ORDER_ID], order)
        send_order_confirmation_mock.assert_called_once_with(EMAIL, order)

    # Success: Credit card checkout with 20% discount
    # The discount has invalid capitalization and leading spaces
    def test_20_percent_discount_code(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        process_payment_mock: Mock,
        uuid4_mock: Mock,
        send_order_confirmation_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/process-checkout",
            method="POST",
            data=self.get_data(
                payment_method="credit_card", discount_code="    welcome20"
            ),
        ):
            add_the_great_gatsby()
            process_checkout()
            self.assertEqual(session["last_order_id"], self.ORDER_ID)

        flash_mock.assert_has_calls(
            [
                call("Welcome discount applied! You saved $15.39", "success"),
                call("Payment successful! Your order has been confirmed.", "success"),
            ]
        )
        url_for_mock.assert_called_once_with(
            "order_confirmation", order_id=self.ORDER_ID
        )
        redirect_mock.assert_called_once_with("url")
        process_payment_mock.assert_called_with(self.CREDIT_CARD_INFO)
        uuid4_mock.assert_called_once_with()
        order = self.get_order("credit_card", 0.2)
        self.assertEqual(orders[self.ORDER_ID], order)
        send_order_confirmation_mock.assert_called_once_with(EMAIL, order)

    # Success: Paypal checkout with 20% discount
    # The discount has correct capitalization and no extra spaces
    def test_paypal_payment(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        process_payment_mock: Mock,
        uuid4_mock: Mock,
        send_order_confirmation_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/process-checkout",
            method="POST",
            data=self.get_data(payment_method="paypal", discount_code="WELCOME20"),
        ):
            add_the_great_gatsby()
            process_checkout()
            self.assertEqual(session["last_order_id"], self.ORDER_ID)

        flash_mock.assert_has_calls(
            [
                call("Welcome discount applied! You saved $15.39", "success"),
                call("Payment successful! Your order has been confirmed.", "success"),
            ]
        )
        url_for_mock.assert_called_once_with(
            "order_confirmation", order_id=self.ORDER_ID
        )
        redirect_mock.assert_called_once_with("url")
        process_payment_mock.assert_called_with(self.PAYPAL_INFO)
        uuid4_mock.assert_called_once_with()
        order = self.get_order("paypal", 0.2)
        self.assertEqual(orders[self.ORDER_ID], order)
        send_order_confirmation_mock.assert_called_once_with(EMAIL, order)


@patch("app.render_template")
@patch("app.get_current_user", return_value=None)
@patch("app.redirect", return_value=None)
@patch("app.url_for", return_value="url")
@patch("app.flash", return_value=None)
class OrderConfirmationTest(unittest.TestCase):
    ORDER_ID: str = "oops"
    ORDER: Order = Order(
        ORDER_ID,
        EMAIL,
        [CartItem(BOOK, 7)],
        SHIPPING_INFO,
        "credit_card",
        "TNX123",
        total_amount=12.34,
    )

    # Failure: No order with this order ID exists
    def test_no_order(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        get_current_user_mock: Mock,
        render_template_mock: Mock,
    ):
        with app.test_request_context(f"/order-confirmation/{self.ORDER_ID}"):
            order_confirmation(self.ORDER_ID)

        flash_mock.assert_called_once_with("Order not found", "error")
        url_for_mock.assert_called_once_with("index")
        redirect_mock.assert_called_once_with("url")
        get_current_user_mock.assert_not_called()
        render_template_mock.assert_not_called()

    # Success: There is a current user
    def test_user(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        get_current_user_mock: Mock,
        render_template_mock: Mock,
    ):
        get_current_user_mock.return_value = USER

        orders[self.ORDER_ID] = self.ORDER
        with app.test_request_context(f"/order-confirmation/{self.ORDER_ID}"):
            order_confirmation(self.ORDER_ID)
        orders.clear()

        flash_mock.assert_not_called()
        url_for_mock.assert_not_called()
        redirect_mock.assert_not_called()
        get_current_user_mock.assert_called_once_with()
        render_template_mock.assert_called_once_with(
            "order_confirmation.html", order=self.ORDER, current_user=USER
        )

    # Success: There is no current user
    def test_no_user(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        get_current_user_mock: Mock,
        render_template_mock: Mock,
    ):
        orders[self.ORDER_ID] = self.ORDER
        with app.test_request_context(f"/order-confirmation/{self.ORDER_ID}"):
            order_confirmation(self.ORDER_ID)
        orders.clear()

        flash_mock.assert_not_called()
        url_for_mock.assert_not_called()
        redirect_mock.assert_not_called()
        get_current_user_mock.assert_called_once_with()
        render_template_mock.assert_called_once_with(
            "order_confirmation.html", order=self.ORDER, current_user=None
        )


@patch("app.render_template")
@patch("app.redirect", return_value=None)
@patch("app.url_for", return_value="url")
@patch("app.flash", return_value=None)
class RegisterTest(unittest.TestCase):
    def get_data(
        self,
        email: str = EMAIL,
        password: str = "password",
        name: str = NAME,
        address: str = ADDRESS,
    ) -> Dict[str, str]:
        return {"email": email, "password": password, "name": name, "address": address}

    # Failure: Email is empty
    def test_empty_email(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        render_template_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/register", method="POST", data=self.get_data(email="")
        ):
            register()

        flash_mock.assert_called_once_with(
            "Please fill in all required fields", "error"
        )
        url_for_mock.assert_not_called()
        redirect_mock.assert_not_called()
        render_template_mock.assert_called_once_with("register.html")

    # Failure: Password is empty
    def test_empty_password(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        render_template_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/register", method="POST", data=self.get_data(password="")
        ):
            register()

        flash_mock.assert_called_once_with(
            "Please fill in all required fields", "error"
        )
        url_for_mock.assert_not_called()
        redirect_mock.assert_not_called()
        render_template_mock.assert_called_once_with("register.html")

    # Failure: Name is empty
    def test_empty_name(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        render_template_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/register", method="POST", data=self.get_data(name="")
        ):
            register()

        flash_mock.assert_called_once_with(
            "Please fill in all required fields", "error"
        )
        url_for_mock.assert_not_called()
        redirect_mock.assert_not_called()
        render_template_mock.assert_called_once_with("register.html")

    # Failure: Address is empty
    def test_empty_address(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        render_template_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/register", method="POST", data=self.get_data(address="")
        ):
            register()

        flash_mock.assert_called_once_with(
            "Please fill in all required fields", "error"
        )
        url_for_mock.assert_not_called()
        redirect_mock.assert_not_called()
        render_template_mock.assert_called_once_with("register.html")

    # Failure: A user with this email already exists
    def test_email_already_exists(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        render_template_mock: Mock,
    ) -> None:
        with app.test_request_context("/register", method="POST", data=self.get_data()):
            register()

        flash_mock.assert_called_once_with(
            "An account with this email already exists", "error"
        )
        url_for_mock.assert_not_called()
        redirect_mock.assert_not_called()
        render_template_mock.assert_called_once_with("register.html")

    # Success: GET request
    def test_get(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        render_template_mock: Mock,
    ) -> None:
        with app.test_request_context("/register", method="GET", data={}):
            register()

        flash_mock.assert_not_called()
        url_for_mock.assert_not_called()
        redirect_mock.assert_not_called()
        render_template_mock.assert_called_once_with("register.html")

    # Success: POST request
    # Email address has incorrect capitalization and extra spaces
    def test_post(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        render_template_mock: Mock,
    ) -> None:
        email = "john.doe2@gmail.com"

        with app.test_request_context(
            "/register",
            method="POST",
            data=self.get_data(email="   JOHN.doe2@Gmail.com  "),
        ):
            register()
            self.assertEqual(session["user_email"], email)

        self.assertEqual(
            users[email],
            User(email, "password", NAME, ADDRESS),
        )

        flash_mock.assert_called_once_with(
            "Account created successfully! You are now logged in.", "success"
        )
        url_for_mock.assert_called_once_with("index")
        redirect_mock.assert_called_once_with("url")
        render_template_mock.assert_not_called()


@patch("app.render_template")
@patch("app.redirect", return_value=None)
@patch("app.url_for", return_value="url")
@patch("app.flash", return_value=None)
class LoginTest(unittest.TestCase):
    # Failure: Email is empty
    def test_empty_email(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        render_template_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/login",
            method="POST",
            data={},
        ):
            login()

        flash_mock.assert_called_once_with("Please enter an email", "error")
        url_for_mock.assert_not_called()
        redirect_mock.assert_not_called()
        render_template_mock.assert_called_once_with("login.html")

    # Failure: No user exists for this email
    def test_no_user_for_email(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        render_template_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/login",
            method="POST",
            data={"email": "jane.doe@gmail.com", "password": PASSWORD},
        ):
            login()

        flash_mock.assert_called_once_with("Invalid email or password", "error")
        url_for_mock.assert_not_called()
        redirect_mock.assert_not_called()
        render_template_mock.assert_called_once_with("login.html")

    # Failure: Password is incorrect
    def test_incorrect_password(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        render_template_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/login",
            method="POST",
            data={"email": EMAIL, "password": "super secret password"},
        ):
            login()

        flash_mock.assert_called_once_with("Invalid email or password", "error")
        url_for_mock.assert_not_called()
        redirect_mock.assert_not_called()
        render_template_mock.assert_called_once_with("login.html")

    # Failure: GET method
    def test_get(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        render_template_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/login",
            method="GET",
            data={},
        ):
            login()

        flash_mock.assert_not_called()
        url_for_mock.assert_not_called()
        redirect_mock.assert_not_called()
        render_template_mock.assert_called_once_with("login.html")

    # Failure: POST method
    def test_post(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        render_template_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/login",
            method="POST",
            data={"email": EMAIL, "password": PASSWORD},
        ):
            login()
            self.assertEqual(session["user_email"], EMAIL)

        flash_mock.assert_called_once_with("Logged in successfully!", "success")
        url_for_mock.assert_called_once_with("index")
        redirect_mock.assert_called_once_with("url")
        render_template_mock.assert_not_called()


@patch("app.redirect", return_value=None)
@patch("app.url_for", return_value="url")
@patch("app.flash", return_value=None)
class LogoutTest(unittest.TestCase):
    # Success: User email does not exist in sessions
    def test_user_email_not_exists(
        self, flash_mock: Mock, url_for_mock: Mock, redirect_mock: Mock
    ) -> None:
        with app.test_request_context("/logout"):
            session.clear()
            logout()
            self.assertTrue(EMAIL not in session)

        flash_mock.assert_called_once_with("Logged out successfully!", "success")
        url_for_mock.assert_called_once_with("index")
        redirect_mock.assert_called_once_with("url")

    # Success: User email exists in sessions
    def test_user_email_exists(
        self, flash_mock: Mock, url_for_mock: Mock, redirect_mock: Mock
    ) -> None:
        with app.test_request_context("/logout"):
            session["user_email"] = EMAIL
            logout()
            self.assertTrue(EMAIL not in session)

        flash_mock.assert_called_once_with("Logged out successfully!", "success")
        url_for_mock.assert_called_once_with("index")
        redirect_mock.assert_called_once_with("url")


@patch("app.get_current_user")
@patch("app.render_template")
@patch("app.redirect", return_value=None)
@patch("app.url_for", return_value="url")
@patch("app.flash", return_value=None)
class AccountTest(unittest.TestCase):
    # Failure: No user email in sessions
    def test_no_user_email(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        render_template_mock: Mock,
        get_current_user_mock: Mock,
    ) -> None:
        with app.test_request_context("/account"):
            session.clear()
            account()

        get_current_user_mock.assert_not_called()
        flash_mock.assert_called_once_with(
            "Please log in to access this page.", "error"
        )
        url_for_mock.assert_called_once_with("login")
        redirect_mock.assert_called_once_with("url")
        render_template_mock.assert_not_called()

    # Success: No current user exists
    def test_no_user(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        render_template_mock: Mock,
        get_current_user_mock: Mock,
    ) -> None:
        with app.test_request_context("/account"):
            session["user_email"] = EMAIL
            get_current_user_mock.return_value = None
            account()

        flash_mock.assert_not_called()
        url_for_mock.assert_not_called()
        redirect_mock.assert_not_called()
        render_template_mock.assert_called_once_with("account.html", current_user=None)

    # Success: Current user exists
    def test_user(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        render_template_mock: Mock,
        get_current_user_mock: Mock,
    ) -> None:
        get_current_user_mock.return_value = USER

        with app.test_request_context("/account"):
            session["user_email"] = EMAIL
            account()

        flash_mock.assert_not_called()
        url_for_mock.assert_not_called()
        redirect_mock.assert_not_called()
        render_template_mock.assert_called_once_with("account.html", current_user=USER)


@patch("app.get_current_user")
@patch("app.redirect", return_value=None)
@patch("app.url_for", return_value="url")
@patch("app.flash", return_value=None)
class UpdateProfileTest(unittest.TestCase):
    # Failure: No user email in sessions
    def test_no_user_email(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        get_current_user_mock: Mock,
    ) -> None:
        with app.test_request_context("/update-profile", method="POST"):
            session.clear()
            account()

        get_current_user_mock.assert_not_called()
        flash_mock.assert_called_once_with(
            "Please log in to access this page.", "error"
        )
        url_for_mock.assert_called_once_with("login")
        redirect_mock.assert_called_once_with("url")

    # Failure: No current user exists
    def test_no_user(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        get_current_user_mock: Mock,
    ) -> None:
        with app.test_request_context("/update-profile", method="POST"):
            session["user_email"] = EMAIL
            get_current_user_mock.return_value = None
            update_profile()

        flash_mock.assert_called_once_with(
            "Cannot update profile for unknown user", "error"
        )
        url_for_mock.assert_called_once_with("account")
        redirect_mock.assert_called_once_with("url")

    # Success: Nothing is changed
    def test_no_change(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        get_current_user_mock: Mock,
    ) -> None:
        with app.test_request_context("/update-profile", method="POST", data={}):
            session["user_email"] = EMAIL
            get_current_user_mock.return_value = USER
            update_profile()

        updated_user = get_current_user_mock.return_value
        self.assertEqual(updated_user.name, NAME)
        self.assertEqual(updated_user.address, ADDRESS)
        self.assertTrue(updated_user.check_password(PASSWORD))
        flash_mock.assert_called_once_with("Profile updated successfully!", "success")
        url_for_mock.assert_called_once_with("account")
        redirect_mock.assert_called_once_with("url")

    # Success: Name and address are changed
    def test_update_name_address(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        get_current_user_mock: Mock,
    ) -> None:
        with app.test_request_context(
            "/update-profile",
            method="POST",
            data={"name": "Jane Doe", "address": "New address"},
        ):
            session["user_email"] = EMAIL
            get_current_user_mock.return_value = USER
            update_profile()

        updated_user = get_current_user_mock.return_value
        self.assertEqual(updated_user.name, "Nobody")
        self.assertEqual(updated_user.address, "New address")
        self.assertTrue(updated_user.check_password(PASSWORD))
        flash_mock.assert_called_once_with("Profile updated successfully!", "success")
        url_for_mock.assert_called_once_with("account")
        redirect_mock.assert_called_once_with("url")

    # Success: Update name, address, and password
    def test_update_name_address_password(
        self,
        flash_mock: Mock,
        url_for_mock: Mock,
        redirect_mock: Mock,
        get_current_user_mock: Mock,
    ) -> None:
        password = "cool new password"
        with app.test_request_context(
            "/update-profile",
            method="POST",
            data={
                "name": "Jane Doe",
                "address": "New address",
                "new_password": password,
            },
        ):
            session["user_email"] = EMAIL
            get_current_user_mock.return_value = USER
            update_profile()

        updated_user = get_current_user_mock.return_value
        self.assertEqual(updated_user.name, "Jane Doe")
        self.assertEqual(updated_user.address, "New address")
        self.assertTrue(updated_user.check_password(password))
        flash_mock.assert_called_once_with("Password updated successfully!", "success")
        url_for_mock.assert_called_once_with("account")
        redirect_mock.assert_called_once_with("url")
