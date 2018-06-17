"""
For demo take english video
"""
import os
from collections import defaultdict

# from fileutil import FileUtil
# from config import video_name, local_video_folder
# from video_to_text import VideoToText


# from .fileutil import FileUtil
from .config import  local_video_folder
from .video_to_text import VideoToText

# video_full_path = os.path.join(local_video_folder, video_name)


class VideoSearch(object):
    def __init__(self, video_path, query, **kwargs):
        """

        :param video_path: video path
        :param query: query to search, exact text
        :param kwargs:
        """
        self.video_path = video_path

        self.query = str(query).lower()

    def search(self, words):
        search_data = defaultdict(dict)
        if self.query in words:
            search_data[self.query]['status'] = True
            search_data[self.query]['count'] = len(words[self.query])
            search_data[self.query]['data'] = words[self.query]

        else:
            search_data[self.query]['status'] = False
        return dict(search_data)

    def run(self, **kwargs):
        """
        1. Transcribe audio
        2. search in audio text , get the time stamp

        clip video from the portion
        :return:
        """
        obj = VideoToText(video_url=self.video_path)
        transcript_words = obj.extract_text(**kwargs)
        words = transcript_words['words']
        return self.search(words)


if __name__ == '__main__':
    audio_file_name = 'mono_audio_India_does_not_believe_in_Me_First_approach_Sushma_Swaraj.mp4_2018-05-24_18:25:13.642331.flac'
    # search = VideoSearch(video_full_path, 'donald')
    # search.run(save_to_cloud=False, audio_file_name=audio_file_name)



