from generate_thumbnails import is_event_supported_image


def test_is_supported_image():
    # Given
    event = {'name': 'test.jpg', 'contentType': 'image/jpeg'}
    file_extension = 'jpg'

    # Then
    assert is_event_supported_image(event, file_extension)


def test_is_supported_image_unsupported_content_type():
    # Given
    event = {'name': 'test.txt', 'contentType': 'text'}
    file_extension = 'txt'

    # Then
    assert not is_event_supported_image(event, file_extension)


def test_is_supported_image_unsupported_extension():
    # Given
    event = {'name': 'test.no', 'contentType': 'image/no'}
    file_extension = '.no'

    # Then
    assert not is_event_supported_image(event, file_extension)
