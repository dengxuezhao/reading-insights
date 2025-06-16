import asyncio
from backend.app.database import get_db
from backend.app.models.reading_session import ReadingSession
from backend.app.models.book import Book
from backend.app.models.highlight import Highlight
from sqlalchemy import select, func

async def check_data():
    async for db in get_db():
        try:
            # 检查阅读会话数据
            sessions_result = await db.execute(select(func.count(ReadingSession.id)))
            sessions_count = sessions_result.scalar()
            
            # 检查书籍数据
            books_result = await db.execute(select(func.count(Book.id)))
            books_count = books_result.scalar()
            
            # 检查标注数据
            highlights_result = await db.execute(select(func.count(Highlight.id)))
            highlights_count = highlights_result.scalar()
            
            print(f'阅读会话数量: {sessions_count}')
            print(f'书籍数量: {books_count}')
            print(f'标注数量: {highlights_count}')
            
            # 检查一些样本数据
            if sessions_count > 0:
                sample_sessions = await db.execute(
                    select(ReadingSession.book_id, ReadingSession.page, ReadingSession.duration, ReadingSession.start_time)
                    .limit(5)
                )
                print('\n样本阅读会话:')
                for session in sample_sessions:
                    print(f'  书籍ID: {session.book_id}, 页码: {session.page}, 时长: {session.duration}秒, 时间: {session.start_time}')
            
            if books_count > 0:
                sample_books = await db.execute(
                    select(Book.id, Book.title, Book.author)
                    .limit(3)
                )
                print('\n样本书籍:')
                for book in sample_books:
                    print(f'  ID: {book.id}, 标题: {book.title}, 作者: {book.author}')
                    
        except Exception as e:
            print(f'检查数据时出错: {e}')
        finally:
            break

if __name__ == "__main__":
    asyncio.run(check_data()) 