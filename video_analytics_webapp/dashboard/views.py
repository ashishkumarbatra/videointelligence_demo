from django.http import JsonResponse

from django.shortcuts import render
from django.views.generic import View
from django.conf import settings

from .src.main import VideoIntelligenceRunner
from .src.config import video_name


class DashboardView(View):
    template_name = 'dashboard.html'

    def get(self, request, *args, **kwargs):
        context = {'video_path': 'data/' + video_name}
        return render(request, self.template_name, context=context)

    def post(self, request, *args, **kwargs):
        query = request.POST.get('query')
        runner = VideoIntelligenceRunner()

        if query and hasattr(settings, 'ANALYTICS_DATA'):
            data = settings.ANALYTICS_DATA
            words = data['speech_analytics']['words']
            runner.search(words, query)
            data = runner.data
        else:
            data = runner.main(query)
        # setattr(settings, 'ANALYTICS_DATA', data)
        # data = {'speech_analytics': []}
        print(data)

        return JsonResponse(data)

