from django import forms

from store.models import Product
from .storage import upload_product_image


class BaseProductForm(forms.ModelForm):
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
            'images',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'price': forms.NumberInput(attrs={'min': 0, 'step': 1}),
            'stock': forms.NumberInput(attrs={'min': 0, 'step': 1}),
        }

    def save(self, commit=True):
        product = super().save(commit=False)
        uploaded_image = self.cleaned_data.get('images')
        if uploaded_image and not getattr(uploaded_image, '_committed', False):
            product.images = upload_product_image(uploaded_image)
        if commit:
            product.save()
            self.save_m2m()
        return product


class ProductEditForm(BaseProductForm):
    images = forms.ImageField(required=False)


class ProductCreateForm(BaseProductForm):
    pass
