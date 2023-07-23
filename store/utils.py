from store.models import Address, Cart, Category, Order, Product,Transactions
from sslcommerz_lib import SSLCOMMERZ 


def createOrder(user, address):
        cart = Cart.objects.filter(user=user)
        for c in cart:
            # Saving all the products from Cart to Order
            Order(user=user, address=address, product=c.product, quantity=c.quantity).save()
            # And Deleting from Cart
            c.delete()

def getSsslCom():
        settings = { 
                'store_id': 'sears6416df2ea881d',
                'store_pass': 'sears6416df2ea881d@ssl',
                'issandbox': True 
                }
        return SSLCOMMERZ(settings)            