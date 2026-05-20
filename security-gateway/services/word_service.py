"""
词库业务服务

负责词库的 CRUD、缓存刷新和批量导入。
"""

from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.security import WordLibrary, WordType


class WordService:
    """词库服务"""

    async def create(
        self, session: AsyncSession, word: str, word_type: str, **kwargs
    ) -> WordLibrary:
        """新增词"""
        db_word = WordLibrary(
            word=word,
            word_type=WordType(word_type),
            category=kwargs.get("category"),
            severity=kwargs.get("severity", 1),
            description=kwargs.get("description"),
            is_active=kwargs.get("is_active", True),
            scope=kwargs.get("scope", "system"),
            organization_id=kwargs.get("organization_id"),
            creator_id=kwargs.get("creator_id"),
        )
        session.add(db_word)
        await session.commit()
        await session.refresh(db_word)
        return db_word

    async def get_by_id(
        self, session: AsyncSession, word_id: int
    ) -> Optional[WordLibrary]:
        """根据 ID 获取词"""
        result = await session.execute(
            select(WordLibrary).where(WordLibrary.id == word_id)
        )
        return result.scalar_one_or_none()

    async def list_words(
        self,
        session: AsyncSession,
        word_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        scope: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[WordLibrary], int]:
        """分页查询词库"""
        query = select(WordLibrary)
        count_query = select(func.count()).select_from(WordLibrary)

        if word_type:
            query = query.where(WordLibrary.word_type == word_type)
            count_query = count_query.where(WordLibrary.word_type == word_type)
        if is_active is not None:
            query = query.where(WordLibrary.is_active == is_active)
            count_query = count_query.where(WordLibrary.is_active == is_active)
        if scope:
            query = query.where(WordLibrary.scope == scope)
            count_query = count_query.where(WordLibrary.scope == scope)

        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        query = (
            query.order_by(WordLibrary.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(query)
        words = result.scalars().all()
        return list(words), total

    async def update(
        self, session: AsyncSession, word_id: int, **kwargs
    ) -> Optional[WordLibrary]:
        """更新词"""
        db_word = await self.get_by_id(session, word_id)
        if not db_word:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(db_word, key):
                setattr(db_word, key, value)

        db_word.version += 1
        await session.commit()
        await session.refresh(db_word)
        return db_word

    async def delete(
        self, session: AsyncSession, word_id: int
    ) -> bool:
        """删除词（硬删）"""
        db_word = await self.get_by_id(session, word_id)
        if not db_word:
            return False
        await session.delete(db_word)
        await session.commit()
        return True

    async def batch_create(
        self,
        session: AsyncSession,
        words_data: List[dict],
    ) -> List[WordLibrary]:
        """批量导入词"""
        db_words = []
        for data in words_data:
            db_word = WordLibrary(
                word=data["word"],
                word_type=WordType(data["word_type"]),
                category=data.get("category"),
                severity=data.get("severity", 1),
                description=data.get("description"),
                is_active=data.get("is_active", True),
                scope=data.get("scope", "system"),
                organization_id=data.get("organization_id"),
                creator_id=data.get("creator_id"),
            )
            session.add(db_word)
            db_words.append(db_word)

        await session.commit()
        for db_word in db_words:
            await session.refresh(db_word)
        return db_words

    async def get_all_active(
        self, session: AsyncSession
    ) -> List[WordLibrary]:
        """获取所有启用的词（用于加载引擎）"""
        result = await session.execute(
            select(WordLibrary).where(WordLibrary.is_active == True)
        )
        return list(result.scalars().all())
