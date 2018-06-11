"""
Pass in an image and get all details of that image
"""
from collections import defaultdict
import os, sys
import datetime
from google.cloud import vision
from google.cloud import storage

from PIL import Image

from config import gcs_bucket, local_video_folder, local_tmp_folder, image_crops_frames


class VisionAnalytics(object):
    def __init__(self, image, **kwargs):
        self.image_name = os.path.split(image)[-1]
        self.image = image
        self.client = vision.ImageAnnotatorClient()

    def upload_image_to_gcs(self):
        s_client = storage.Client()
        s_bucket = s_client.bucket(gcs_bucket)
        blob = s_bucket.blob("image/" + self.image_name)
        print("Start image to Storage")
        blob.upload_from_filename(self.image)
        print("End image to Storage")

    def create_vision_image(self, image_path):
        with open(image_path, 'rb') as image_obj:
            image_content = image_obj.read()
        vision_image = vision.types.Image(content=image_content)

        # vision_image = vision.types.Image()
        # vision_image.source.image_uri = "gs://"+gcs_bucket+'/image/'+self.image

        return vision_image

    def annotate(self):

        image_analytics = []
        vision_image = self.create_vision_image(self.image)

        labels = self.detect_labels(vision_image)
        web_result = self.detect_web(vision_image)
        logo = self.detect_logo(vision_image)
        # self.detect_crop_hints(vision_image)
        cords = self.detect_faces(vision_image)
        search_result = self.search_faces(vision_image, cords)
        image_analytics.extend([labels, web_result, logo, search_result])
        return image_analytics

    def detect_labels(self, vision_image):
        response = self.client.label_detection(image=vision_image)
        labels = response.label_annotations
        _labels = []

        for label in labels:
            _labels.append(label.description)
        return {'labels': _labels}

    def detect_logo(self, vision_image):
        response = self.client.logo_detection(image=vision_image)
        logos = response.logo_annotations

        _logos = []
        for logo in logos:
            _logos.append(logo.description)

        print('Logos:', _logos)
        return {'logo': _logos}

    def detect_faces(self, vision_image):
        response = self.client.face_detection(image=vision_image)
        faces = response.face_annotations

        # Names of likelihood from google.cloud.vision.enums
        likelihood_name = vision.enums
        print('vision likelihood')
        likelihood_name = ('UNKNOWN', 'VERY_UNLIKELY', 'UNLIKELY', 'POSSIBLE',
                           'LIKELY', 'VERY_LIKELY')

        print(type(faces))
        _faces = []
        for face in faces:
            face_data = {
                'anger': likelihood_name[face.anger_likelihood],
                'joy': likelihood_name[face.joy_likelihood],
                # 'Confidence': face.detectionConfidence,
                # 'landmarkingConfidence': face.landmarkingConfidence,
                'surprise': likelihood_name[face.surprise_likelihood]
            }
            print('Face Data')
            print(face_data)

            vertices = (['({},{})'.format(vertex.x, vertex.y)
                         for vertex in face.bounding_poly.vertices])

            print('face bounds: {}'.format(','.join(vertices)))
            _faces.append(face.bounding_poly.vertices)
        return _faces

    def detect_web(self, vision_image):
        """Detects web annotations given an image."""
        response = self.client.web_detection(image=vision_image)
        annotations = response.web_detection

        data = defaultdict(list)

        if hasattr(annotations, 'best_guess_labels') and annotations.best_guess_labels:
            for label in annotations.best_guess_labels:
                print('\nBest guess label: {}'.format(label.label))

        if hasattr(annotations, 'pages_with_matching_images') and annotations.pages_with_matching_images:
            _match = '\n{} Pages with matching images found:'.format(len(annotations.pages_with_matching_images))
            data['web_results'].append(_match)

            for page in annotations.pages_with_matching_images:
                data['web_results'].append(page.url)

                if hasattr(page, 'full_matching_images') and page.full_matching_images:
                    for image in page.full_matching_images:
                        data['web_results'].append(image.url)

                if hasattr(page, 'partial_matching_images') and page.partial_matching_images:
                    print('\t{} Partial Matches found: '.format(
                        len(page.partial_matching_images)))

                    for image in page.partial_matching_images:
                        print('\t\tImage url  : {}'.format(image.url))

        if hasattr(annotations, 'web_entities') and  annotations.web_entities:
            _web_match = '{} Web entities found: '.format(len(annotations.web_entities))
            data['web_results'].append(_web_match)

            names = []
            for entity in annotations.web_entities:
                names.append({'confidence': entity.score, 'description': entity.description})

            data['web_results'].append({'entity_names': names})

        if hasattr(annotations, 'visually_similar_images') and annotations.visually_similar_images:
            print('\n{} visually similar images found:\n'.format(
                len(annotations.visually_similar_images)))

            for image in annotations.visually_similar_images:
                print('\tImage url    : {}'.format(image.url))
        return dict(data)

    def search_faces(self, vision_image, face_cordinates):
        face_search_result = []
        for cor in face_cordinates:
            image_path = self._crop_to_hint(cor)
            _vision_image = self.create_vision_image(image_path)
            result = self.detect_web(_vision_image)
            face_search_result.append(result)
        return face_search_result

    def detect_crop_hints(self, vision_image):
        """
        :return:
        """
        crop_hints_params = vision.types.CropHintsParams(aspect_ratios=[1.77])
        image_context = vision.types.ImageContext(crop_hints_params=crop_hints_params)

        response = self.client.crop_hints(image=vision_image, image_context=image_context)
        hints = response.crop_hints_annotation.crop_hints

        # Get bounds for the first crop hint using an aspect ratio of 1.77.
        vertices = hints[0].bounding_poly.vertices
        print(vertices)
        return vertices

    def _crop_to_hint(self, vects):

        im = Image.open(self.image)
        im2 = im.crop([vects[0].x, vects[0].y,
                       vects[2].x - 1, vects[2].y - 1])
        output_image = os.path.join(local_tmp_folder,
                                    image_crops_frames,
                                    'Image.png').replace(" ", '_')

        im2.save(output_image)
        return output_image

    def run(self, **kwargs):
        # self.upload_image_to_gcs()
        analytics_data = self.annotate()
        return {'vision_analytics': analytics_data}


if __name__ == '__main__':
    # image = os.path.join(local_video_folder, 'download.jpeg')
    image = os.path.join(local_video_folder, 'modi_screenshot.png')
    ana = VisionAnalytics(image)
    ana.run()


