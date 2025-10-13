"""Image service for managing digital products."""
import os
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from database.models import Image, Purchase


class ImageService:
    """Service for image/product operations."""
    
    @staticmethod
    async def add_image(
        session: AsyncSession,
        file_id: str,
        file_path: str,
        price_sol: float,
        region_id: int,
        city_id: int,
        uploaded_by: int,
        description: Optional[str] = None,
        district_id: Optional[int] = None,
        preview_file_id: Optional[str] = None,
        category: Optional[str] = None
    ) -> Image:
        """Add new image to database."""
        # Note: file_path and uploaded_by are not in Image model
        # Image model only has: file_id, price_sol, region_id, city_id, district_id, description, preview_file_id, category
        image = Image(
            file_id=file_id,
            price_sol=price_sol,
            region_id=region_id,
            city_id=city_id,
            district_id=district_id,
            description=description,
            preview_file_id=preview_file_id,
            category=category
        )
        session.add(image)
        await session.commit()
        await session.refresh(image)
        return image
    
    @staticmethod
    async def get_available_images(
        session: AsyncSession,
        region_id: Optional[int] = None,
        city_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Image]:
        """Get available (not sold) images."""
        query = select(Image).where(Image.is_sold == False)
        
        if region_id:
            query = query.where(Image.region_id == region_id)
        
        if city_id:
            query = query.where(Image.city_id == city_id)
        
        query = query.limit(limit)
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_image_by_id(session: AsyncSession, image_id: int) -> Optional[Image]:
        """Get image by ID."""
        result = await session.execute(
            select(Image).where(Image.id == image_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def mark_as_sold(
        session: AsyncSession,
        image_id: int,
        user_id: int,
        price_paid: float
    ) -> bool:
        """Mark image as sold and create purchase record."""
        image = await ImageService.get_image_by_id(session, image_id)
        if not image or image.is_sold:
            return False
        
        # Mark as sold
        image.is_sold = True
        from datetime import datetime
        image.sold_at = datetime.utcnow()
        
        # Create purchase record
        purchase = Purchase(
            user_id=user_id,
            image_id=image_id,
            price_sol=price_paid
        )
        session.add(purchase)
        
        await session.commit()
        return True
    
    @staticmethod
    async def delete_image(session: AsyncSession, image_id: int) -> bool:
        """Delete image and its file."""
        image = await ImageService.get_image_by_id(session, image_id)
        if not image:
            return False
        
        # Delete file if exists
        if os.path.exists(image.file_path):
            try:
                os.remove(image.file_path)
            except Exception as e:
                print(f"Error deleting file: {e}")
        
        # Delete from database
        await session.delete(image)
        await session.commit()
        return True
    
    @staticmethod
    async def get_images_by_category(session: AsyncSession, category_key: str) -> List[Image]:
        """Get all images by category key."""
        stmt = select(Image).where(Image.category == category_key)
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_user_purchases(
        session: AsyncSession,
        user_id: int,
        limit: int = 50
    ) -> List[Purchase]:
        """Get user's purchase history."""
        result = await session.execute(
            select(Purchase)
            .where(Purchase.user_id == user_id)
            .order_by(Purchase.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_image_count(
        session: AsyncSession,
        region_id: Optional[int] = None,
        city_id: Optional[int] = None,
        sold: Optional[bool] = None
    ) -> int:
        """Get count of images with filters."""
        from sqlalchemy import func
        
        query = select(func.count(Image.id))
        
        conditions = []
        if region_id:
            conditions.append(Image.region_id == region_id)
        if city_id:
            conditions.append(Image.city_id == city_id)
        if sold is not None:
            conditions.append(Image.is_sold == sold)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await session.execute(query)
        return result.scalar() or 0
    
    @staticmethod
    async def get_images_by_uploader(session: AsyncSession, user_id: int, limit: int = 50):
        """Get images uploaded by specific user."""
        result = await session.execute(
            select(Image)
            .where(Image.uploaded_by == user_id)
            .order_by(Image.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_all_images(session: AsyncSession, limit: int = 50):
        """Get all images."""
        result = await session.execute(
            select(Image)
            .order_by(Image.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_statistics(session: AsyncSession) -> dict:
        """Get overall statistics."""
        from sqlalchemy import func
        
        # Total images
        total_images = await ImageService.get_image_count(session)
        
        # Sold images
        sold_images = await ImageService.get_image_count(session, sold=True)
        
        # Available images
        available_images = await ImageService.get_image_count(session, sold=False)
        
        # Total revenue
        result = await session.execute(
            select(func.sum(Purchase.price_sol))
        )
        total_revenue = result.scalar() or 0.0
        
        return {
            'total_images': total_images,
            'sold_images': sold_images,
            'available_images': available_images,
            'total_revenue': total_revenue
        }

