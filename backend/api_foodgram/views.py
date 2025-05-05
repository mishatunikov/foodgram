from django.shortcuts import get_object_or_404, redirect

from foodgram.models import Recipe


def redirect_to_recipe(request, link_id):
    recipe = get_object_or_404(Recipe, short_link_id=link_id)
    return redirect(to=f'/recipes/{recipe.id}/')
