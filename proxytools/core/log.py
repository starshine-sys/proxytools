import logging


def getLogger(name=None, level=logging.INFO):
    name = __name__ if name is None else name
    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    # handler.setFormatter(
    #     logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # )
    # logger.addHandler(handler)

    return logger
