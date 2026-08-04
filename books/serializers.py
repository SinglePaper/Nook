from rest_framework import serializers
from .models import Book, BookList

class BookSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    average_rating = serializers.SerializerMethodField()
    tags = serializers.StringRelatedField(many=True, read_only=True)
    is_available_now = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'author',
            'isbn',
            'cover_image',
            'description',
            'owner',
            'owner_username',
            'created_at',
            'availability',
            'is_available_now',
            'tags',
            'average_rating',
        ]
        read_only_fields = ['id', 'created_at', 'owner', 'average_rating', 'is_available_now']
    
    def get_average_rating(self, obj):
        return obj.average_rating
    
    def get_is_available_now(self, obj):
        return obj.is_available()

        
class BookListSerializer(serializers.ModelSerializer):
    books = BookSerializer(many=True, read_only=True)
    book_ids = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(),
        many=True,
        write_only=True,
        source='books'
    )
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = BookList
        fields = ['id', 'name', 'owner_username', 'books', 'book_ids', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner']