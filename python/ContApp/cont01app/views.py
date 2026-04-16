import json
import base64
from django.utils import timezone

from django.core.files.base import ContentFile
from django.db.models import Count, F
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from cont01app.models import CounterGroup, CountEntry

def get_counter(request):
    if request.method == 'GET':
        counter = CounterGroup.objects.filter(participants = request.user)

        status = request.GET.get('status')

        if status == 'active':
            counter = counter.filter(close_at__gt=timezone.now())
        elif status == 'finished':
            counter = counter.filter(close_at__le=timezone.now())

        counters_list = []
        for c in counter:
            counters_list.append({
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "image_url": c.image,
                "close_at": c.close_at,
                "state": c.state,
                "participants_count": c.participants.count(),
            })

        return JsonResponse(counters_list, safe=False, status=200)

    else:
        return JsonResponse({"error": "Method not allowed!"}, status=405)

def create_counter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        title = data.get('title')
        description = data.get('description')
        close_at = data.get('close_at')
        image_b64 = data.get('image_base64')

        if not title or not close_at:
            return JsonResponse({'message': 'Title and close at are required'}, status=400)

        new_counter = CounterGroup(
            title=title,
            description=description,
            close_at=close_at,
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
            ranking_query = ranking_query.order_by('total_clicks')
        else:
            ranking_query = ranking_query.order_by('-total_clicks')

        response_data = {
            "counter": counter.title,
            "close_at": counter.close_at < timezone.now(),
            "participants": counter.participants.count(),
            "ranking": list(ranking_query),
        }

        return JsonResponse(response_data, safe=False, status=200)
    else:
        return JsonResponse({"error": "Method not allowed!"}, status=405)

def update_counter(request, counter_id):
    if request.method == 'PUT':
        counter = get_object_or_404(CounterGroup, id=counter_id)

        if counter.creator != request.user:
            return JsonResponse({'error': 'Not authorized'}, status=401)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        if 'title' in data:
            counter.title = data['title']

        if 'description' in data:
            counter.description = data['description']

        if 'close_at' in data:
            counter.close_at = data['close_at']

        counter.save()

        return JsonResponse({
            "message": "Counter updated successfully!",
            "counter_id": counter.id
        }, status=200)
    else:
        return JsonResponse({"error": "Method not allowed!"}, status=405)

def delete_counter(request, counter_id):
    if request.method == 'DELETE':
        counter = get_object_or_404(CounterGroup, id=counter_id)

        if counter.creator != request.user:
            return JsonResponse({"message": "Forbidden: Only the creator can delete this counter."}, status=403)

        counter.delete()

        return JsonResponse({"message": "Counter deleted successfully!"}, status=200)

    else:
        return JsonResponse({"error": "Method not allowed!"}, status=405)

def increment_counter(request, counter_id):
    if request.method == 'POST':
        counter = get_object_or_404(CounterGroup, id=counter_id)

        if counter.state == 'finished':
            return JsonResponse({'error': 'Counter already closed!'}, status=400)

        if request.user not in counter.participants.all():
            return JsonResponse({'error': 'You must join the counter first'}, status=401)

        CountEntry.objects.create(
            user=request.user,
            counter=counter,
        )

        user_total_clicks = CountEntry.objects.filter(user=request.user, counter=counter).count()

        return JsonResponse({
            'message': 'Counter incremented successfully!',
            'user_total_clicks': user_total_clicks
        }, status=200)

    else:
        return JsonResponse({"error": "Method not allowed!"}, status=405)