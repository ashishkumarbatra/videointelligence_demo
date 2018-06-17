import os

from django.http import JsonResponse

from django.shortcuts import render
from django.views.generic import View
from django.conf import settings

from .src.main import VideoIntelligenceRunner
from .src.config import gcs_bucket_url


class DashboardView(View):
    template_name = 'dashboard.html'

    def get(self, request, *args, **kwargs):
        #changing to check
        context = {'video_path': 'Here_how_Trump_North_Korea_summit_failed.mp4'}
        #context = {'video_path': 'data/' + video_name}
        return render(request, self.template_name, context=context)

    def post(self, request, *args, **kwargs):
        query = request.POST.get('query')
        video_url_obj = request.POST.get('video_url')
        video_button_obj = request.POST.get('video_button')
        video_url = str(video_url_obj)
        video_button = str(video_button_obj)
        dashbaord_video_name = os.path.split(video_url)[-1]
        # print(query)
        # print(video_url_obj,video_url,dashbaord_video_name)

        runner = VideoIntelligenceRunner()

        if query and hasattr(settings, 'ANALYTICS_DATA'):
            data = settings.ANALYTICS_DATA
            words = data['speech_analytics']['words']
            runner.search(words, query)
            data = runner.data
        else:
            data = runner.main(query,dashbaord_video_name,video_button)
        # setattr(settings, 'ANALYTICS_DATA', data)
        # data = {'speech_analytics': []}

        return JsonResponse(data)

