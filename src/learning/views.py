from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from accounts.models import UserConfiguration
from dictionary.models import DictionaryTerm
# from resources.models import Resource
from .models import Language, LearningLanguage, LanguageLevel, LanguageLevelCEFR

def index_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("browse"))
    return render(request, "learning/index.html", {})

@ensure_csrf_cookie
@login_required
def browse_view(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("index"))
    context = {
        "terms": DictionaryTerm.objects.filter(language=request.user.settings.learning_language.language).order_by('-added_date')[:5],
        # resources: Resource.objects.filter(language=request.user.settings.learning_language.language).order_by('-added_date')[:5],
    }
    return render(request, "learning/browse.html", context)

def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    context = {
        "profile": user,
        "its_me": user == request.user
    }
    return render(request, "learning/profile.html", context)

@ensure_csrf_cookie
@login_required
def settings_view(request):
    if not request.method == "POST":
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse("index"))
        return render(request, "learning/settings.html", {})
    email = None
    native_language = None
    learning_language = None
    try:
        email = request.POST["email"]
        native_language = request.POST["native_language"]
        learning_language = request.POST["learning_language"]
    except KeyError:
        return HttpResponseBadRequest("Nope.")

    if request.user.email != email: # Email cannot be changed (by now)
        return JsonResponse({"response": "emailchanged"})
    if native_language == learning_language: # Native language and learning language cannot be the same
        return JsonResponse({"response": "samelanguage"})
    if (request.user.email == email and
        request.user.settings.native_language.code == native_language and
        request.user.settings.learning_language.language.code == learning_language): # Nothing changed here!
        return JsonResponse({"response": "nochange"})

    if request.user.settings.native_language.code != native_language:
        request.user.settings.native_language = get_object_or_404(Language, code=native_language)
    if request.user.settings.learning_language.language.code != learning_language:
        request.user.settings.learning_language.language = get_object_or_404(Language, code=learning_language)
    request.user.save()
    request.user.settings.save()
    request.user.settings.learning_language.save()
    return JsonResponse({"response": "success"})

""" API STUFF """

def api_get_languages_view(request):
    if not request.method == "POST":
        return HttpResponseRedirect(reverse("index"))
    languages = Language.objects.order_by('name').all()
    payload = []
    for language in languages:
        payload.append({
            'name': language.name,
            'code': language.code,
            'filename': language.flag_filename()
        })
    return JsonResponse(payload, safe=False)
