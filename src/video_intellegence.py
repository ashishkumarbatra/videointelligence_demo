import os
import datetime
from google.cloud import videointelligence
from google.cloud import storage
import json

from src.config import gcs_bucket, video_name, local_video_folder, video_frames_folder, local_tmp_folder, video_frames_json


enum_features = videointelligence.enums.Feature


class ParseVideo(object):

    def __init__(self, video_name, **kwargs):
        self.video = video_name

    def process(self):
        video_client = videointelligence.VideoIntelligenceServiceClient()
        features = [videointelligence.enums.Feature.LABEL_DETECTION]

        mode = videointelligence.enums.LabelDetectionMode.SHOT_AND_FRAME_MODE
        config = videointelligence.types.LabelDetectionConfig(label_detection_mode=mode)

        context = videointelligence.types.VideoContext(label_detection_config=config)

        video_path = 'gs://' + gcs_bucket + '/' + self.video
        operation = video_client.annotate_video(input_uri=video_path, features=features, video_context=context)

        print("processing")
        result = operation.result(timeout=120)
        frame_offsets = []

        # Process frame level label annotations
        frame_labels = result.annotation_results[0].frame_label_annotations
        for i, frame_label in enumerate(frame_labels):
            for category_entity in frame_label.category_entities:
                # look for categories that contain person regardless of situation
                if category_entity.description == 'person':
                    # Each frame_label_annotation has many frames,
                    # but we keep information only about the first one
                    frame = frame_label.frames[0]
                    time_offset = (frame.time_offset.seconds +
                                   frame.time_offset.nanos / 1e9)
                    print('\tFirst frame time offset: {}s'.format(time_offset))
                    print('\tFirst frame confidence: {}'.format(frame.confidence))
                    print('\n')
                    frame_offsets.append(time_offset)

        return {'person': sorted(set(frame_offsets))}

    def capture_frames(self, timestamps):
        """
        capture frames at specified timestamps
        :param timestamps:
        :return:
        """
        video_input = os.path.join(local_video_folder, self.video)
        screenshot_files = []
        for _ftime in timestamps:
            try:
                name_output = os.path.join(local_tmp_folder, video_frames_folder, str(_ftime)+ '.jpg')
                screenshot_files.append(name_output)
                print("Creating screenshot", name_output)
                os.system("ffmpeg -i " + video_input + " -ss " + str(_ftime) + " -frames:v 1 " + name_output)
            except ValueError:
                return ("Oops! error when creating screenshot")
        return screenshot_files

    def run(self):
        processed_data = self.process()
        print(processed_data)
        # processed_data = {'person': [0.661993, 1.787127, 3.6564870000000003, 5.680453]}#, 7.617809, 8.698539, 30.621787, 79.793596, 96.352172, 97.47503, 99.758555, 101.866913, 369.632425, 709.352819, 829.4914220000001, 876.436231, 1509.513032]}
        screenshot_files = self.capture_frames(processed_data['person'])
        processed_data['frame_images'] = [os.path.split(image)[-1] for image in screenshot_files]
        #self.upload_to_gcs(processed_data)
        #self.upload_image(screenshot_files)
        return processed_data

    def upload_to_gcs(self, data):
        json_data = json.dumps(data)
        _tstamp = str(datetime.datetime.now()).replace(' ', '_')
        base_target_path = FileUtil.join(local_tmp_folder, video_frames_json)
        if not os.path.exists(base_target_path):
            os.makedirs(base_target_path)

        target_file = 'person_video_intelligence.json'
        target_file_path = os.path.join(base_target_path, target_file)

        with open(target_file_path, 'w') as json_file:
            print("Saving Video Intelligence data to ", target_file_path)
            json_file.write(json_data)

        client = storage.Client()
        bucket = client.get_bucket(gcs_bucket)
        blob = bucket.blob(video_frames_json+'/'+target_file)
        blob.upload_from_filename(target_file_path)
        print("Uploaded Video intelligence data to cloud", video_frames_json+'/'+target_file)

    def upload_image(self, images):
        client = storage.Client()
        bucket = client.get_bucket(gcs_bucket)
        for image in images:
            blob = bucket.blob(video_frames_folder + '/' + os.path.split(image)[-1])
            blob.upload_from_filename(image)
            print("uploading", image)


if __name__ == "__main__":
    parser = ParseVideo(video_name)
    parser.run()

