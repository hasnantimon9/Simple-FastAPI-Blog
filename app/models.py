from sqlalchemy import Boolean, Column, Integer, String, text, ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship
from .database import Base


class Post(Base):
	__tablename__ = "Posts"

	id = Column(Integer, primary_key=True, nullable=False)
	title = Column(String, nullable=False)
	content = Column(String, nullable=False)
	published = Column(Boolean, server_default=text("true"), nullable=False)
	created_at = Column(TIMESTAMP(timezone=True), nullable=False,server_default=text('now()'))
	owner_id = Column(Integer, ForeignKey("Users.id", ondelete="CASCADE"), nullable=False)
	owner = relationship("User")
      
class User(Base):
    __tablename__ = "Users"
    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()')) 

class Votes(Base):
	__tablename__ = "Votes"
	user_id = Column(Integer, ForeignKey("Users.id", ondelete="CASCADE"), primary_key=True)
	post_id = Column(Integer, ForeignKey("Posts.id", ondelete="CASCADE"), primary_key=True)
	value = Column(Integer, nullable=False)
	