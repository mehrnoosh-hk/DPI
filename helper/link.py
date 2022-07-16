import datetime

def create_link():
    time_stamp = datetime.datetime.utcnow().strftime('%M%S%f')
    time_stamp_hex = hex(int(time_stamp))
    return time_stamp_hex


