"""
putting all things together
"""
import datetime
import os
from pprint import pprint

from src.nlp_analytics import NLPAnalytics
from src.video_intellegence import ParseVideo
from src.video_search import VideoSearch
from src.video_to_text import VideoToText
from src.vision_analytics import VisionAnalytics
from src.config import video_name, local_video_folder, video_frames_folder, local_tmp_folder, clean_folders


class VideoIntelligenceRunner(object):
    def __init__(self):
        self.data = {}

    def main(self, query=''):
        # return fixture_data

        clean_folders()
        print("Starting Video Processing", datetime.datetime.now())
        video_parse = ParseVideo(video_name)
        process_video_data = video_parse.run()
        print("Finished Video Processing", datetime.datetime.now())

        self.data['video_analytics'] = process_video_data
        print(self.data)
        self.data['vision_analytics'] = []

        for image in process_video_data['frame_images']:
            image_path = os.path.join(local_tmp_folder, video_frames_folder, image)
            vanalytics = VisionAnalytics(image_path)
            vision_data = vanalytics.run()
            print("Statring vision analytics on ")
            self.data['vision_analytics'].append(vision_data)

        print("Starting Speech Analytics")
        video_abs_path = os.path.join(local_video_folder, video_name)
        vtext = VideoToText(video_abs_path)
        vspeechdata = vtext.run()
        self.data['speech_analytics'] = vspeechdata
        print(self.data)
        print("Finished Speech Analytics")

        print("Starting NLP analytics")
        nlp_ana = NLPAnalytics()
        nlp_data = nlp_ana.entities_text(vspeechdata['transcript'])
        self.data['nlp_analytics'] = nlp_data
        print(self.data['nlp_analytics'])
        print("Finished NLP Analytics")

        words = self.data['speech_analytics']['words']

        self.search(video_abs_path, words, query)

        self.data = dict(self.data)
        pprint(self.data)
        return self.data

    def search(self, video_abs_path, words, query):
        if query:
            print("Starting search analytics ")
            vsearch = VideoSearch(video_abs_path, query)
            vsearch_data = vsearch.search(words)
            self.data['search_data'] = vsearch_data
            print(self.data)
            print("Finished Search Analytics")
        else:
            self.data['search_data'] = "Pass query to search"
        return {'search_data': self.data['search_data']}


if __name__ == '__main__':
    vrunner = VideoIntelligenceRunner()
    vrunner.main()


