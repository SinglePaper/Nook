from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from taggit.managers import TaggableManager


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=20, unique=True, blank=True, null=True)
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_books')
    created_at = models.DateTimeField(auto_now_add=True)
    availability = models.BooleanField(default=True)
    tags = TaggableManager(blank=True)
    
    class Meta:
        ordering = ['-availability','author','title', 'owner']
    
    def __str__(self):
        return self.title
    
    def is_available(self):
        self.availability = not self.loans.filter(returned_at__isnull=True).exists()
        self.save()
        # print(self.availability)
        return self.availability

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            total_rating = sum(review.rating for review in reviews)
            return total_rating / reviews.count()
        return 0.0


class BookList(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='book_lists')
    books = models.ManyToManyField(Book, related_name='lists', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class Loan(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='loans')
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrowed_books')
    borrowed_at = models.DateTimeField(auto_now_add=True)
    returned_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-borrowed_at']
    
    def __str__(self):
        return f"{self.borrower.username} borrowed {self.book.title}"


class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('book', 'reviewer')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.reviewer.username} - {self.book.title}"


class Subscriptions(models.Model):
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    subscribed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscribers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('subscribed', 'subscriber')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subscriber.username} subscribed to {self.subscribed.username}"

