import eyed3

class Mp3TagUtilities:

    @staticmethod
    def set_audio_file_tag(filename: str, **kwargs):
        audio_file = eyed3.load(filename)
        for k, v in kwargs.items():
            setattr(audio_file.tag, k, v)

        audio_file.tag.save()
