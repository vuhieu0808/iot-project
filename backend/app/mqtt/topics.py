"""MQTT topic string constants."""


class Topics:
    """MQTT topic paths used for communication between ESP32 hardware and Python backend."""

    # ESP32 -> Backend
    DOOR_CHECKIN_REQUEST = "gymtag/door/checkin_request"
    DOOR_CHECKOUT_REQUEST = "gymtag/door/checkout_request"
    LOCKER_REQUEST = "gymtag/locker/request"
    ENVIRONMENT_READING = "gymtag/environment/reading"
    REPS_COUNTER_REQUEST = "gymtag/repscounter/request"
    REPS_COUNTER_RESULT = "gymtag/repscounter/result"

    # Backend -> ESP32
    DOOR_CHECKIN_RESPONSE = "gymtag/door/response"
    DOOR_CHECKOUT_RESPONSE = "gymtag/door/response"
    LOCKER_RESPONSE = "gymtag/locker/response"
    ENVIRONMENT_FAN_CONTROL = "gymtag/environment/fan_control"
    REPS_COUNTER_RESPONSE = "gymtag/repscounter/response"
