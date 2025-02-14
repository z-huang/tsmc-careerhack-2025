
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Time
from sqlalchemy.orm import relationship, Session
from database import engine, Base


class Settings(Base):
    __tablename__ = 'settings'
    setting_id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(String, nullable=False)


class Meeting(Base):
    __tablename__ = 'meetings'
    meeting_id = Column(String, primary_key=True, index=True)
    topic = Column(String, index=True)
    date = Column(Date)

    contents = relationship("MeetingContent", back_populates="meeting")


class MeetingContent(Base):
    __tablename__ = 'meeting_contents'
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(String, ForeignKey('meetings.meeting_id'))
    message = Column(String)
    time = Column(Time)

    meeting = relationship("Meeting", back_populates="contents")


if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)
    
    with Session(bind=engine) as session:
        existing_setting = session.query(Settings).filter(
            Settings.key == "language").first()
        if not existing_setting:
            language_setting = Settings(key="language", value="cmn-Hant-TW")
            session.add(language_setting)
            session.commit()
