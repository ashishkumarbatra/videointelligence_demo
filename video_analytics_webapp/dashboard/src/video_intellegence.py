import os
import datetime
from google.cloud import videointelligence
from google.cloud import storage
import json
import time

# from config import gcs_bucket, video_name, local_video_folder, video_frames_folder, local_tmp_folder, video_frames_json
# from fileutil import FileUtil

from .config import gcs_bucket, local_video_folder, video_frames_folder, local_tmp_folder, video_frames_json
# from .fileutil import FileUtil

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
        #remove hardcoding
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
        # Django changes
        # video_input = os.path.join(local_video_folder, self.video)
        # video_input = os.path.join(self.video)

        s_client = storage.Client()
        s_bucket = s_client.bucket(gcs_bucket)
        blob = s_bucket.blob(self.video)

        # store the file temporarily for processing
        video_input = os.path.join(local_video_folder, self.video)
        directory = os.path.dirname(video_input)
        if not os.path.exists(directory):
            os.makedirs(directory)
        # write code to clean directory if exists

        blob.download_to_filename(video_input)
        #hardcoding time to sleep for download
        time.sleep(20)

        video_frames_path = os.path.join(local_tmp_folder,video_frames_folder)
        if not os.path.exists(video_frames_path):
            os.makedirs(video_frames_path)
        screenshot_files = []
        for _ftime in timestamps:
            try:
                # name_output = FileUtil.join(local_tmp_folder, video_frames_folder, str(_ftime)+ '.jpg')
                name_output = os.path.join(local_tmp_folder, video_frames_folder, str(_ftime) + '.jpg')
                screenshot_files.append(name_output)
                print("Creating screenshot", name_output)
                # remove pre-existing files
                try:
                    if os.path.isfile(name_output):
                        os.unlink(name_output)
                    # elif os.path.isdir(file_path): shutil.rmtree(file_path)
                except Exception as e:
                    print(e)

                os.system("ffmpeg -i " + video_input + " -ss " + str(_ftime) + " -frames:v 1 " + name_output)
            except ValueError:
                return ("Oops! error when creating screenshot")
        return screenshot_files

    def run(self):
        processed_data = self.process()
        #processed data is annotated data
        print("processed_data")
        print(processed_data)
        # processed_data = {'person': [0.661993, 1.787127, 3.6564870000000003, 5.680453]}#, 7.617809, 8.698539, 30.621787, 79.793596, 96.352172, 97.47503, 99.758555, 101.866913, 369.632425, 709.352819, 829.4914220000001, 876.436231, 1509.513032]}
        screenshot_files = self.capture_frames(processed_data['person'])
        processed_data['frame_images'] = [os.path.split(image)[-1] for image in screenshot_files]
        #not required everything on cloud
        self.upload_to_gcs(processed_data)
        framesPublicUurlDict =self.upload_image(screenshot_files)
        processed_data['publicUrls'] = framesPublicUurlDict
        return processed_data

    def upload_to_gcs(self, data):
        json_data = json.dumps(data)
        _tstamp = str(datetime.datetime.now()).replace(' ', '_')
        base_target_path = os.path.join(local_tmp_folder, video_frames_json)
        # if not os.path.exists(base_target_path):
        #     os.makedirs(base_target_path)

        target_file = 'person_video_intelligence.json'
        target_file_path = os.path.join(base_target_path, target_file)

        # remove pre-existing files
        try:
            if os.path.isfile(target_file_path):
                os.unlink(target_file_path)
            # elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)

        directory = os.path.dirname(target_file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)


        with open(target_file_path, 'w') as json_file:
            print("Saving Video Intelligence data to ", target_file_path)
            json_file.write(json_data)

        client = storage.Client()
        bucket = client.get_bucket(gcs_bucket)
        blob = bucket.blob(video_frames_json+'/'+target_file)
        blob.upload_from_filename(target_file_path)
        print("Uploaded Video intelligence data to cloud", video_frames_json+'/'+target_file)

    def upload_image(self, images):
        urlDict ={}
        client = storage.Client()
        bucket = client.get_bucket(gcs_bucket)
        for image in images:
            image_name =  os.path.split(image)[-1]
            blob = bucket.blob(video_frames_folder + '/' + image_name)
            blob.upload_from_filename(image)
            blob.make_public()
            public_url_data = blob.public_url
            urlDict[image_name]= public_url_data
            print("uploading", image)
        return urlDict


if __name__ == "__main__":
    parser = ParseVideo(video_name)
    parser.run()

