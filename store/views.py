import django
from django.contrib.auth.models import User
from sslcommerz_lib import SSLCOMMERZ
from django.db.models import Q
from .utils import createOrder, getSsslCom
from django.views.decorators.csrf import csrf_exempt
import uuid
from store.models import Address, Cart, Category, Order, Product, Transactions
from django.shortcuts import redirect, render, get_object_or_404
from .forms import RegistrationForm, AddressForm
from django.contrib import messages
from django.views import View
import decimal
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator  # for Class Based Views
from django.http import JsonResponse


# Create your views here.


def home(request):
    categories = Category.objects.filter(is_active=True, is_featured=True)[:3]
    products = Product.objects.filter(is_active=True, is_featured=True)[:8]
    context = {
        "categories": categories,
        "products": products,
    }
    return render(request, "store/index.html", context)


def detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.exclude(id=product.id).filter(
        is_active=True, category=product.category
    )
    context = {
        "product": product,
        "related_products": related_products,
    }
    return render(request, "store/detail.html", context)


def all_categories(request):
    categories = Category.objects.filter(is_active=True)
    return render(request, "store/categories.html", {"categories": categories})


def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(is_active=True, category=category)
    categories = Category.objects.filter(is_active=True)
    context = {
        "category": category,
        "products": products,
        "categories": categories,
    }
    return render(request, "store/category_products.html", context)


def products(request):
    category = request.GET.get("category")
    search = request.GET.get("search")
    filters = {}
    if category:
        category = get_object_or_404(Category, slug=category)
        filters["category"] = category
    if search:
        filters["title__contains"] = search
    products = Product.objects.filter(**filters, is_active=True)
    categories = Category.objects.filter(is_active=True)
    context = {
        "products": products,
        "categories": categories,
    }
    return render(request, "store/products.html", context)


# Authentication Starts Here


class RegistrationView(View):
    def get(self, request):
        form = RegistrationForm()
        return render(request, "account/register.html", {"form": form})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            messages.success(request, "Congratulations! Registration Successful!")
            form.save()
        return render(request, "account/register.html", {"form": form})


@login_required
def profile(request):
    addresses = Address.objects.filter(user=request.user)
    orders = Order.objects.filter(user=request.user)
    return render(
        request, "account/profile.html", {"addresses": addresses, "orders": orders}
    )


@method_decorator(login_required, name="dispatch")
class AddressView(View):
    def get(self, request):
        form = AddressForm()
        return render(request, "account/add_address.html", {"form": form})

    def post(self, request):
        form = AddressForm(request.POST)
        if form.is_valid():
            user = request.user
            locality = form.cleaned_data["locality"]
            city = form.cleaned_data["city"]
            state = form.cleaned_data["state"]
            reg = Address(user=user, locality=locality, city=city, state=state)
            reg.save()
            messages.success(request, "New Address Added Successfully.")
        return redirect("store:profile")


@login_required
def remove_address(request, id):
    a = get_object_or_404(Address, user=request.user, id=id)
    a.delete()
    messages.success(request, "Address removed.")
    return redirect("store:profile")


@login_required
def add_to_cart(request):
    user = request.user
    product_id = request.GET.get("prod_id")
    product = get_object_or_404(Product, id=product_id)

    # Check whether the Product is alread in Cart or Not
    item_already_in_cart = Cart.objects.filter(product=product_id, user=user)
    if item_already_in_cart:
        cp = get_object_or_404(Cart, product=product_id, user=user)
        cp.quantity += 1
        cp.save()
    else:
        Cart(user=user, product=product).save()

    return redirect("store:cart")


@login_required
def cart(request):
    user = request.user
    cart_products = Cart.objects.filter(user=user)

    # Display Total on Cart Page
    amount = decimal.Decimal(0)
    shipping_amount = decimal.Decimal(10)
    # using list comprehension to calculate total amount based on quantity and shipping
    cp = [p for p in Cart.objects.all() if p.user == user]
    if cp:
        for p in cp:
            temp_amount = p.quantity * p.product.price
            amount += temp_amount

    # Customer Addresses
    addresses = Address.objects.filter(user=user)

    context = {
        "cart_products": cart_products,
        "amount": amount,
        "shipping_amount": shipping_amount,
        "total_amount": amount + shipping_amount,
        "addresses": addresses,
    }
    return render(request, "store/cart.html", context)


@login_required
def remove_cart(request, cart_id):
    if request.method == "GET":
        c = get_object_or_404(Cart, id=cart_id)
        c.delete()
        messages.success(request, "Product removed from Cart.")
    return redirect("store:cart")


@login_required
def plus_cart(request, cart_id):
    if request.method == "GET":
        # Get list of item in cart
        total_cart_of_user = Cart.objects.filter(user=request.user).count()

        # Get cart
        cp = get_object_or_404(Cart, id=cart_id)
        cp.quantity += 1
        cp.save()

        return JsonResponse(
            {
                "status": "success",
                "id": cart_id,
                "quantity": cp.quantity,
                "total_price": cp.total_price,
                "total_cart_of_user": total_cart_of_user,
                "overall_product_price_of_cart":cp.overall_product_price_of_cart
            }
        )


@login_required
def minus_cart(request, cart_id):
    if request.method == "GET":
        # Get list of item in cart
        total_cart_of_user = Cart.objects.filter(user=request.user).count()

        # Get cart
        cp = get_object_or_404(Cart, id=cart_id)
        if cp.quantity == 1:
            cp.delete()
        else:
            cp.quantity -= 1
            cp.save()
        return JsonResponse(
            {
                "status": "success",
                "id": cart_id,
                "quantity": cp.quantity,
                "total_price": cp.total_price,
                "total_cart_of_user": total_cart_of_user,
                "overall_product_price_of_cart":cp.overall_product_price_of_cart
            }
        )


@login_required
def checkout(request):
    user = request.user
    address_id = request.GET.get("address")
    address = get_object_or_404(Address, id=address_id)

    payment = (
        request.GET.get("paymenttype") if request.GET.get("paymenttype") else "cash"
    )

    if payment == "cash":
        createOrder(request.user, address)
        # Get all the products of User in Cart

    else:
        amount = decimal.Decimal(0)
        shipping_amount = decimal.Decimal(10)
        trans_id = uuid.uuid1()
        # using list comprehension to calculate total amount based on quantity and shipping
        cp = [p for p in Cart.objects.all() if p.user == user]
        if cp:
            for p in cp:
                temp_amount = p.quantity * p.product.price
                amount += temp_amount

        post_body = {}
        post_body["total_amount"] = amount
        post_body["currency"] = "BDT"
        post_body["tran_id"] = trans_id
        post_body["success_url"] = "http://127.0.0.1:8000/ssl/payment/response/success"
        post_body["fail_url"] = "http://127.0.0.1:8000/ssl/payment/response/faild"
        post_body["cancel_url"] = "http://127.0.0.1:8000/ssl/payment/response/faild"
        post_body["emi_option"] = 0
        post_body["cus_name"] = user.username
        post_body["cus_email"] = user.email
        post_body["cus_phone"] = "018"
        post_body["cus_add1"] = address.locality
        post_body["cus_city"] = address.city
        post_body["cus_country"] = "Bangladesh"
        post_body["shipping_method"] = "NO"
        post_body["multi_card_name"] = ""
        post_body["num_of_item"] = 1
        post_body["product_name"] = "Test"
        post_body["product_category"] = "Test Category"
        post_body["product_profile"] = "general"

        sslcz = getSsslCom()
        response = sslcz.createSession(post_body)  # API response
        # print(response)
        if response["status"] == "SUCCESS":
            Transactions(user=request.user, trans_id=trans_id, provider="SSL").save()
            request.session["address"] = address.id
            return redirect(response["GatewayPageURL"])

    return redirect("store:orders")


@csrf_exempt
@login_required
def paymentresponse(request):
    print(request.POST)
    tranid = request.POST["tran_id"]

    transaction = Transactions.objects.filter(trans_id=tranid).first()
    if transaction:
        sslcz = getSsslCom()
        response = sslcz.transaction_query_tranid(tranid)
        print(response.get("element")[0]["status"], response)
        if response.get("element")[0]["status"] == "VALID":
            print("test")
            address = Address.objects.filter(pk=request.session.get("address")).first()
            createOrder(request.user, address)
            transaction.status = "SUCCESS"
            transaction.save()
    return redirect("store:orders")


@login_required
def paymentfaildresponse(request):
    tranid = request.POST["tran_id"]
    transaction = Transactions.objects.filter(trans_id=tranid).first()
    transaction.status = "FAILD"
    transaction.save()


@login_required
def orders(request):
    all_orders = Order.objects.filter(user=request.user).order_by("-ordered_date")
    return render(request, "store/orders.html", {"orders": all_orders})


def shop(request):
    return render(request, "store/shop.html")


def test(request):
    return render(request, "store/test.html")
