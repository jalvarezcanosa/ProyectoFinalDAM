import json
from django.utils import timezone
from django.db.models import F, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from cont01app.models import Counter, CounterMembership


def get_counter(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.method == 'GET':
        user_counters = Counter.objects.filter(participants=request.user)

        for c in user_counters:
            if c.closed_at < timezone.now() and c.status != 'closed':
                c.status = 'closed'
                c.save()

        status_param = request.GET.get('status')
        if status_param == 'open':
            user_counters = user_counters.filter(status='open')
        elif status_param == 'closed':
            user_counters = user_counters.filter(status='closed')

        counters_list = []
        for c in user_counters:
            membership = CounterMembership.objects.filter(user=request.user, counter=c).first()
            individual_count = membership.individual_count if membership else 0
            global_count = CounterMembership.objects.filter(counter=c).aggregate(total=Sum('individual_count'))[
                               'total'] or 0

            counters_list.append({
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "image_url": c.image.url if c.image else None,
                "closed_at": c.closed_at,
                "status": c.status,
                "individual_count": individual_count,
                "global_count": global_count,
            })

        return JsonResponse(counters_list, safe=False, status=200)

    else:
        return JsonResponse({"error": "Method not allowed!"}, status=405)


def create_counter(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        closed_at = request.POST.get('closed_at')
        image = request.FILES.get('image')

        if not title or not closed_at:
            return JsonResponse({'message': 'Title and closed_at are required'}, status=400)

        new_counter = Counter(
            title=title,
            description=description,
            closed_at=closed_at,
            creator=request.user,
        )

        if image:
            new_counter.image = image

        new_counter.save()

        CounterMembership.objects.create(user=request.user, counter=new_counter, individual_count=0)

        return JsonResponse({
            "message": "Counter created successfully!",
            "counter_id": new_counter.id,
            "invite_code": str(new_counter.invite_code)
        }, status=201)
    else:
        return JsonResponse({"error": "Method not allowed!"}, status=405)


def get_counter_by_id(request, counter_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.method == 'GET':
        counter = get_object_or_404(Counter, id=counter_id)

        if not CounterMembership.objects.filter(user=request.user, counter=counter).exists():
            return JsonResponse({'error': 'You are not a member of this counter'}, status=403)

        if counter.closed_at < timezone.now() and counter.status != 'closed':
            counter.status = 'closed'
            counter.save()

        ranking_query = CounterMembership.objects.filter(counter=counter).values(
            username=F('user__username'),
            total_clicks=F('individual_count')
        ).order_by('-individual_count')

        response_data = {
            "counter": counter.title,
            "status": counter.status,
            "participants": counter.participants.count(),
            "ranking": list(ranking_query),
        }

        return JsonResponse(response_data, safe=False, status=200)
    else:
        return JsonResponse({"error": "Method not allowed!"}, status=405)


def update_counter(request, counter_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.method == 'PUT':
        counter = get_object_or_404(Counter, id=counter_id)

        if counter.creator != request.user:
            return JsonResponse({'error': 'Not authorized'}, status=403)

        if counter.status == 'closed':
            return JsonResponse({'error': 'Counter is closed and cannot be modified'}, status=400)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        if 'title' in data:
            counter.title = data['title']

        if 'description' in data:
            counter.description = data['description']

        if 'closed_at' in data:
            counter.closed_at = data['closed_at']

        counter.save()

        return JsonResponse({
            "message": "Counter updated successfully!",
            "counter_id": counter.id
        }, status=200)
    else:
        return JsonResponse({"error": "Method not allowed!"}, status=405)


def delete_counter(request, counter_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.method == 'DELETE':
        counter = get_object_or_404(Counter, id=counter_id)

        if counter.creator != request.user:
            return JsonResponse({"message": "Forbidden: Only the creator can delete this counter."}, status=403)

        counter.delete()

        return JsonResponse({}, status=204)

    else:
        return JsonResponse({"error": "Method not allowed!"}, status=405)


def increment_counter(request, counter_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.method == 'POST':
        counter = get_object_or_404(Counter, id=counter_id)

        if counter.status == 'closed':
            return JsonResponse({'error': 'Counter is already closed!'}, status=400)

        membership = CounterMembership.objects.filter(user=request.user, counter=counter).first()

        if not membership:
            return JsonResponse({'error': 'You must join the counter first'}, status=401)

        membership.individual_count += 1
        membership.save()

        global_count = CounterMembership.objects.filter(counter=counter).aggregate(total=Sum('individual_count'))[
                           'total'] or 0

        return JsonResponse({
            'message': 'Counter incremented successfully!',
            'individual_count': membership.individual_count,
            'global_count': global_count
        }, status=200)

    else:
        return JsonResponse({"error": "Method not allowed!"}, status=405)


def join_counter(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        invite_code = data.get('invite_code')
        if not invite_code:
            return JsonResponse({'error': 'invite_code is required'}, status=400)

        counter = Counter.objects.filter(invite_code=invite_code).first()
        if not counter:
            return JsonResponse({'error': 'Counter not found'}, status=404)

        if counter.status != 'open':
            return JsonResponse({'error': 'Counter is closed'}, status=400)

        if CounterMembership.objects.filter(user=request.user, counter=counter).exists():
            return JsonResponse({'error': 'You are already a member'}, status=400)

        CounterMembership.objects.create(user=request.user, counter=counter, individual_count=0)

        return JsonResponse({
            'id': counter.id,
            'title': counter.title,
            'description': counter.description,
            'status': counter.status,
            'invite_code': str(counter.invite_code)
        }, status=201)

    else:
        return JsonResponse({"error": "Method not allowed!"}, status=405)