from typing import Dict, Optional
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)
from models import (
    Book,
    Cart,
    User,
    Order,
    PaymentGateway,
    EmailService,
    ShippingInfo,
    CardPaymentInfo,
    PaypalPaymentInfo,
)
import uuid
from functools import wraps

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session management

# Global storage for users and orders (in production, use a database)
users: Dict[str, User] = {}  # email -> User object
orders: Dict[str, Order] = {}  # order_id -> Order object

# Create demo user for testing
demo_user = User(
    "demo@bookstore.com", "demo123", "Demo User", "123 Demo Street, Demo City, DC 12345"
)
users["demo@bookstore.com"] = demo_user

# Create a cart instance to manage the cart
cart: Cart = Cart()

# Create a global books dicationary to avoid duplication
BOOKS: Dict[str, Book] = {
    "The Great Gatsby": Book(
        "The Great Gatsby", "Fiction", 10.99, "/images/books/the_great_gatsby.jpg"
    ),
    "1984": Book("1984", "Dystopia", 8.99, "/images/books/1984.jpg"),
    "I Ching": Book("I Ching", "Traditional", 18.99, "/images/books/I-Ching.jpg"),
    "Moby Dick": Book("Moby Dick", "Adventure", 12.49, "/images/books/moby_dick.jpg"),
}


def get_current_user() -> Optional[User]:
    """Helper function to get current logged-in user"""
    if "user_email" in session:
        return users.get(session["user_email"])
    return None


def login_required(f):  # type: ignore
    """Decorator to require login for certain routes"""

    @wraps(f)  # type: ignore
    def decorated_function(*args, **kwargs):  # type: ignore
        if "user_email" not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)  # type: ignore

    return decorated_function  # type: ignore


@app.route("/")
def index():
    current_user = get_current_user()
    return render_template(
        "index.html", books=BOOKS.values(), cart=cart, current_user=current_user
    )


@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():
    book_title = request.form.get("title")
    quantity = str(request.form.get("quantity", 1))

    # Validate quantity
    try:
        quantity = int(quantity)
    except:
        flash(f"Received non-numeric quantity {quantity}")
        return redirect(url_for("view_cart"))

    book = BOOKS.get(book_title) if book_title else None

    if book:
        cart.add_book(book, quantity)
        flash(f'Added {quantity} "{book.title}" to cart!', "success")
    else:
        flash("Book not found!", "error")

    return redirect(url_for("index"))


@app.route("/remove-from-cart", methods=["POST"])
def remove_from_cart():
    book_title = request.form.get("title")

    # Validate required fields
    if not book_title:
        flash("Cannot remove book with unknown book_title", "error")
        return redirect(url_for("view_cart"))

    cart.remove_book(book_title)
    flash(f'Removed "{book_title}" from cart!', "success")
    return redirect(url_for("view_cart"))


@app.route("/update-cart", methods=["POST"])
def update_cart():
    """
    Update the quantity of a book in the cart.
    This function handles HTTP POST requests to update the quantity of a book in the user's cart.
    If the quantity is set to 0 or less, the book is effectively removed from the cart.
    Args:
        None (uses form data from the request)
    Returns:
        Response: Redirects to the view_cart page after updating the cart.
    Form Parameters:
        title (str): The title of the book to update.
        quantity (int): The new quantity of the book. Defaults to 1.
    Flash Messages:
        - Confirmation of removal if quantity <= 0
        - Confirmation of update otherwise
    """
    book_title: Optional[str] = request.form.get("title")
    quantity = str(request.form.get("quantity", 1))

    # Validate quantity
    try:
        quantity = int(quantity)
    except:
        flash(f"Received non-numeric quantity {quantity}")
        return redirect(url_for("view_cart"))

    # Validate book_title
    if not book_title:
        flash("Cannot update quantity for unknown book_title", "error")
        return redirect(url_for("view_cart"))

    cart.update_quantity(book_title, quantity)

    if quantity <= 0:
        flash(f'Removed "{book_title}" from cart!', "success")
    else:
        flash(f'Updated "{book_title}" quantity to {quantity}!', "success")

    return redirect(url_for("view_cart"))


@app.route("/cart")
def view_cart():
    current_user = get_current_user()
    return render_template("cart.html", cart=cart, current_user=current_user)


@app.route("/clear-cart", methods=["POST"])
def clear_cart():
    cart.clear()
    flash("Cart cleared!", "success")
    return redirect(url_for("view_cart"))


@app.route("/checkout")
def checkout():
    if cart.is_empty():
        flash("Your cart is empty!", "error")
        return redirect(url_for("index"))

    current_user = get_current_user()
    total_price = cart.get_total_price()
    return render_template(
        "checkout.html", cart=cart, total_price=total_price, current_user=current_user
    )


@app.route("/process-checkout", methods=["POST"])
def process_checkout():
    """Process the checkout form with shipping and payment information"""
    if cart.is_empty():
        flash("Your cart is empty!", "error")
        return redirect(url_for("index"))

    # Get shipping information
    shipping_info = ShippingInfo.from_opt_values(
        name=request.form.get("name"),
        email=request.form.get("email"),
        address=request.form.get("address"),
        city=request.form.get("city"),
        zip_code=request.form.get("zip_code"),
    )

    if isinstance(shipping_info, str):
        flash(shipping_info, "error")
        return redirect(url_for("checkout"))

    discount_code = request.form.get("discount_code")
    if discount_code:
        discount_code = discount_code.upper().strip()

    # Calculate total with discount
    total_amount = cart.get_total_price()
    discount_applied = 0

    if discount_code == "SAVE10":
        discount_applied = total_amount * 0.10
        total_amount -= discount_applied
        flash(f"Discount applied! You saved ${discount_applied:.2f}", "success")
    elif discount_code == "WELCOME20":
        discount_applied = total_amount * 0.20
        total_amount -= discount_applied
        flash(f"Welcome discount applied! You saved ${discount_applied:.2f}", "success")
    elif discount_code:
        flash("Invalid discount code", "error")

    # Get payment information based on the payment method
    payment_method = request.form.get("payment_method")
    if payment_method == "credit_card":
        payment_info = CardPaymentInfo.from_opt_values(
            card_number=request.form.get("card_number"),
            expiry_date=request.form.get("expiry_date"),
            cvv=request.form.get("cvv"),
        )
    elif payment_method == "paypal":
        payment_info = PaypalPaymentInfo.from_opt_values(
            email=request.form.get("paypal_email")
        )
    else:
        payment_info = f"Received invalid payment method {payment_method}"

    if isinstance(payment_info, str):
        flash(payment_info, "error")
        return redirect(url_for("checkout"))

    # Process payment through mock gateway
    payment_result = PaymentGateway.process_payment(payment_info)

    if not payment_result.transaction_id:
        flash(payment_result.message, "error")
        return redirect(url_for("checkout"))

    # Create order
    order_id = str(uuid.uuid4())[:8].upper()
    order = Order(
        order_id=order_id,
        user_email=shipping_info.email,
        items=cart.get_items(),
        shipping_info=shipping_info,
        payment_method=payment_info.payment_method,
        transaction_id=payment_result.transaction_id,
        total_amount=total_amount,
    )

    # Store order
    orders[order_id] = order

    # Add order to user if logged in
    current_user = get_current_user()
    if current_user:
        current_user.add_order(order)

    # Send confirmation email (mock)
    EmailService.send_order_confirmation(shipping_info.email, order)

    # Clear cart
    cart.clear()

    # Store order in session for confirmation page
    session["last_order_id"] = order_id

    flash("Payment successful! Your order has been confirmed.", "success")
    return redirect(url_for("order_confirmation", order_id=order_id))


@app.route("/order-confirmation/<order_id>")
def order_confirmation(order_id: str):
    """Display order confirmation page"""
    order = orders.get(order_id)
    if not order:
        flash("Order not found", "error")
        return redirect(url_for("index"))

    current_user = get_current_user()
    return render_template(
        "order_confirmation.html", order=order, current_user=current_user
    )


# User Account Management Routes


@app.route("/register", methods=["GET", "POST"])
def register():
    """User registration"""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name")
        address = request.form.get("address")

        # Validate required fields
        if not email or not password or not name or not address:
            flash("Please fill in all required fields", "error")
            return render_template("register.html")

        # Consistent capitalization for email
        email = email.lower().strip()

        if email in users:
            flash("An account with this email already exists", "error")
            return render_template("register.html")

        # Create new user
        user = User(email, password, name, address)
        users[email] = user

        # Log in the user
        session["user_email"] = email
        flash("Account created successfully! You are now logged in.", "success")
        return redirect(url_for("index"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login"""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Validate required fields
        if not email:
            flash("Please fill in all required fields", "error")
            return render_template("login.html")

        # Consistent capitalization for email
        email = email.lower().strip()

        user = users.get(email)
        if user and user.check_password(password):
            session["user_email"] = email
            flash("Logged in successfully!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """User logout"""
    session.pop("user_email", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for("index"))


@app.route("/account")
@login_required
def account():
    """User account page"""
    current_user = get_current_user()
    return render_template("account.html", current_user=current_user)


@app.route("/update-profile", methods=["POST"])
@login_required
def update_profile():
    """Update user profile"""
    current_user = get_current_user()

    # Validate required fields
    if not current_user:
        flash("Cannot update profile for unknown user", "error")
        return redirect(url_for("account"))

    current_user.name = request.form.get("name", current_user.name)
    current_user.address = request.form.get("address", current_user.address)

    new_password = request.form.get("new_password")
    if new_password:
        current_user.set_password(new_password)
        flash("Password updated successfully!", "success")
    else:
        flash("Profile updated successfully!", "success")

    return redirect(url_for("account"))


if __name__ == "__main__":
    app.run(debug=True)
