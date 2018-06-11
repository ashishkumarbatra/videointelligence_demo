
import json
from collections import defaultdict
import os
import subprocess
from google.cloud import storage

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types


from .config import gcs_bucket, video_name, local_video_folder, video_encoding, local_tmp_folder, audio_folder, image_crops_frames


class VideoToText(object):
    """
    ffmpeg -i input-video.avi -vn -acodec copy output-audio.aac
    """
    def __init__(self, video_url):
        self.video_url = video_url
        self.audio_file_name = None
        self.audio_tmp_dir = os.path.join(local_tmp_folder, audio_folder)
        self.duration = None
        self.get_file_length()

    def get_file_length(self):
        print(self.video_url)
        duration = subprocess.check_output(['ffprobe', '-i', self.video_url, '-show_entries', 'format=duration', '-v', 'quiet', '-of',
             'csv=%s' % ("p=0")])
        print(duration)
        self.duration = float(duration.strip())  # in seconds

    def extract_audio(self, output_name=None):
        if output_name is None:
            output_name = os.path.split(self.video_url)[-1]

        output_name = ('audio_' + output_name).replace(" ", '_')

        print("Start Extracting Audio from Video")
        _tmp_file = os.path.join(self.audio_tmp_dir, output_name+'.aac')

        # 45 seconds audio only
        # subprocess.call(['ffmpeg', '-i', self.video_url, '-vn', '-t', '45', '-acodec', 'copy', _tmp_file])

        subprocess.call(['ffmpeg', '-i', self.video_url, '-ac', '1', '-vn', '-t', '300', '-acodec', 'copy', _tmp_file])
        print("Stop Extracting Audio from Video")

        print("Start convert aac to flac")
        _final_file_name = output_name + '.flac'
        subprocess.call(['ffmpeg', '-i', _tmp_file, '-c:a', 'flac', os.path.join(self.audio_tmp_dir, _final_file_name)])

        print("Stop convert aac to flac")

        print("start convert to mono")
        final_file_name = 'mono_'+_final_file_name
        subprocess.call(['ffmpeg', '-i', os.path.join(self.audio_tmp_dir, _final_file_name), '-ac', '1', os.path.join(self.audio_tmp_dir, final_file_name)])

        print("end convert to mono")

        self.audio_file_name = final_file_name

    def upload_to_storage(self):
        s_client = storage.Client()
        s_bucket = s_client.bucket(gcs_bucket)
        blob = s_bucket.blob('audio/'+self.audio_file_name)
        print("Start Uploading Audio to Storage")
        blob.upload_from_filename(os.path.join(self.audio_tmp_dir, self.audio_file_name))
        blob.make_public()
        print("Stop Uploading Audio to Storage")
        return blob.public_url

    def extract_text(self, save_to_cloud=True, **kwargs):
        client = speech.SpeechClient()

        audio_file_name = kwargs.get('audio_file_name') or self.audio_file_name
        audio_gcs_url = 'gs://' + gcs_bucket + '/audio/' + audio_file_name

        print("Transcribing from ", audio_gcs_url)
        audio = types.RecognitionAudio(uri=audio_gcs_url)

        config = types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.FLAC,
            language_code=video_encoding,
            enable_word_time_offsets=True)
        print("Start Extract text from audio")

        longer = (self.duration > 58)

        if longer:
            operation = client.long_running_recognize(config, audio)
            response = operation.result(timeout=500)
        else:
            response = client.recognize(config, audio)

        transcript_words = self.get_text(response)

        if transcript_words and save_to_cloud:
            s_client = storage.Client()
            s_bucket = s_client.bucket(gcs_bucket)
            blob = s_bucket.blob("speech/Transcript_"+audio_file_name+'.txt')
            print("Start transcript string to Storage")
            blob.upload_from_string("\r\n".join(transcript_words['transcript']))

            blob = s_bucket.blob("speech/Words_time_stamp_"+audio_file_name+'.json')
            words_json = json.dumps(transcript_words['words'])
            blob.upload_from_string(words_json)
            print("Stop Uploading transcript to Storage")

        print("End Extract text from audio")
        return transcript_words

    def get_text(self, response):
        transcript = []
        timestamp_word = defaultdict(list)
        for result in response.results:
            alternative = result.alternatives[0]
            # The first alternative is the most likely one for this portion. os.path.join(self.audio_tmp_dir, _final_file_name)
            print(u'Transcript: {}'.format(alternative.transcript))
            print('Confidence: {}'.format(alternative.confidence))
            transcript.append(alternative.transcript)

            for word_info in alternative.words:
                word = word_info.word.lower()
                start_time = word_info.start_time
                end_time = word_info.end_time
                timestamp_word[word].append({
                    'start_time': start_time.seconds + start_time.nanos * 1e-9,
                    'end_time': end_time.seconds + end_time.nanos * 1e-9
                })

        return {'transcript': "\r\n".join(transcript), 'words': dict(timestamp_word)}

    def run(self, **kwargs):
        self.extract_audio(**kwargs)
        audio_url = self.upload_to_storage(**kwargs)
        speech_data = self.extract_text(**kwargs)
        speech_data['audio_url'] = audio_url
        speech_data['audio_tmp_url'] = os.path.join(self.audio_tmp_dir, self.audio_file_name)
        return speech_data


if __name__ == "__main__":
    video_path = os.path.join(local_video_folder, video_name)
    extractor = VideoToText(video_path)
    extractor.run()
