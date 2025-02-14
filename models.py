
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import engine, Base


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
    time = Column(String)

    meeting = relationship("Meeting", back_populates="contents")

if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)