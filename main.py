# FastAPI ToDo List Manager with SQLite
# This application provides a full CRUD API for managing tasks.
# It uses SQLAlchemy for ORM and Pydantic for data validation.

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi_mcp import FastApiMCP

# --- Database Configuration ---
DATABASE_URL = "sqlite:///./todos.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SQLAlchemy Model ---
class TodoModel(Base):
    __tablename__ = "todos"
    todo_id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    completed = Column(Boolean, default=False)

# Create the database tables
Base.metadata.create_all(bind=engine)

# --- Pydantic Schemas ---
class TodoBase(BaseModel):
    content: str
    completed: bool = False

class TodoCreate(TodoBase):
    pass

class TodoResponse(TodoBase):
    todo_id: int

    class Config:
        from_attributes = True

# --- Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FastAPI App ---
app = FastAPI(title="ToDo MCP API", description="A simple CRUD API for managing tasks.")

@app.get("/")
async def root():
    """Welcome route."""
    return {"message": "Welcome to the FastAPI ToDo Manager"}

@app.get("/todos", operation_id="get_all_todos", response_model=List[TodoResponse])
def get_all_todos(db: Session = Depends(get_db)):
    """Retrieve all todo items."""
    return db.query(TodoModel).all()

@app.get("/todos/{todo_id}", operation_id="getTodo", response_model=TodoResponse)
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific todo by ID."""
    todo = db.query(TodoModel).filter(TodoModel.todo_id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@app.post("/todos", response_model=TodoResponse, operation_id="createTodo", status_code=201)
def add_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    """Create a new todo item."""
    db_todo = TodoModel(**todo.model_dump())
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.put("/todos/{todo_id}", operation_id="updateTodo", response_model=TodoResponse)
def update_todo(todo_id: int, updated_todo: TodoCreate, db: Session = Depends(get_db)):
    """Update an existing todo item."""
    db_todo = db.query(TodoModel).filter(TodoModel.todo_id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    db_todo.content = updated_todo.content
    db_todo.completed = updated_todo.completed
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.delete("/todos/{todo_id}", operation_id="deleteTodo", status_code=204)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Delete a todo item."""
    db_todo = db.query(TodoModel).filter(TodoModel.todo_id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    db.delete(db_todo)
    db.commit()
    return None


#if __name__ == "__main__":
#    import uvicorn
    mcp = FastApiMCP(app, include_operations=["get_all_todos", "getTodo", "createTodo", "updateTodo", "deleteTodo"])
    mcp.mount()
#    uvicorn.run(app, host="127.0.0.1", port=8000)