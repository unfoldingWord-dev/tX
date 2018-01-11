def sample_service(name=None):
    """
    This is a sample service. Give it your name
    and prepare to be greeted!

    :param name: Your name
    :type name: basestring
    :return: A greeting or an error
    """
    if name:
        return { 'hello': name}
    else:
        return {"error": "what's your name?"}