from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordChangeView
from django.contrib import messages
from django.db.models import Q, Avg
from django.urls import reverse_lazy
from django.http import Http404, JsonResponse
from django.core.mail import send_mail
from django.views.decorators.http import require_http_methods
from taggit.models import Tag
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import BookListSerializer, BookSerializer
from .models import Book, BookList, Loan, Review
from .forms import SignUpForm, BookForm, ReviewForm, UserProfileForm, UserPasswordChangeForm

def get_all_tags():
    return ",".join([tag.name.lower() for tag in Tag.objects.filter(taggit_taggeditem_items__isnull=False).distinct()])

def get_autocomplete(request, **kwargs):
    query = request.GET.__getitem__('query').strip()

    if len(query) < 1:
        return JsonResponse({'results': []})

    books = [str(book) for book in Book.objects.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(author__icontains=query))]
    tags = [str(tag) for tag in Tag.objects.filter(taggit_taggeditem_items__isnull=False, name__icontains=query).values_list('name', flat=True).distinct()]
    authors = [str(author) for author in Book.objects.filter(author__icontains=query).values_list('author', flat=True).distinct()]

    results = {
        'authors': authors[:5],
        'tags': tags[:5],
        'books': books[:5]
    }

    return JsonResponse(results)

def get_author_autocomplete(request, **kwargs):
    query = request.GET.__getitem__('query').strip()

    if len(query) < 1:
        return JsonResponse({'results': []})

    authors = [str(author) for author in Book.objects.filter(author__icontains=query).values_list('author', flat=True).distinct()]

    results = {
        'authors': authors[:5]
    }
    return JsonResponse(results)

def custom_404(request, exception):
    return render(request, '404.html', status=404)

def home(request):
    books = Book.objects.all()
    if request.GET.get('search'):
        query = request.GET.get('search')
        books = books.filter(Q(title__icontains=query) | Q(author__icontains=query) | Q(tags__name__in=[query])).distinct()
    return render(request, 'books/home.html', {'books': books})

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'books/signup.html', {'form': form})

@login_required
def add_book(request):
    all_tags = get_all_tags()
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.owner = request.user
            book.save()
            form.save_m2m()
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm()
    return render(request, 'books/add_book.html', {
            'form': form, 
            'all_tags': all_tags
        })

@login_required
def edit_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    all_tags = get_all_tags()
    # print(all_tags)
    
    # Only the book owner can edit it
    if book.owner != request.user and not request.user.is_superuser:
        messages.error(request, "You can only edit your own books.")
        return redirect('book_detail', pk=book.pk)
    
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book details updated successfully!')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm(instance=book)
    
    return render(request, 'books/edit_book.html', {
            'form': form, 
            'book': book,
            'all_tags': all_tags
        })

@login_required
def delete_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    
    # Only the book owner can delete it
    if book.owner != request.user and not request.user.is_superuser:
        messages.error(request, "You can only delete your own books.")
        return redirect('book_detail', pk=book.pk)
    
    # Check if the book is currently borrowed
    if not book.is_available():
        messages.error(request, "You cannot delete a book that is currently borrowed. Please wait for it to be returned.")
        return redirect('book_detail', pk=book.pk)
    
    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Book deleted successfully!')
        return redirect('my_library')
    
    return render(request, 'books/delete_book.html', {'book': book})

def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    reviews = book.reviews.all()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    user_review = None
    
    if request.user.is_authenticated:
        user_review = reviews.filter(reviewer=request.user).first()
    
    if request.method == 'POST' and request.user.is_authenticated:
        form = ReviewForm(request.POST, instance=user_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.book = book
            review.reviewer = request.user
            review.save()
            return redirect('book_detail', pk=book.pk)
    else:
        form = ReviewForm(instance=user_review) if user_review else ReviewForm()

    if request.user.is_authenticated:
        user_lists = BookList.objects.filter(owner=request.user)
    else:
        user_lists = []
    


    return render(request, 'books/book_detail.html', {
        'book': book,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'form': form,
        'user_review': user_review,
        'user_lists': user_lists,
    })

@login_required
def borrow_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if book.is_available():
        Loan.objects.create(book=book, borrower=request.user)
        
        # Send email to book owner
        # Optional addition; requires mail server.
    return redirect('book_detail', pk=book.pk)

@login_required
def return_book(request, pk):
    loan = get_object_or_404(Loan, pk=pk, borrower=request.user)
    from django.utils import timezone
    loan.returned_at = timezone.now()
    loan.save()
    return redirect('my_library')

@login_required
@require_http_methods(["POST"])
def add_book_to_list(request, pk, list_pk):
    """Add a book to a list via AJAX"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    book = get_object_or_404(Book, pk=pk)
    book_list = get_object_or_404(BookList, pk=list_pk, owner=request.user)
    
    book_list.books.add(book)
    return JsonResponse({'success': True, 'message': f'Added to {book_list.name}'})

@login_required
@require_http_methods(["POST"])
def remove_book_from_list(request, pk, list_pk):
    """Add a book to a list via AJAX"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    book = get_object_or_404(Book, pk=pk)
    book_list = get_object_or_404(BookList, pk=list_pk, owner=request.user)
    
    book_list.books.remove(book)
    return redirect('view_list', list_pk=list_pk)

@login_required
@require_http_methods(["POST"])
def create_list_and_add_book(request, pk):
    """Create a new list and add a book to it"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    list_name = request.POST.get('list_name', '').strip()
    if not list_name:
        return JsonResponse({'error': 'List name cannot be empty'}, status=400)
    
    book = get_object_or_404(Book, pk=pk)
    new_list = BookList.objects.create(name=list_name, owner=request.user)
    new_list.books.add(book)
    
    return JsonResponse({
        'success': True,
        'list_id': new_list.id,
        'list_name': new_list.name,
        'message': f'Created "{list_name}" and added book'
    })

@require_http_methods(["POST"])
def delete_list(request, list_pk):
    """Delete a book list"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    book_list = get_object_or_404(BookList, pk=list_pk, owner=request.user)
    book_list.delete()
    
    return JsonResponse({'success': True})

def view_list(request, list_pk):
    """View a specific book list"""
    book_list = get_object_or_404(BookList, pk=list_pk, owner=request.user)
    books = book_list.books.all()
    
    context = {
        'book_list': book_list,
        'books': books,
    }
    return render(request, 'books/view_list.html', context)

@login_required
def my_library(request):
    owned_books = request.user.owned_books.all()
    borrowed_books = Loan.objects.filter(borrower=request.user, returned_at__isnull=True)
    
    # Get active loans for books the user owns
    active_loans = Loan.objects.filter(
        book__owner=request.user, 
        returned_at__isnull=True
    ).select_related('book', 'borrower')

    if request.user.is_authenticated:
        user_lists = BookList.objects.filter(owner=request.user)
    else:
        user_lists = []

    return render(request, 'books/my_library.html', {
        'owned_books': owned_books,
        'borrowed_books': borrowed_books,
        'active_loans': active_loans,
        'user_lists': user_lists
    })

@login_required
def mark_book_returned(request, loan_pk):
    """Owner marks a borrowed book as returned"""
    loan = get_object_or_404(Loan, pk=loan_pk)
    
    # Only the book owner can mark it as returned
    if loan.book.owner != request.user and not request.user.is_superuser:
        return redirect('my_library')
    
    if request.method == 'POST':
        from django.utils import timezone
        loan.returned_at = timezone.now()
        loan.save()
    
    return redirect('my_library')

def profile(request, username):
    user = get_object_or_404(User, username=username)
    books = user.owned_books.all()
    return render(request, 'books/profile.html', {'profile_user': user, 'books': books})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile', username=request.user.username)
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'books/edit_profile.html', {'form': form})
    
@login_required
def change_password(request):
    if request.method == 'POST':
        form = UserPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Re-authenticate the user to keep them logged in
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('profile', username=request.user.username)
    else:
        form = UserPasswordChangeForm(request.user)
    return render(request, 'books/change_password.html', {'form': form})



class BookListViewSet(viewsets.ModelViewSet):
    serializer_class = BookListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Users only see their own lists
        return BookList.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        # Automatically set the owner to the current user
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_books(self, request, pk=None):
        """Add books to an existing list"""
        book_list = self.get_object()
        book_ids = request.data.get('book_ids', [])
        
        books = Book.objects.filter(id__in=book_ids)
        book_list.books.add(*books)
        
        return Response(BookListSerializer(book_list).data)
    
    @action(detail=True, methods=['post'])
    def remove_books(self, request, pk=None):
        """Remove books from a list"""
        book_list = self.get_object()
        book_ids = request.data.get('book_ids', [])
        
        book_list.books.remove(*book_ids)
        
        return Response(BookListSerializer(book_list).data)