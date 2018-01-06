def sample_service(name=None):
    """
    This is the friendly service. Give it your name
    and prepare to be greeted!
    :param name:
    :return:
    """
    if name:
        return { 'hello': name}
    else:
        return {"error": "what's your name?"}