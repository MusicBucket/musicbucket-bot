import datetime
import logging
from collections import defaultdict
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker, scoped_session, subqueryload, joinedload, join
from sqlalchemy.sql import exists
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)

Base = declarative_base()


class DB:
    def __init__(self):
        logger.info('Setting up DB')
        self.engine = create_engine(
            'sqlite:///db.sqlite?check_same_thread=False', echo=True)
        self.sessionmaker = scoped_session(sessionmaker(bind=self.engine))
        self.__setup()

    def __setup(self):
        logger.info('Setting up models')
        Base.metadata.create_all(self.engine)

    def get_users(self):
        logger.info('Getting users')
        session = self.sessionmaker()
        return session.query(User).all()

    def get_links(self, chat_id, days=None):
        """Returns a dictionary of the users and their links for a specific chat and the given days"""
        qry = None
        session = self.sessionmaker()

        if days is not None:
            logger.info(
                'Getting links of chat: {} from the last {} days'.format(chat_id, days))
            qry = session.query(UserChatLink)\
                .filter(UserChatLink.created_at >= datetime.datetime.now() - datetime.timedelta(days=days))\
                .filter(UserChatLink.chat_id == chat_id)\
                .order_by(UserChatLink.created_at)\
                .all()
        else:
            logger.info(
                'Getting links of chat: {} from the beggining'.format(chat_id))
            qry = session.query(UserChatLink)\
                .filter(UserChatLink.chat_id == chat_id)\
                .order_by(UserChatLink.created_at)\
                .all()

        res = defaultdict(list)
        for link in qry:
            res[link.user].append(link)
        res = dict(res)
        return res

    def check_if_same_link_same_chat(self, link, chat_id, days):
        logger.info(
            'Checking if this user already saved this link in the same chat.')
        session = self.sessionmaker()
        return session.query(exists()
                             .where(UserChatLink.chat_id == chat_id)
                             .where(UserChatLink.link == link)
                             .where(UserChatLink.created_at >= datetime.datetime.now() - datetime.timedelta(days=days))
                             )\
            .scalar()

    def check_if_user_exists(self, user_id):
        logger.info('Checking if exists. User: {}'.format(user_id))
        session = self.sessionmaker()
        return session.query(exists().where(User.id == user_id)).scalar()

    def save_object(self, object):
        session = self.sessionmaker()
        session.add(object)
        session.commit()


class User(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True)
    username = Column(String)
    firstname = Column(String)
    lastname = Column(String)

    links = relationship('UserChatLink', back_populates='user',
                         cascade='all, delete, delete-orphan')

    def __str__(self):
        return 'User. id:{}, username: {}, firstname: {}'.format(self.id, self.username, self.lastname)


class UserChatLink(Base):
    __tablename__ = 'user_chat_links'

    id = Column(Integer, primary_key=True)
    link = Column(String)
    link_type = Column(Integer)
    artist_name = Column(String)
    album_name = Column(String)
    track_name = Column(String)
    genre = Column(String)
    created_at = Column(DateTime)
    chat_id = Column(String)
    chat_name = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))

    user = relationship('User', back_populates='links', lazy='joined')

    def __str__(self):
        return 'UserChatLink. user_id: {}, chat_id: {}, link: {}'.format(self.user_id, self.chat_id, self.link)
