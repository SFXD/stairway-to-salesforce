def config_environment():
    import os
    import tzdata
    
    tzdata_path = os.path.dirname(tzdata.__file__)
    os.environ["TZDIR"] = tzdata_path
    os.environ["PYTHONTZPATH"] = tzdata_path
