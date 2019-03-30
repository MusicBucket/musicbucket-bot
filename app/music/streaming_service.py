import abc


class StreamingServiceParser(abc.ABC):
    """
    Abstract class that defines methods for Streaming Services Parsers
    """

    @abc.abstractmethod
    def get_link_type(self, url):
        pass

    @abc.abstractmethod
    def search_link(self, query, entity_type):
        pass

    @abc.abstractmethod
    def get_link_info(self, url, link_type):
        pass

    @abc.abstractmethod
    def get_entity_id_from_url(self, url):
        pass

    @abc.abstractmethod
    def clean_url(self, url, link_type):
        pass

    @abc.abstractmethod
    def is_valid_url(self, url):
        pass
