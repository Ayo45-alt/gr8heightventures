from django.db import models
from store.models import Product, Variation
from accounts.models import Account

PER_VARIATION_STOCK = {
    # Multi-size / multi-color exact stock per variation
    238: {'UK 18 (US 14)': 1, 'UK 20 (US 16)': 4},
    164: {
        ('Gold', 'UK 14 (US 10)'): 2,
        ('Gold', 'UK 20 (US 16)'): 2,
        ('Gold', 'UK 22 (US 18)'): 3,
        ('Champagne', 'UK 18 (US 14)'): 1,
        ('Champagne', 'UK 20 (US 16)'): 3,
        ('Champagne', 'UK 22 (US 18)'): 3,
    },
    239: {'L (UK 16)': 1, 'XXL (UK 20-22)': 4, 'XL (UK 18-20)': 1},
    166: {'L (UK 16)': 2},
    170: {'1X (UK 20-22)': 1, 'Plus X (UK 18-20)': 1},
    171: {'Dark Gold': 1, 'Dark Silver': 1},
    182: {'M (UK 12-14)': 2, 'L (UK 16)': 3, 'Petite L (UK 14-16)': 1},
    180: {'1X (UK 20-22)': 1, '2X (UK 24-26)': 1, '3X (UK 26-28)': 1},
    181: {'3X (UK 26-28)': 2},
    205: {'2X (UK 24-26)': 1, '1X (UK 20-22)': 1},
    206: {'EU 40-41 (US 9.5)': 3, 'EU 41 (US 10)': 1},
    208: {'EU 41 (US 10)': 2},
    209: {'EU 40-41 (US 9.5)': 2},
    210: {'EU 40-41 (US 9.5)': 2},
    212: {'Silver Glitter': 1, 'Champagne Gold Glitter': 1},
    213: {'EU 40-41 (US 9.5)': 1, 'EU 41 (US 10)': 1},
    214: {'EU 40-41 (US 9.5)': 2, 'EU 41 (US 10)': 1},
    215: {'EU 40-41 (US 9.5)': 1, 'EU 41 (US 10)': 1, 'EU 42-43 (US 11)': 2},
    217: {'EU 40-41 (US 9.5)': 1, 'EU 41 (US 10)': 1},
    218: {'EU 40 (US 9)': 1, 'EU 42-43 (US 11)': 1},
    220: {
        ('Black Wet-Look', 'EU 40 (US 9)'): 1,
        ('Black Wet-Look', 'EU 40-41 (US 9.5)'): 2,
        ('Mirror Gold Metallic', 'EU 40-41 (US 9.5)'): 1,
    },
    223: {'EU 40 (US 9)': 1, 'EU 40-41 (US 9.5)': 1},
    229: {'EU 35 (US 5)': 1, 'EU 37 (US 6.5)': 1, 'EU 40 (US 9)': 1},
    236: {'EU 40-41 (US 9.5)': 1, 'EU 35 / Size 3': 1},
    237: {'EU 43.5 (US 10.5)': 1, 'EU 44.5 (US 11.5)': 1},
}


def get_variation_max_stock(product, variations):
    rules = PER_VARIATION_STOCK.get(product.id)
    if not rules:
        return product.stock
    size_val = None
    color_val = None
    for v in variations:
        cat = v.variation_category.lower()
        if cat == 'size':
            size_val = v.variation_value
        elif cat == 'color':
            color_val = v.variation_value
    if color_val and size_val and (color_val, size_val) in rules:
        return rules[(color_val, size_val)]
    if size_val and size_val in rules:
        return rules[size_val]
    if color_val and color_val in rules:
        return rules[color_val]
    return product.stock


class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    date_added = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.cart_id
    

class CartItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def sub_total(self):
        return self.product.price * self.quantity

    def max_available_qty(self):
        return get_variation_max_stock(self.product, self.variations.all())

    def __unicode__(self):
        return self.product
