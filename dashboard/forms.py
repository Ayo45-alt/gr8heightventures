from django import forms

from store.models import Product


class ProductEditForm(forms.ModelForm):
    price = forms.IntegerField(min_value=0)
    stock = forms.IntegerField(min_value=0)

    class Meta:
        model = Product
        fields = (
            'product_name',
            'description',
            'price',
            'stock',
            'category',
            'is_available',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
