from fastapi import APIRouter, Depends, FastAPI, HTTPException, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models, schemas
from ..database import get_db
from . import oauth2 

router = APIRouter(
    prefix="/posts",
    tags=['Posts']
)

@router.get('/', response_model=list[schemas.PostWithVote]) 
def intro(db: Session = Depends(get_db), limit: int = 10, skip: int = 0, search: str | None = None):
	query = db.query(models.Post)

	if search:
		query = query.filter(models.Post.content.contains(search))

	posts = query.limit(limit).offset(skip).all()

	results = db.query(models.Post, func.count(models.Votes.value)).outerjoin(models.Votes, models.Post.id == models.Votes.post_id).filter(models.Post.id.in_([post.id for post in posts])).group_by(models.Post.id).all()

	return [{"post": post, "vote": vote} for post, vote in results]


@router.get("/{id}", response_model=schemas.PostWithVote)
def get_post(id: int, db: Session = Depends(get_db), user = Depends(oauth2.get_current_user)):
	one_post = db.query(models.Post, func.count(models.Votes.value)).outerjoin(models.Votes, models.Post.id == models.Votes.post_id).group_by(models.Post.id).filter(models.Post.id == id).first()

	if not one_post:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

	post, vote = one_post
	return {"post": post, "vote": vote}

@router.post("/",response_model=schemas.PostResponse)
def create_posts(post: schemas.PostCreate, db: Session = Depends(get_db), user = Depends(oauth2.get_current_user)):
	new_post = models.Post(owner_id=user.id, **post.model_dump())
	db.add(new_post)
	db.commit()
	db.refresh(new_post)

	return new_post

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db), user = Depends(oauth2.get_current_user)):
	post_query = db.query(models.Post).filter(models.Post.id == id)
	post = post_query.first()
	if not post:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item with {id} doesn't exist")

	if post.owner_id != user.id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
	
	post_query.delete()
	db.commit()
	return {'message': 'post deleted'}

@router.put("/{id}")
def update_post(id: int, post_created: schemas.PostCreate, db: Session = Depends(get_db), user = Depends(oauth2.get_current_user)):
	post_query = db.query(models.Post).filter(models.Post.id == id)
	post = post_query.first()
	if post is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

	if post.owner_id != user.id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
	post_query.update(post_created.model_dump())
	db.commit()
	return post_query.first()

@router.post("/{post_id}/vote")
def vote(post_id: int, vote_data: schemas.VoteCreate, db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):

	post_query = db.query(models.Post).filter(models.Post.id == post_id)

	if not post_query.first():
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

	existing_vote_query = db.query(models.Votes).filter(models.Votes.user_id == current_user.id, models.Votes.post_id == post_id)

	if existing_vote_query.first():
		existing_vote_query.first().value = vote_data.value 

	else:

		new_vote = models.Votes(
			user_id = current_user.id,
			post_id = post_id,
			value = vote_data.value 
		)

		db.add(new_vote)

	db.commit()

	return {'message':'Successfully voted'}

@router.delete("/{post_id}/vote")
def delete_vote(post_id: int, db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):

	existing_vote_query = db.query(models.Votes).filter(models.Votes.user_id == current_user.id, models.Votes.post_id == post_id)

	if not existing_vote_query.first():
		raise HTTPException(status_code=status.HTTP_409_CONFLICT)

	db.delete(existing_vote_query.first())
	db.commit()

	return {'message': "vote successfully removed"}