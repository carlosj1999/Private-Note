from django.urls import path
from .views import create_note_view, note_created_view, view_note_view

urlpatterns = [
    path('', create_note_view, name='create_note'),
    path('created/<uuid:unique_link>/', note_created_view, name='note_created'),
    path('<uuid:unique_link>/', view_note_view, name='view_note'),
]
