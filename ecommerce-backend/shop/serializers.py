from django.utils.text import slugify
from rest_framework import serializers
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False)

    class Meta:
        model = Category
        fields = ["id", "name", "slug"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        # auto generate slugs from name if not provided
        if not validated_data.get("slug"):
            validated_data["slug"] = slugify(validated_data["name"])
        return super().create(validated_data)


class ProductSerializer(serializers.ModelSerializer):
    # accept category by PK for writes; return nested category details for reads
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), write_only=True)
    category_details = CategorySerializer(source="category", read_only=True)

    image = serializers.ImageField(required=False, allow_null=True)
    slug = serializers.SlugField(required=False)

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "category_details",  # ✅ fixed name
            "name",
            "slug",
            "description",
            "price",
            "stock",
            "available",
            "image",
            "created",
            "updated",
        ]
        read_only_fields = ["id", "created", "updated", "category_details"]

    def create(self, validated_data):
        # auto generate slug if missing
        if not validated_data.get("slug"):
            validated_data["slug"] = slugify(validated_data["name"])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # keep default behaviour
        if "slug" not in validated_data:
            # optionally update slug on name change
            name = validated_data.get("name")
            if name:
                validated_data["slug"] = slugify(name)
        return super().update(instance, validated_data)
