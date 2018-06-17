import os
from google.cloud import storage

#from fileutil import FileUtil
# from .fileutil import FileUtil

gcs_bucket = 'videointelligence_demo'
gcs_bucket_url ='https://storage.googleapis.com/videointelligence_demo'
ffmpeg_duration_format = "%H:%M:%S.%f"

# video_name = 'Here_how_Trump_North_Korea_summit_failed.mp4'
# video_name = 'short_kim_trump.mp4'
# video_name = 'Narendra_Modi_Full_Speech_At_British_Parliament_In_U_K.mp4'
# video_name = 'Narendra_Modi_on_demonetisation_of_Rs_500_and_Rs_1000_notes.mp4'
# video_name = 'India_does_not_believe_in_Me_First_approach_Sushma_Swaraj.mp4'
local_video_folder = 'data'
local_tmp_folder = 'temp'
# video_encoding = 'hi-IN' #'en-US'  # 'hi-IN'


video_frames_json = 'video_frames_json'
video_frames_folder = 'video_frames'
image_crops_frames = 'image_crops'
audio_folder = 'audio'

paths_to_make = [
    os.path.join(local_tmp_folder, video_frames_json),
    os.path.join(local_tmp_folder, video_frames_folder),
    os.path.join(local_tmp_folder, image_crops_frames),
    os.path.join(local_tmp_folder, audio_folder),
]
# client = storage.Client()
#         bucket = client.get_bucket(gcs_bucket)
#         bucket.get_blob()
#         blob = bucket.blob(video_frames_json+'/'+target_file)
#         blob.upload_from_filename(target_file_path)
#         print("Uploaded Video intelligence data to cloud", video_frames_json+'/'+target_file)
#
# for path in paths_to_make:
#     if not os.path.exists(path):
#         print("Creating folder", path)
#         os.makedirs(path)


def clean_folders():
    for path in paths_to_make:
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
                print("Deleted", file_path)

#clean_folders()