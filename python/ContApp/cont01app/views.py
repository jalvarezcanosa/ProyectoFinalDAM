import json
import base64
from datetime import timezone

from django.core.files.base import ContentFile
from django.db.models import Count, F
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from ContApp.cont01app.models import CounterGroup, CountEntry


def create_counter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        title = data.get('title')
        description = data.get('description')
        closes_at = data.get('closes_at')
        image_b64 = data.get('image_base64')

        if not title or not closes_at:
            return JsonResponse({'message': 'Title and closes at are required'}, status=400)

        new_counter = CounterGroup(
            title=title,
            description=description,
            closes_at=closes_at,
            creator = request.user,
        )

        if image_b64:
            if ';base64' in image_b64:
                format, imgstr = image_b64.split(';base64,')
                ext = format.split('/')[-1]
            else:
                imgstr = image_b64
                ext = 'jpg'

            data_image = ContentFile(base64.b64decode(imgstr), name=f'foto_temp.{ext}')

            new_counter.image = data_image

        new_counter.save()

        new_counter.participants.add(request.user)

        return JsonResponse({"message": "Counter created successfully!",
        "counter_id": new_counter.id}, status=201)

    else:
        return JsonResponse({"error": "Method not allowed!"}, status=405)

def get_counter_stats(request, counter_id):
    if request.method == 'GET':
        counter = get_object_or_404(CounterGroup, id=counter_id)

        sort_order = request.GET.get('sort_order', 'desc')
        ranking_query = CountEntry.objects.filter(counter=counter).values(
            username=F('user__username')
        ).annotate(
            total_clicks=Count('id'),
        )

        if sort_order == 'asc':
            ranking_query = ranking_query.order_by('total-clicks')
        else:
            ranking_query = ranking_query.order_by('-total-clicks')

        response_data = {
            "counter": counter.title,
            "closes_at": counter.close_at < timezone.now(),
            "participants": counter.participants.count(),
            "ranking": list(ranking_query),
        }

        return JsonResponse(response_data, safe=False, status=200)

