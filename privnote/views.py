from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Note
from .forms import NoteForm
from django.utils import timezone
from django.views.decorators.cache import never_cache

def create_note_view(request):
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            duration = form.cleaned_data['duration']
            if duration:
                duration = int(duration)
                note.expires_at = timezone.now() + timezone.timedelta(minutes=duration)
                note.one_time_view = form.cleaned_data['one_time_view'] #dont know 
            note.save()
            return redirect('note_created', unique_link=note.unique_link)
    else:
        form = NoteForm()
    return render(request, 'privnote/create_note.html', {'form': form})

    

def note_created_view(request, unique_link):
    return render(request, 'privnote/note_created.html', {'unique_link': unique_link})


@never_cache
def view_note_view(request, unique_link):
    note = get_object_or_404(Note, unique_link=unique_link)
    
    if note.is_expired() or not note.is_active:
        return render(request, 'privnote/error.html', {'message': 'No longer available.'}, status=410)

    # Render the note content
    response = render(request, 'privnote/view_note.html', {'note': note})


    
    note.mark_as_viewed()

    # Add cache control headers
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response