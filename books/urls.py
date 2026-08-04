from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views
from . import views

router = DefaultRouter()
router.register(r'lists', views.BookListViewSet, basename='book-list')

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='books/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('add-book/', views.add_book, name='add_book'),
    path('book/<int:pk>/', views.book_detail, name='book_detail'),
    path('book/<int:pk>/edit/', views.edit_book, name='edit_book'),
    path('book/<int:pk>/delete/', views.delete_book, name='delete_book'),    
    path('book/<int:pk>/add-to-list/<int:list_pk>/', views.add_book_to_list, name='add_book_to_list'),
    path('book/<int:pk>/remove-from-list/<int:list_pk>/', views.remove_book_from_list, name='remove_book_from_list'),
    path('book/<int:pk>/create-list/', views.create_list_and_add_book, name='create_list_and_add_book'),
    path('borrow/<int:pk>/', views.borrow_book, name='borrow_book'),
    path('return/<int:pk>/', views.return_book, name='return_book'),
    path('library/', views.my_library, name='my_library'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('mark-returned/<int:loan_pk>/', views.mark_book_returned, name='mark_book_returned'),
    path('api/autocomplete/', views.get_autocomplete, name='get_autocomplete'),
    path('api/author-autocomplete/', views.get_author_autocomplete, name='author_autocomplete'),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('list/<int:list_pk>/', views.view_list, name='view_list'),
    path('list/<int:list_pk>/delete/', views.delete_list, name='delete_list'),
]