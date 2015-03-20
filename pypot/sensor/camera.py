import cv2
import logging

from ..robot.sensor import Sensor
from ..robot.controller import SensorsController


logger = logging.getLogger(__name__)

class Camera(Sensor):
    registers = Sensor.registers + ['camera_id', 'last_frame']

    def __init__(self, name, camera_id):
        Sensor.__init__(self, name)

        self._id = camera_id
        self._img = None
        self._fps = None
        self._resolution = None

    @property
    def camera_id(self):
        return self._id

    @property
    def last_frame(self):
        return self._img.copy() if self._img is not None else None

    @property
    def fps(self):
        return self._fps

    @property
    def resolution(self):
        return self._resolution


class CameraController(SensorsController):
    def __init__(self, name, camera_id, fps, resolution=None):
        camera = Camera(name, camera_id)

        SensorsController.__init__(self, None, [camera], sync_freq=fps)

        if resolution is not None:
            self.resolution = resolution

    # This should be done side the setup method.
    # Yet, it freezes when not runned on the main thread.
    # def setup(self):
        self.capture = cv2.VideoCapture(self.camera.camera_id)
        # This should work but it does not ...
        # self.capture.set(cv2.cv.CV_CAP_PROP_CONVERT_RGB, True)
        # self.resolution = resolution

        # just a hack to force the push of values to the Camera Sensor
        self.resolution = self.resolution
        self.fps = fps

        # try to get a first frame
        if not self.capture.isOpened():
            raise ValueError('Can not open camera device {}!'.format(camera_id))

        self.rval, frame = self.capture.read()
        if not self.rval:
            raise EnvironmentError('Can not grab an image from the camera device!')

        self._last_frame = None

    # This should be done inside the teardown method instead.
    # But unfortunately, releasing the VideoCapture freezes
    # when not done in the main thread
    # def teardown(self):
    def __del__(self):
        self.capture.release()

    def update(self):
        self.rval, img = self.capture.read()
        if self.rval:
            self.camera._img = self.post_processing(img)

    @property
    def camera(self):
        return self.sensors[0]

    def post_processing(self, img):
        """ Returns the image post processed. """
        return img

    @property
    def resolution(self):
        return [self.capture.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH),
                self.capture.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)]

    @resolution.setter
    def resolution(self, new_resolution):
        self.capture.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, new_resolution[0])
        self.capture.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, new_resolution[1])

        self.camera._resolution = new_resolution

    @property
    def fps(self):
        return self.capture.get(cv2.cv.CV_CAP_PROP_FPS)

    @fps.setter
    def fps(self, new_fps):
        ischanged = self.capture.set(cv2.cv.CV_CAP_PROP_FPS, new_fps)

        if not ischanged:
            logger.warning('Cannot set the camera fps to {}'
                           ' (current: {})!'.format(new_fps, self.fps))

        self.camera._fps = new_fps

        self.period = 1.0 / new_fps


if __name__ == '__main__':
    import cv2

    from pypot.sensor.camera import CameraController

    cc = CameraController('camera', camera_id=-1, fps=25)
    cc.start()

    while True:
        if cc.camera.last_frame is not None:
            cv2.imshow('cam', cc.camera.last_frame)
        cv2.waitKey(int(1000/25))
