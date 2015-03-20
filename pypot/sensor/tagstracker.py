from numpy import nan, nanmean
from collections import defaultdict, deque

from hampy import detect_markers

from ..robot.sensor import Sensor
from ..robot.controller import SensorsController


class TagSensor(Sensor):
    registers = Sensor.registers + ['tag_id', 'position']

    def __init__(self, name, id):
        Sensor.__init__(self, name)
        self._id = id

    @property
    def tag_id(self):
        return self._id

    @property
    def position(self):
        return self._pos


class TagsTracker(SensorsController):
    def __init__(self, camera, objects_marker, freq=25., window_length=5):
        tags = [TagSensor(obj, mid) for obj, mid in objects_marker.items()]

        SensorsController.__init__(self, None, tags, freq)

        self.camera = camera
        self.objects_marker = objects_marker

        self._pos = defaultdict(lambda: deque([], window_length))

    def update(self):
        img = self.camera.last_frame

        if img is not None:
            markers = detect_markers(img, [self.objects_marker.values()])
        else:
            markers = []

        for obj, mid in self.objects_marker.items():
            tracked_pos = [m.center for m in markers if m.id == mid]
            pos = tracked_pos[0] if tracked_pos else [nan, nan]

            self._pos[obj].append(pos)

        res = self.camera.resolution
        for tag in self.sensors:
            tag._pos = nanmean(self._pos[tag.name], axis=0) / res


if __name__ == '__main__':
    import cv2

    from numpy import isnan

    from pypot.sensor.camera import CameraController
    from pypot.sensor.tagstracker import TagsTracker

    cc = CameraController('camera', -1, 25)
    cc.start()

    tt = TagsTracker(cc.camera, {'bob': 224107608})
    tt.start()

    tag = tt.sensors[0]
    w, h = cc.camera.resolution

    while True:
        if cc.camera.last_frame is not None:
            img = cc.camera.last_frame

            if not isnan(tag.position).any():
                x, y = tag.position

                cv2.putText(img, tag.name,
                            (int(x * w), int(y * h)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)

            cv2.imshow('cam', img)

        cv2.waitKey(int(1000/25))
